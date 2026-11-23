"""Mesures d'évaluation qui ne dépendent pas de la segmentation (F2).

Place dans le projet : le **rappel par annotation** compare équitablement des modèles évalués sur
des segmentations différentes (texte CUAD, PDF par blocs, fusion…) : une clause annotée de la
validation est-elle détectée dans au moins un segment, dans la bonne famille ?
"""

from pathlib import Path

import numpy as np
import pandas as pd

from cg.datasets.cuad import FAMILLE_DE, FAMILLES, SEUIL_CHEVAUCHEMENT, chevauchement
from cg.ingestion.alignement import aligner, normaliser
from cg.ingestion.pdf import extraire_pdf, segmenter_pdf, trouver_pdf
from cg.ingestion.segmentation import fusionner_fragments


def rappel_par_annotation(
    val: pd.DataFrame, predictions: dict[str, np.ndarray], seuil_fusion: int,
    textes: dict[str, str], annotations_val: dict[str, list], dossier_pdf: Path,
) -> dict[str, float]:
    """Part des annotations de la validation dont au moins un segment est détecté (bonne famille).

    Args:
        val: Segments PDF de validation, dans l'ordre des prédictions.
        predictions: Prédictions par famille, alignées sur ``val``.
        seuil_fusion: Seuil de fusion utilisé pour produire ``val`` (pour refaire les mêmes segments).
        textes: Textes CUAD (pour lire les passages annotés).
        annotations_val: Annotations de nos catégories, par contrat de validation.
        dossier_pdf: Dossier ``full_contract_pdf/`` de CUAD.

    Returns:
        Le rappel par annotation pour chaque famille et ``"macro"`` (moyenne des familles).
    """
    detecte: dict[tuple[str, int, int], dict[str, bool]] = {
        (t, d, f): {fam: bool(predictions[fam][i]) for fam in FAMILLES}
        for i, (t, d, f) in enumerate(zip(val["titre"], val["debut"], val["fin"]))
    }
    trouvees = {f: 0 for f in FAMILLES}
    totales = {f: 0 for f in FAMILLES}
    for titre, annotations in annotations_val.items():
        document = extraire_pdf(trouver_pdf(dossier_pdf, titre), titre, mode="blocs")
        segments = fusionner_fragments(document.texte, segmenter_pdf(document), seuil_fusion)
        cible = normaliser(document.texte, "etendue")
        contexte = textes[titre]
        for a in annotations:
            position = aligner(contexte[a.debut:a.fin], cible, "etendue", a.debut / len(contexte))
            if position is None:
                continue  # D-007 : exclue
            famille = FAMILLE_DE[a.categorie]
            totales[famille] += 1
            debut, fin = position
            seuil = min(SEUIL_CHEVAUCHEMENT, fin - debut)
            if any(chevauchement(s.debut, s.fin, debut, fin) >= seuil
                   and detecte[(titre, s.debut, s.fin)][famille] for s in segments):
                trouvees[famille] += 1
    rappels = {f: trouvees[f] / totales[f] for f in FAMILLES}
    rappels["macro"] = float(np.mean(list(rappels.values())))
    return rappels
