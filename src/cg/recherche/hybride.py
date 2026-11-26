"""Recherche hybride dans les segments d'un contrat : mots (texte intégral) + sens (vecteurs) (F5).

Place dans le projet : première étape de la question-réponse. On cherche **dans un seul contrat**
(celui que l'utilisateur interroge), et chaque résultat garde sa provenance (segment, page,
positions : règle 1).

- **Par les mots** : recherche en texte intégral de PostgreSQL (``tsv``, racinisation anglaise),
  classement ``ts_rank_cd`` ; la question est transformée en « l'un de ces mots » (OU), pour ne pas
  exiger que tous les mots d'une longue question soient présents.
- **Par le sens** : distance cosinus entre le vecteur de la question et ceux des segments (pgvector).
- **Fusion RRF** (*Reciprocal Rank Fusion*) : score = somme de 1 / (60 + rang) dans chaque classement.
- **Variante BM25** (D-024, **acceptée** : recherche par défaut) : modes ``"bm25"`` et ``"hybride_bm25"``,
  où le classement par les mots est un vrai BM25 (``cg.recherche.bm25``) au lieu de ``ts_rank_cd``.
  Les modes ``"mots"`` et ``"hybride"`` (texte intégral PostgreSQL) restent pour les ablations.
"""

from dataclasses import dataclass

import numpy as np
import psycopg

from cg.recherche.bm25 import par_bm25
from cg.recherche.embeddings import Encodeur, vers_pgvector

K_RRF: int = 60
RECHERCHE_PAR_DEFAUT: str = "hybride_bm25"  # D-024


@dataclass
class Resultat:
    """Un segment trouvé, avec sa provenance et ses scores.

    Attributes:
        segment_id: Identifiant du segment dans la base.
        page: Numéro de page.
        debut: Position de début dans le texte complet du contrat.
        fin: Position de fin.
        texte: Texte du segment.
        rang_mots: Rang dans la recherche par mots (``None`` si absent).
        rang_sens: Rang dans la recherche par sens (``None`` si absent).
        similarite: Similarité cosinus avec la question (entre -1 et 1).
        score_rrf: Score de la fusion.
    """

    segment_id: int
    page: int
    debut: int
    fin: int
    texte: str
    rang_mots: int | None = None
    rang_sens: int | None = None
    similarite: float = 0.0
    score_rrf: float = 0.0


def par_mots(connexion: psycopg.Connection, contrat_id: int, question: str, k: int) -> list[tuple[int, float]]:
    """Segments du contrat classés par la recherche en texte intégral.

    Args:
        connexion: Connexion à la base.
        contrat_id: Contrat interrogé.
        question: Question en langage naturel.
        k: Nombre de résultats.

    Returns:
        Les couples (segment_id, score), du meilleur au moins bon.
    """
    with connexion.cursor() as curseur:
        curseur.execute(
            """WITH q AS (SELECT NULLIF(replace(plainto_tsquery('english', %s)::text, '&', '|'), '')::tsquery AS requete)
               SELECT s.id, ts_rank_cd(s.tsv, q.requete) AS score
               FROM segments s, q
               WHERE s.contrat_id = %s AND q.requete IS NOT NULL AND s.tsv @@ q.requete
               ORDER BY score DESC, s.id LIMIT %s""",
            (question, contrat_id, k))
        return [(int(i), float(s)) for i, s in curseur.fetchall()]


def par_sens(connexion: psycopg.Connection, contrat_id: int, vecteur: str, k: int) -> list[tuple[int, float]]:
    """Segments du contrat classés par similarité cosinus avec la question.

    Args:
        connexion: Connexion à la base.
        contrat_id: Contrat interrogé.
        vecteur: Vecteur de la question au format pgvector.
        k: Nombre de résultats.

    Returns:
        Les couples (segment_id, similarité cosinus), du plus proche au moins proche.
    """
    with connexion.cursor() as curseur:
        curseur.execute(
            """SELECT id, 1 - (embedding <=> %s::vector) AS similarite
               FROM segments WHERE contrat_id = %s AND embedding IS NOT NULL
               ORDER BY embedding <=> %s::vector, id LIMIT %s""",
            (vecteur, contrat_id, vecteur, k))
        return [(int(i), float(s)) for i, s in curseur.fetchall()]


def rechercher(
    connexion: psycopg.Connection, encodeur: Encodeur, contrat_id: int, question: str,
    k: int = 10, mode: str = RECHERCHE_PAR_DEFAUT, vecteur_requete: np.ndarray | None = None,
) -> list[Resultat]:
    """Recherche dans un contrat : ``"mots"``, ``"sens"``, ``"hybride"`` (fusion RRF), ``"bm25"`` ou ``"hybride_bm25"``.

    Args:
        connexion: Connexion à la base.
        encodeur: Encodeur d'embeddings.
        contrat_id: Contrat interrogé.
        question: Question en langage naturel.
        k: Nombre de résultats renvoyés.
        mode: Méthode de recherche.
        vecteur_requete: Vecteur déjà calculé de la question (évite de le recalculer).

    Returns:
        Les résultats, du meilleur au moins bon, avec provenance et similarité cosinus.
    """
    vecteur = vers_pgvector(vecteur_requete if vecteur_requete is not None else encodeur.encoder_requete(question))
    profondeur = max(50, k)  # on fusionne sur des listes plus longues que k
    if mode not in ("mots", "sens", "hybride", "bm25", "hybride_bm25"):
        raise ValueError(f"mode de recherche inconnu : {mode}")
    if mode in ("mots", "hybride"):
        mots = par_mots(connexion, contrat_id, question, profondeur)
    elif mode in ("bm25", "hybride_bm25"):
        mots = par_bm25(connexion, contrat_id, question, profondeur)
    else:
        mots = []
    sens = par_sens(connexion, contrat_id, vecteur, profondeur) if mode in ("sens", "hybride", "hybride_bm25") else []
    scores: dict[int, float] = {}
    rangs_mots = {sid: r for r, (sid, _) in enumerate(mots, start=1)}
    rangs_sens = {sid: r for r, (sid, _) in enumerate(sens, start=1)}
    for rangs in (rangs_mots, rangs_sens):
        for sid, r in rangs.items():
            scores[sid] = scores.get(sid, 0.0) + 1.0 / (K_RRF + r)
    meilleurs = sorted(scores, key=lambda sid: (-scores[sid], sid))[:k]
    if not meilleurs:
        return []
    with connexion.cursor() as curseur:
        curseur.execute(
            """SELECT id, page, debut, fin, texte, 1 - (embedding <=> %s::vector)
               FROM segments WHERE id = ANY(%s)""", (vecteur, meilleurs))
        lignes = {int(r[0]): r for r in curseur.fetchall()}
    return [Resultat(segment_id=sid, page=lignes[sid][1], debut=lignes[sid][2], fin=lignes[sid][3],
                     texte=lignes[sid][4], rang_mots=rangs_mots.get(sid), rang_sens=rangs_sens.get(sid),
                     similarite=float(lignes[sid][5] or 0.0), score_rrf=scores[sid]) for sid in meilleurs]
