"""Indexation du corpus explicatif dans PostgreSQL : sources, segments et vecteurs (F5, D-023).

Place dans le projet : troisième étape du corpus explicatif. Remplit les tables
``sources_explicatives`` et ``segments_explicatifs`` (``db/init/003_explicatif.sql``), **séparées** des
tables des contrats. Relancer le script remplace proprement une source déjà indexée.

Lancement (base démarrée, sources téléchargées par ``cg.explicatif.collecte``) :

    PYTHONPATH=src .venv/bin/python -m cg.explicatif.indexer
"""

import json
from pathlib import Path

import psycopg

from cg.explicatif.collecte import DOSSIER
from cg.explicatif.sources import SOURCES, Source
from cg.explicatif.texte import lire_source, segmenter_source
from cg.recherche.embeddings import Encodeur, vers_pgvector
from cg.stockage.connexion import connecter


def indexer_source(connexion: psycopg.Connection, encodeur: Encodeur, source: Source, manifeste: dict,
                   dossier: Path = DOSSIER) -> int:
    """Indexe une source (texte, segments, vecteurs), en remplaçant sa version précédente.

    Args:
        connexion: Connexion à la base.
        encodeur: Encodeur d'embeddings (le même que pour les contrats, D-015).
        source: La source à indexer.
        manifeste: Entrée du manifeste de collecte pour cette source (version, empreinte, date).
        dossier: Dossier des fichiers téléchargés.

    Returns:
        Le nombre de segments indexés.
    """
    document = lire_source(source, dossier)
    segments = segmenter_source(document)
    vecteurs = encodeur.encoder([s.texte for s in segments])
    # Une transaction : la source est remplacée en entier, ou pas du tout (connexion en autocommit).
    with connexion.transaction(), connexion.cursor() as c:
        c.execute("DELETE FROM sources_explicatives WHERE cle = %s", (source.cle,))
        c.execute(
            """INSERT INTO sources_explicatives (cle, titre, url, url_version, editeur, licence, attribution,
                                                 date_version, consulte_le, sha256, texte_complet)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (source.cle, source.titre, source.url, manifeste.get("url_version"), source.editeur, source.licence,
             source.attribution, manifeste.get("date_version"), manifeste["consulte_le"], manifeste["sha256"],
             document.texte))
        source_id = c.fetchone()[0]
        c.executemany(
            """INSERT INTO segments_explicatifs (source_id, debut, fin, texte, page, section, embedding)
               VALUES (%s, %s, %s, %s, %s, %s, %s::vector)""",
            [(source_id, s.debut, s.fin, s.texte, s.page, s.section, vers_pgvector(v))
             for s, v in zip(segments, vecteurs)])
    return len(segments)


def main() -> None:
    """Indexe toutes les sources du manifeste."""
    manifeste = json.loads((DOSSIER / "manifeste.json").read_text(encoding="utf-8"))
    encodeur = Encodeur()
    with connecter() as connexion:
        for source in SOURCES:
            n = indexer_source(connexion, encodeur, source, manifeste[source.cle])
            print(f"{source.cle:28} {n:>5} segments", flush=True)


if __name__ == "__main__":
    main()
