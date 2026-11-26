"""Vérification NLI d'une réponse du RAG : le passage cité doit « impliquer » la réponse (F5, D-022).

Place dans le projet : second contrôle de l'étape « vérifier » du graphe RAG (``cg.recherche.graphe``),
après la vérification mot pour mot des citations. Il réutilise le modèle NLI de F4 (D-014) : une
réponse n'est gardée que si **au moins un** passage cité l'implique (probabilité « Entailment »
≥ 0,85, seuil réglé sur 200 questions du **train** avec le critère A de D-025 ; 0,5 avant) ; sinon,
abstention.
"""

from collections.abc import Callable

SEUIL_NLI_RAG: float = 0.85  # D-025 : critère A sur 200 questions de réglage du train (0,5 avant) ; jamais le test
LONGUEUR_MAX: int = 256  # même longueur que pour F4


def creer_verificateur(tokeniseur, modele, appareil) -> Callable[[str, list[str]], bool]:
    """Construit la fonction de vérification à passer au graphe RAG.

    Args:
        tokeniseur: Tokeniseur du modèle NLI de F4.
        modele: Modèle NLI de F4 (déjà sur ``appareil``).
        appareil: Appareil de calcul (``"mps"``, ``"cuda"`` ou ``"cpu"``).

    Returns:
        Une fonction ``(reponse, passages) -> bool`` : vrai si au moins un passage implique la réponse.
    """
    from cg.nli.modele import probas_paires
    from cg.nli.paires import INDICE, Paire

    def impliquee(reponse: str, passages: list[str]) -> bool:
        if not reponse.strip() or not passages:
            return False  # une réponse vide ne peut pas être vérifiée : prudence
        paires = [Paire("", "f5", 0, reponse, texte, 0) for texte in passages]
        probas = probas_paires(modele, tokeniseur, paires, appareil, LONGUEUR_MAX)[:, INDICE["Entailment"]]
        return bool((probas >= SEUIL_NLI_RAG).any())

    return impliquee
