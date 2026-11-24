"""Logique de l'application (F6) : importer un contrat, extraire les clauses, répondre, alerter.

Place dans le projet : l'API (``app.py``) n'est qu'une façade HTTP ; tout le travail est ici, et
réutilise les modules de F1 à F5. Les modèles lourds sont chargés à la première utilisation.
Chaque sortie référence ses segments avec page et positions (règle 1).
"""

import itertools
import tempfile
from dataclasses import asdict
from functools import cached_property
from pathlib import Path

import numpy as np
import psycopg
import pymupdf

from cg import config
from cg.comparison.alertes import decider_alerte
from cg.extraction.pipeline import ExtracteurClauses
from cg.ingestion.pdf import extraire_pdf, segmenter_pdf
from cg.recherche.embeddings import Encodeur, vers_pgvector
from cg.recherche.extractive import repondre
from cg.recherche.graphe import construire_graphe
from cg.recherche.hybride import rechercher
from cg.recherche.llm import discuter
from cg.stockage.depot import compter_segments_non_tracables, enregistrer_document

AVERTISSEMENT = ("ContractGuardian est une aide à la lecture : il ne donne pas d'avis juridique. "
                 "Vérifiez toujours le passage cité dans le contrat.")
SEUIL_EXTRACTIF = 0.71               # D-017 (réglé sur le train, critère équilibré)
SEUILS_NLI = (0.85, 0.95)            # D-014 (document, évidence), réglés sur le dev de ContractNLI
PAIRES_FAMILLES = [("durée", "résiliation"), ("responsabilité", "responsabilité"),
                   ("résiliation", "résiliation"), ("durée", "durée")]
MAX_PAIRES_ALERTES = 30


def titre_libre(connexion: psycopg.Connection, titre: str) -> str:
    """Titre unique dans la base : ajoute « (import 2) », « (import 3) »… si le titre existe déjà.

    Args:
        connexion: Connexion à la base.
        titre: Titre souhaité (nom du fichier sans extension).

    Returns:
        Un titre qui n'existe pas encore (la table ``contrats`` impose des titres uniques).
    """
    candidat, n = titre, 1
    with connexion.cursor() as c:
        while True:
            c.execute("SELECT 1 FROM contrats WHERE titre = %s", (candidat,))
            if c.fetchone() is None:
                return candidat
            n += 1
            candidat = f"{titre} (import {n})"


class Services:
    """Opérations de l'application sur la base, avec chargement paresseux des modèles."""

    @cached_property
    def extracteur(self) -> ExtracteurClauses:
        return ExtracteurClauses()

    @cached_property
    def encodeur(self) -> Encodeur:
        return Encodeur()

    @cached_property
    def nli(self):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        from cg.extraction.transformer import choisir_appareil
        chemin = config.RACINE / "models" / "f4-nli-legal-bert-small"
        appareil = choisir_appareil()
        return (AutoTokenizer.from_pretrained(chemin),
                AutoModelForSequenceClassification.from_pretrained(chemin).to(appareil), appareil)

    # --- Contrats -----------------------------------------------------------------------------------
    def lister_contrats(self, connexion: psycopg.Connection) -> list[dict]:
        """Contrats importés par l'utilisateur (les contrats CUAD de la base sont exclus)."""
        with connexion.cursor() as c:
            c.execute("""SELECT id, titre, nb_pages, importe_le FROM contrats
                         WHERE source = 'import' AND mode_extraction NOT LIKE 'test%%' ORDER BY id DESC""")
            return [{"id": i, "titre": t, "nb_pages": n, "importe_le": d.isoformat()} for i, t, n, d in c.fetchall()]

    def importer_pdf(self, connexion: psycopg.Connection, contenu: bytes, nom_fichier: str) -> dict:
        """Extrait, segmente, enregistre, indexe et étiquette un PDF importé.

        Args:
            connexion: Connexion à la base.
            contenu: Octets du fichier PDF.
            nom_fichier: Nom d'origine du fichier.

        Returns:
            Un résumé : identifiant, pages, pages sans texte, segments, clauses détectées, traçabilité.
        """
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / nom_fichier
            chemin.write_bytes(contenu)
            titre = titre_libre(connexion, Path(nom_fichier).stem)
            document = extraire_pdf(chemin, titre, mode="blocs")
            segments = segmenter_pdf(document)
            contrat_id = enregistrer_document(connexion, document, segments, "import",
                                              f"pymupdf-{pymupdf.VersionBind}/blocs", chemin)
        pages_vides = [p.numero for p in document.pages if not document.texte[p.debut:p.fin].strip()]
        with connexion.cursor() as c:
            c.execute("SELECT id, texte FROM segments WHERE contrat_id = %s ORDER BY debut", (contrat_id,))
            lignes = c.fetchall()
        textes = [t for _, t in lignes]
        vecteurs = self.encodeur.encoder(textes)
        detections = self.extracteur.detecter(textes)
        with connexion.transaction(), connexion.cursor() as c:
            c.executemany("UPDATE segments SET embedding = %s::vector WHERE id = %s",
                          [(vers_pgvector(v), i) for (i, _), v in zip(lignes, vecteurs)])
            c.executemany("""INSERT INTO resultats (segment_id, tache, etiquette, score, modele)
                             VALUES (%s, 'extraction', %s, %s, %s)""",
                          [(lignes[d.indice][0], d.famille, d.score, d.modele) for d in detections])
        return {"id": contrat_id, "titre": titre, "nb_pages": len(document.pages), "pages_sans_texte": pages_vides,
                "segments": len(segments), "clauses_detectees": len(detections),
                "segments_non_tracables": compter_segments_non_tracables(connexion, contrat_id)}

    def contrat(self, connexion: psycopg.Connection, contrat_id: int) -> dict | None:
        """Informations d'un contrat, ou ``None`` s'il n'existe pas."""
        with connexion.cursor() as c:
            c.execute("SELECT id, titre, nb_pages, importe_le FROM contrats WHERE id = %s", (contrat_id,))
            ligne = c.fetchone()
        return None if ligne is None else {"id": ligne[0], "titre": ligne[1], "nb_pages": ligne[2],
                                           "importe_le": ligne[3].isoformat()}

    # --- F2 : clauses -------------------------------------------------------------------------------
    def clauses(self, connexion: psycopg.Connection, contrat_id: int) -> list[dict]:
        """Clauses détectées, avec la citation exacte du segment et sa provenance."""
        with connexion.cursor() as c:
            c.execute("""SELECT r.etiquette, r.score, r.modele, s.id, s.page, s.debut, s.fin, s.texte
                         FROM resultats r JOIN segments s ON s.id = r.segment_id
                         WHERE s.contrat_id = %s AND r.tache = 'extraction'
                         ORDER BY r.etiquette, s.debut""", (contrat_id,))
            return [{"famille": f, "score": round(sc, 3), "modele": m, "segment_id": sid, "page": p,
                     "debut": d, "fin": fi, "citation": t} for f, sc, m, sid, p, d, fi, t in c.fetchall()]

    # --- F5 : questions -----------------------------------------------------------------------------
    def repondre(self, connexion: psycopg.Connection, contrat_id: int, question: str, mode: str) -> dict:
        """Réponse avec citations vérifiées (``rag``) ou segment cité (``extractif``), ou abstention."""
        if mode == "extractif":
            rep = repondre(rechercher(connexion, self.encodeur, contrat_id, question, 10), SEUIL_EXTRACTIF)
            if rep.abstention:
                return {"abstention": True, "raison": "aucun passage assez proche de la question", "citations": []}
            r = rep.citation
            return {"abstention": False, "reponse": None, "citations": [
                {"segment_id": r.segment_id, "page": r.page, "debut": r.debut, "fin": r.fin, "extrait": r.texte}]}
        graphe = construire_graphe(lambda q: rechercher(connexion, self.encodeur, contrat_id, q, 5), discuter)
        resultat = graphe.invoke({"question": question})["resultat"]
        return {"abstention": resultat.abstention, "raison": resultat.raison, "reponse": resultat.reponse or None,
                "citations": [asdict(c) for c in resultat.citations], "modele": config.LLM_MODELE}

    # --- F3 : alertes (expérimental) ----------------------------------------------------------------
    def alertes(self, connexion: psycopg.Connection, contrat_id: int) -> list[dict]:
        """Points à vérifier entre clauses détectées (règle v1, D-018) : fonctionnalité expérimentale."""
        from cg.nli.modele import probas_paires
        from cg.nli.paires import INDICE, Paire
        clauses = self.clauses(connexion, contrat_id)
        paires = []
        for fa, fb in PAIRES_FAMILLES:
            for a, b in itertools.product([c for c in clauses if c["famille"] == fa], [c for c in clauses if c["famille"] == fb]):
                if a["segment_id"] < b["segment_id"] or (fa != fb and a["segment_id"] != b["segment_id"]):
                    paires.append((a, b))
        paires = paires[:MAX_PAIRES_ALERTES]
        if not paires:
            return []
        tokeniseur, modele, appareil = self.nli
        jeux = [Paire("", "f3", 0, a["citation"], b["citation"], 0) for a, b in paires] + \
               [Paire("", "f3", 0, b["citation"], a["citation"], 0) for a, b in paires]
        p = probas_paires(modele, tokeniseur, jeux, appareil, 256)[:, INDICE["Contradiction"]]
        sortie = []
        for k, (a, b) in enumerate(paires):
            d = decider_alerte(a["citation"], b["citation"], float(max(p[k], p[len(paires) + k])))
            if d.alerte:
                sortie.append({"raisons": list(d.raisons), "p_contradiction": round(d.p_contradiction, 3),
                               "clause_a": {k2: a[k2] for k2 in ("famille", "page", "debut", "fin", "citation")},
                               "clause_b": {k2: b[k2] for k2 in ("famille", "page", "debut", "fin", "citation")}})
        return sortie

    # --- F4 : NLI -----------------------------------------------------------------------------------
    def nli_hypothese(self, connexion: psycopg.Connection, contrat_id: int, hypothese: str) -> dict:
        """Implication / contradiction / non mentionné, avec les segments d'évidence (D-014)."""
        from cg.nli.modele import decider, probas_paires
        from cg.nli.paires import Paire
        with connexion.cursor() as c:
            c.execute("SELECT id, page, debut, fin, texte FROM segments WHERE contrat_id = %s ORDER BY debut", (contrat_id,))
            segments = c.fetchall()
        tokeniseur, modele, appareil = self.nli
        probas = probas_paires(modele, tokeniseur, [Paire("", "h", i, hypothese, s[4], 0) for i, s in enumerate(segments)],
                               appareil, 128)
        d = decider(probas, *SEUILS_NLI)
        return {"etiquette": d.etiquette, "score": round(d.score, 3), "evidences": [
            {"segment_id": segments[i][0], "page": segments[i][1], "debut": segments[i][2], "fin": segments[i][3],
             "citation": segments[i][4]} for i in d.evidences]}
