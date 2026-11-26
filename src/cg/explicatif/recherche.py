"""Recherche dans le corpus documentaire explicatif : BM25 + embeddings, fusion RRF (F5, D-023, D-024).

Place dans le projet : pendant de ``cg.recherche.hybride`` pour le corpus explicatif. La recherche porte
sur **tout** le corpus explicatif (et jamais sur les contrats : index séparé). Chaque résultat garde sa
provenance (source, page ou section, positions) et l'**attribution** à afficher (D-023).
"""

from dataclasses import dataclass

import numpy as np
import psycopg

from cg.recherche.bm25 import index_explicatif, mots_question
from cg.recherche.embeddings import Encodeur, vers_pgvector
from cg.recherche.hybride import K_RRF


@dataclass
class ResultatExplicatif:
    """Un passage explicatif trouvé, avec sa provenance et son attribution.

    Attributes:
        segment_id: Identifiant dans ``segments_explicatifs``.
        source: Titre de la source.
        url: Page de la source.
        licence: Licence de la source.
        attribution: Texte d'attribution à afficher.
        date_version: Date de la version indexée.
        page: Page (PDF) ou ``None``.
        section: Section, ou ``None``.
        debut: Position de début dans le texte de la source.
        fin: Position de fin.
        texte: Texte du passage.
        similarite: Similarité cosinus avec la question.
        score_rrf: Score de la fusion.
    """

    segment_id: int
    source: str
    url: str
    licence: str
    attribution: str
    date_version: str | None
    page: int | None
    section: str | None
    debut: int
    fin: int
    texte: str
    similarite: float = 0.0
    score_rrf: float = 0.0


def rechercher_explicatif(connexion: psycopg.Connection, encodeur: Encodeur, question: str, k: int = 3,
                          vecteur_requete: np.ndarray | None = None) -> list[ResultatExplicatif]:
    """Passages explicatifs les plus proches de la question (BM25 + embeddings, fusion RRF).

    Args:
        connexion: Connexion à la base.
        encodeur: Encodeur d'embeddings.
        question: Question en langage naturel.
        k: Nombre de passages renvoyés.
        vecteur_requete: Vecteur déjà calculé de la question.

    Returns:
        Les passages, du meilleur au moins bon (liste vide si le corpus n'est pas indexé).
    """
    vecteur = vers_pgvector(vecteur_requete if vecteur_requete is not None else encodeur.encoder_requete(question))
    profondeur = max(50, k)
    mots = index_explicatif(connexion).classer(mots_question(connexion, question), profondeur)
    with connexion.cursor() as c:
        c.execute("""SELECT id FROM segments_explicatifs WHERE embedding IS NOT NULL
                     ORDER BY embedding <=> %s::vector, id LIMIT %s""", (vecteur, profondeur))
        sens = [int(i) for (i,) in c.fetchall()]
    scores: dict[int, float] = {}
    for classement in ([sid for sid, _ in mots], sens):
        for rang, sid in enumerate(classement, start=1):
            scores[sid] = scores.get(sid, 0.0) + 1.0 / (K_RRF + rang)
    meilleurs = sorted(scores, key=lambda sid: (-scores[sid], sid))[:k]
    if not meilleurs:
        return []
    with connexion.cursor() as c:
        c.execute("""SELECT s.id, src.titre, src.url, src.licence, src.attribution, src.date_version, s.page,
                            s.section, s.debut, s.fin, s.texte, 1 - (s.embedding <=> %s::vector)
                     FROM segments_explicatifs s JOIN sources_explicatives src ON src.id = s.source_id
                     WHERE s.id = ANY(%s)""", (vecteur, meilleurs))
        lignes = {int(r[0]): r for r in c.fetchall()}
    return [ResultatExplicatif(*lignes[sid][:11], similarite=float(lignes[sid][11] or 0.0), score_rrf=scores[sid])
            for sid in meilleurs]
