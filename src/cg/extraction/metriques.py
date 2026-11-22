"""Métriques d'évaluation de l'extraction (F2) et choix du seuil de décision.

Place dans le projet : toutes les baselines et tous les modèles de F2 sont évalués avec ces
fonctions, pour que les chiffres soient comparables.

On ne calcule **pas** l'exactitude globale : avec 97 % de segments « aucune famille », un modèle
qui ne trouve rien aurait 97 % d'exactitude. On mesure précision, rappel et F1 par famille,
puis le macro-F1 (moyenne simple des familles, pour que la plus rare compte autant).
"""

import numpy as np
import pandas as pd


def metriques_binaires(y_vrai: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Précision, rappel et F1 pour une famille (problème oui / non).

    Args:
        y_vrai: Étiquettes vraies (booléens), une par segment.
        y_pred: Prédictions (booléens), une par segment.

    Returns:
        Un dictionnaire avec ``precision``, ``rappel``, ``f1`` (0 quand non défini),
        et les effectifs ``vp`` (vrais positifs), ``fp``, ``fn``, ``support`` (positifs vrais).
    """
    y_vrai = np.asarray(y_vrai, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)
    vp = int((y_vrai & y_pred).sum())
    fp = int((~y_vrai & y_pred).sum())
    fn = int((y_vrai & ~y_pred).sum())
    precision = vp / (vp + fp) if vp + fp else 0.0
    rappel = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * precision * rappel / (precision + rappel) if precision + rappel else 0.0
    return {"precision": precision, "rappel": rappel, "f1": f1,
            "vp": vp, "fp": fp, "fn": fn, "support": vp + fn}


def tableau_metriques(y_vrai: dict[str, np.ndarray], y_pred: dict[str, np.ndarray]) -> pd.DataFrame:
    """Tableau des métriques par famille, avec une ligne finale « macro ».

    Args:
        y_vrai: ``famille -> étiquettes vraies``.
        y_pred: ``famille -> prédictions`` (mêmes familles, même ordre des segments).

    Returns:
        Un DataFrame indexé par famille ; la ligne ``macro`` contient la moyenne simple des
        précisions, rappels et F1 des familles.
    """
    lignes = {famille: metriques_binaires(y_vrai[famille], y_pred[famille]) for famille in y_vrai}
    tableau = pd.DataFrame(lignes).T
    tableau.loc["macro", ["precision", "rappel", "f1"]] = tableau[["precision", "rappel", "f1"]].mean()
    return tableau


def choisir_seuil(
    y_vrai: np.ndarray, probas: np.ndarray, seuils: np.ndarray | None = None
) -> tuple[float, float]:
    """Choisit le seuil de décision qui maximise le F1. À utiliser sur la VALIDATION seulement.

    Args:
        y_vrai: Étiquettes vraies de la validation.
        probas: Probabilités prédites pour la validation.
        seuils: Seuils candidats ; par défaut de 0,05 à 0,95 par pas de 0,05.

    Returns:
        Le couple (meilleur seuil, F1 obtenu avec ce seuil). En cas d'égalité, le plus petit seuil.
    """
    if seuils is None:
        seuils = np.round(np.arange(0.05, 0.951, 0.05), 2)
    meilleur_seuil, meilleur_f1 = float(seuils[0]), -1.0
    for seuil in seuils:
        f1 = metriques_binaires(y_vrai, probas >= seuil)["f1"]
        if f1 > meilleur_f1:
            meilleur_seuil, meilleur_f1 = float(seuil), f1
    return meilleur_seuil, meilleur_f1
