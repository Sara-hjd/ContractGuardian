"""Chargement des segments étiquetés (``data/processed/cuad_segments_v1.jsonl``).

Place dans le projet : point d'entrée unique des données d'entraînement de F2. Il protège la
règle absolue 2 : le jeu de test n'est jamais chargé par accident.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from cg.datasets.cuad import FAMILLES


def charger_segments(chemin: Path, jeux: set[str], ouvrir_test: bool = False) -> pd.DataFrame:
    """Lit les segments des jeux demandés, avec une colonne booléenne par famille.

    Args:
        chemin: Fichier JSONL produit par ``cg.datasets.preparer_segments``.
        jeux: Jeux à charger, parmi ``"train"``, ``"val"``, ``"test"``.
        ouvrir_test: Doit valoir ``True`` pour charger le test. Réservé à l'évaluation finale,
            une seule fois (règle 2) ; aucun réglage ne doit suivre.

    Returns:
        Un DataFrame : titre, jeu, debut, fin, texte, categories, familles, et une colonne par
        famille (``True`` si le segment en relève).

    Raises:
        PermissionError: Si ``"test"`` est demandé sans ``ouvrir_test=True``.
    """
    if "test" in jeux and not ouvrir_test:
        raise PermissionError("Le jeu de test est fermé (règle 2) : ouvrir_test=True requis.")

    lignes = []
    with open(chemin, encoding="utf-8") as fichier:
        for ligne in fichier:
            segment = json.loads(ligne)
            if segment["jeu"] in jeux:  # les autres lignes ne sont même pas gardées en mémoire
                lignes.append(segment)
    df = pd.DataFrame(lignes)
    for famille in FAMILLES:
        df[famille] = df["familles"].map(lambda fams, f=famille: f in fams).astype(bool)
    return df


def etiquettes(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Extrait les étiquettes de chaque famille sous forme de tableaux booléens.

    Args:
        df: Segments chargés par ``charger_segments``.

    Returns:
        ``famille -> tableau de booléens``, dans l'ordre des lignes de ``df``.
    """
    return {famille: df[famille].to_numpy(dtype=bool) for famille in FAMILLES}
