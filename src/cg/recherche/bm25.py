"""Recherche par les mots avec un vrai BM25 (Okapi), dans les segments d'un contrat (F5, D-024).

Place dans le projet : le cahier des charges demande une recherche « BM25 + embeddings ». Jusqu'ici,
la recherche par les mots utilisait le classement ``ts_rank_cd`` de PostgreSQL, qui **n'est pas**
BM25 (il ne pondère pas les mots rares et ne normalise pas par la longueur du segment de la même
façon). Ce module calcule un vrai BM25, pour le comparer (``evaluation/evaluer_recherche_bm25.py``).

Pour que la comparaison ne mesure **que** la formule de classement, les mots sont ceux de PostgreSQL :
les **lexèmes** de ``to_tsvector('english', …)`` (minuscules, racinisation anglaise, mots vides retirés),
déjà stockés dans la colonne ``tsv`` de chaque segment.

Formule (pour une question q et un segment s, sur les N segments du contrat) :

    BM25(q, s) = somme sur les mots t de q de  idf(t) * tf(t, s) * (k1 + 1) / (tf(t, s) + k1 * (1 - b + b * |s| / moy))
    idf(t)     = ln(1 + (N - n(t) + 0,5) / (n(t) + 0,5))

où tf(t, s) = nombre d'occurrences de t dans s, n(t) = nombre de segments contenant t, |s| = nombre de
mots du segment, moy = longueur moyenne. k1 = 1,2 et b = 0,75 : valeurs usuelles, **fixées d'avance**
(non réglées).
"""

import math
from collections import Counter
from dataclasses import dataclass

import psycopg

K1: float = 1.2
B: float = 0.75


@dataclass
class IndexBM25:
    """Index BM25 des segments d'un contrat.

    Attributes:
        frequences: Pour chaque segment, le nombre d'occurrences de chaque mot (lexème).
        longueurs: Nombre de mots de chaque segment.
        nb_segments_avec: Pour chaque mot, nombre de segments qui le contiennent.
        longueur_moyenne: Longueur moyenne des segments.
    """

    frequences: dict[int, Counter]
    longueurs: dict[int, int]
    nb_segments_avec: Counter
    longueur_moyenne: float

    @classmethod
    def construire(cls, frequences: dict[int, Counter]) -> "IndexBM25":
        """Construit l'index à partir des fréquences de mots de chaque segment.

        Args:
            frequences: Segment -> compteur des mots du segment.

        Returns:
            L'index prêt à classer des questions.
        """
        longueurs = {sid: sum(c.values()) for sid, c in frequences.items()}
        nb_avec: Counter = Counter()
        for c in frequences.values():
            nb_avec.update(c.keys())
        moyenne = (sum(longueurs.values()) / len(longueurs)) if longueurs else 0.0
        return cls(frequences, longueurs, nb_avec, moyenne)

    def idf(self, mot: str) -> float:
        """Poids d'un mot : élevé s'il est rare dans le contrat, proche de 0 s'il est partout."""
        n, total = self.nb_segments_avec.get(mot, 0), len(self.frequences)
        return math.log(1.0 + (total - n + 0.5) / (n + 0.5))

    def score(self, mots: list[str], segment_id: int) -> float:
        """Score BM25 d'un segment pour les mots (distincts) d'une question."""
        freq, longueur = self.frequences[segment_id], self.longueurs[segment_id]
        norme = K1 * (1.0 - B + B * longueur / self.longueur_moyenne) if self.longueur_moyenne else K1
        return sum(self.idf(t) * freq[t] * (K1 + 1.0) / (freq[t] + norme) for t in mots if freq.get(t))

    def classer(self, mots: list[str], k: int) -> list[tuple[int, float]]:
        """Les k segments au meilleur score (score > 0 seulement), départagés par identifiant.

        Args:
            mots: Mots de la question (lexèmes).
            k: Nombre de résultats.

        Returns:
            Les couples (segment_id, score), du meilleur au moins bon.
        """
        distincts = sorted(set(mots))
        scores = [(sid, self.score(distincts, sid)) for sid in self.frequences]
        scores = [(sid, s) for sid, s in scores if s > 0]
        return sorted(scores, key=lambda x: (-x[1], x[0]))[:k]


_CACHE: dict[int, IndexBM25] = {}


def index_contrat(connexion: psycopg.Connection, contrat_id: int) -> IndexBM25:
    """Index BM25 d'un contrat, construit une fois puis gardé en mémoire.

    Args:
        connexion: Connexion à la base.
        contrat_id: Contrat à indexer.

    Returns:
        L'index des segments du contrat (lexèmes de la colonne ``tsv``).
    """
    if contrat_id not in _CACHE:
        frequences: dict[int, Counter] = {}
        with connexion.cursor() as curseur:
            curseur.execute("SELECT id FROM segments WHERE contrat_id = %s", (contrat_id,))
            for (sid,) in curseur.fetchall():
                frequences[int(sid)] = Counter()  # un segment sans mot reste dans N
            curseur.execute(
                """SELECT s.id, u.lexeme, cardinality(u.positions)
                   FROM segments s, unnest(s.tsv) u WHERE s.contrat_id = %s""", (contrat_id,))
            for sid, mot, n in curseur.fetchall():
                frequences[int(sid)][mot] = max(int(n or 0), 1)
        _CACHE[contrat_id] = IndexBM25.construire(frequences)
    return _CACHE[contrat_id]


def mots_question(connexion: psycopg.Connection, question: str) -> list[str]:
    """Mots (lexèmes) d'une question, avec le même traitement que les segments."""
    with connexion.cursor() as curseur:
        curseur.execute("SELECT lexeme FROM unnest(to_tsvector('english', %s))", (question,))
        return [m for (m,) in curseur.fetchall()]


def par_bm25(connexion: psycopg.Connection, contrat_id: int, question: str, k: int) -> list[tuple[int, float]]:
    """Segments du contrat classés par BM25.

    Args:
        connexion: Connexion à la base.
        contrat_id: Contrat interrogé.
        question: Question en langage naturel.
        k: Nombre de résultats.

    Returns:
        Les couples (segment_id, score BM25), du meilleur au moins bon.
    """
    return index_contrat(connexion, contrat_id).classer(mots_question(connexion, question), k)
