"""Téléchargement des sources du corpus explicatif, avec leur provenance (F5, D-023).

Place dans le projet : première étape du corpus explicatif. Chaque source de ``cg.explicatif.sources``
est téléchargée **telle quelle** dans ``data/raw/explicatif/`` (jamais commité), et un manifeste
``manifeste.json`` note pour chacune : la date de consultation, l'empreinte SHA-256 du fichier, et,
pour Wikipédia, l'identifiant et la date de la **révision** téléchargée (pour pouvoir la retrouver).

Lancement (depuis la racine du projet) :

    PYTHONPATH=src .venv/bin/python -m cg.explicatif.collecte
"""

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from cg.explicatif.sources import SOURCES, Source

RACINE = Path(__file__).resolve().parents[3]
DOSSIER = RACINE / "data" / "raw" / "explicatif"
PAUSE_S: float = 3.0  # secondes entre deux téléchargements
# Identification polie auprès des serveurs (sans donnée personnelle).
ENTETES = {"User-Agent": "ContractGuardian/0.1 (projet academique ; corpus explicatif)"}


def telecharger(url: str) -> bytes:
    """Télécharge une adresse et renvoie son contenu brut.

    Args:
        url: Adresse HTTPS.

    Returns:
        Les octets reçus.
    """
    for essai in range(5):
        time.sleep(PAUSE_S)  # ne pas surcharger les serveurs (Wikipédia répond 429 sinon)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=ENTETES), timeout=120) as reponse:
                return reponse.read()
        except urllib.error.HTTPError as erreur:
            if erreur.code != 429 or essai == 4:
                raise
            attente = int(erreur.headers.get("Retry-After", "30") or 30)
            print(f"  trop de requêtes (429) : nouvelle tentative dans {attente} s", flush=True)
            time.sleep(attente)
    raise RuntimeError("inaccessible : " + url)


def _wikipedia(source: Source) -> tuple[bytes, dict]:
    """Texte brut d'un article (API de Wikipédia), avec l'identifiant de révision."""
    parametres = {"action": "query", "format": "json", "formatversion": "2", "redirects": "1",
                  "prop": "extracts|revisions", "explaintext": "1", "exsectionformat": "wiki",
                  "rvprop": "ids|timestamp", "titles": source.adresse}
    contenu = telecharger("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(parametres))
    page = json.loads(contenu)["query"]["pages"][0]
    revision = page["revisions"][0]
    return contenu, {"revision": revision["revid"], "date_version": revision["timestamp"][:10],
                     "url_version": f"https://en.wikipedia.org/w/index.php?oldid={revision['revid']}"}


def _govuk(source: Source) -> tuple[bytes, dict]:
    """Page GOV.UK au format JSON (API de contenu de GOV.UK), avec sa date de mise à jour."""
    contenu = telecharger("https://www.gov.uk/api/content/" + source.adresse)
    donnees = json.loads(contenu)
    return contenu, {"date_version": (donnees.get("public_updated_at") or "")[:10]}


def collecter() -> dict[str, dict]:
    """Télécharge toutes les sources et écrit le manifeste.

    Returns:
        Le manifeste : clé de la source -> fichier, empreinte, date de consultation, version.
    """
    DOSSIER.mkdir(parents=True, exist_ok=True)
    manifeste: dict[str, dict] = {}
    for source in SOURCES:
        if source.type == "wikipedia":
            contenu, version, extension = *_wikipedia(source), "json"
        elif source.type == "govuk":
            contenu, version, extension = *_govuk(source), "json"
        elif source.type == "far":
            contenu, version, extension = telecharger(source.adresse), {"date_version": source.date_publication}, "html"
        else:
            contenu, version, extension = telecharger(source.adresse), {"date_version": source.date_publication}, "pdf"
        fichier = DOSSIER / f"{source.cle}.{extension}"
        fichier.write_bytes(contenu)
        manifeste[source.cle] = {"fichier": fichier.name, "octets": len(contenu),
                                 "sha256": hashlib.sha256(contenu).hexdigest(),
                                 "consulte_le": date.today().isoformat(), **version}
        print(f"{source.cle:28} {len(contenu):>9} octets  version {version.get('date_version', '')}", flush=True)
    (DOSSIER / "manifeste.json").write_text(json.dumps(manifeste, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifeste


if __name__ == "__main__":
    collecter()
