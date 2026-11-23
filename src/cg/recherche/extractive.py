"""Réponse extractive : citer exactement le segment le plus probant, ou s'abstenir (F5).

Place dans le projet : base de la question-réponse, et point de comparaison du LLM (D-016). La
réponse **est** un segment du contrat, cité mot pour mot avec sa page et ses positions ; rien n'est
reformulé. Si le meilleur segment n'est pas assez proche de la question (similarité cosinus sous un
seuil réglé hors du jeu d'évaluation), on **s'abstient**.
"""

from dataclasses import dataclass

from cg.recherche.hybride import Resultat


@dataclass(frozen=True)
class Reponse:
    """Réponse à une question, ou abstention.

    Attributes:
        abstention: Vrai si le système refuse de répondre (aucune preuve assez fiable).
        citation: Le segment cité (``None`` en cas d'abstention).
        confiance: Similarité cosinus du segment retenu avec la question.
    """

    abstention: bool
    citation: Resultat | None
    confiance: float


def repondre(resultats: list[Resultat], seuil: float) -> Reponse:
    """Cite le premier résultat de la recherche s'il est assez proche de la question.

    Args:
        resultats: Résultats de la recherche, du meilleur au moins bon.
        seuil: Similarité cosinus minimale pour répondre.

    Returns:
        La réponse (le segment cité tel quel) ou une abstention.
    """
    if not resultats or resultats[0].similarite < seuil:
        return Reponse(abstention=True, citation=None, confiance=resultats[0].similarite if resultats else 0.0)
    return Reponse(abstention=False, citation=resultats[0], confiance=resultats[0].similarite)
