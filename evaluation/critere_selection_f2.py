"""Script : appliquer le critère de sélection de F2 (D-012) sur la VALIDATION.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -u evaluation/critere_selection_f2.py

Critère (D-012) : **rappel par annotation maximal, sous contrainte d'une précision minimale par
famille** (précision par segment) ; macro-F1 affiché en complément. Pour chaque modèle et chaque
famille, le seuil est choisi **sur la validation** : le plus petit seuil (donc le plus grand
rappel) dont la précision atteint le minimum. On compare ensuite les modèles.

Le critère sert à **choisir le modèle sur la validation** ; le test n'évalue ensuite que le modèle
retenu, une seule fois (règle 2). Le test n'est pas ouvert ici.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from cg.datasets.cuad import FAMILLE_DE, FAMILLES, charger_cuad
from cg.datasets.segments import charger_segments, etiquettes
from cg.datasets.splits import lire_splits
from cg.extraction.evaluation import rappel_par_annotation
from cg.extraction.metriques import metriques_binaires, tableau_metriques
from cg.extraction.tfidf import creer_vectoriseur, entrainer_classifieur
from cg.extraction.transformer import choisir_appareil, predire_probas

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1"
CHEMIN = RACINE / "data" / "processed" / "cuad_pdf_segments_fusion0.jsonl"
SEUILS = np.unique(np.concatenate([np.round(np.arange(0.01, 0.991, 0.01), 2), [0.995, 0.999]]))
PRECISIONS_MIN = (0.40, 0.50, 0.60)
# Réglages TF-IDF retenus sur la validation (D-011, run MLflow « pdf-fusion0 ») : bigrammes, C = 10.
TFIDF = {"ngram_max": 2, "C": 10.0}


def seuil_sous_contrainte(y: np.ndarray, probas: np.ndarray, precision_min: float) -> float | None:
    """Plus petit seuil dont la précision atteint le minimum (donc rappel maximal).

    Args:
        y: Étiquettes vraies (validation).
        probas: Probabilités prédites.
        precision_min: Précision minimale exigée.

    Returns:
        Le seuil, ou ``None`` si aucun seuil n'atteint la précision demandée.
    """
    for seuil in SEUILS:
        pred = probas >= seuil
        if pred.any() and metriques_binaires(y, pred)["precision"] >= precision_min:
            return float(seuil)
    return None


def main() -> None:
    """Calcule les probabilités des modèles, applique le critère, affiche la comparaison."""
    train = charger_segments(CHEMIN, {"train"})
    val = charger_segments(CHEMIN, {"val"})
    y_val = etiquettes(val)
    probas: dict[str, np.ndarray] = {}

    vectoriseur = creer_vectoriseur(TFIDF["ngram_max"])
    X_train, X_val = vectoriseur.fit_transform(train["texte"]), vectoriseur.transform(val["texte"])
    probas["TF-IDF"] = np.column_stack([
        entrainer_classifieur(X_train, train[f].to_numpy(), TFIDF["C"]).predict_proba(X_val)[:, 1]
        for f in FAMILLES])
    appareil = choisir_appareil()
    for nom, dossier in [("Transformer poids fort", "f2-cuad-legal-bert-small"),
                         ("Transformer poids atténué", "f2-cuad-legal-bert-small-poids-racine")]:
        chemin = RACINE / "models" / dossier
        modele = AutoModelForSequenceClassification.from_pretrained(chemin).to(appareil)
        probas[nom] = predire_probas(modele, AutoTokenizer.from_pretrained(chemin), val["texte"].tolist(), appareil, 256)

    textes, annotations = charger_cuad(DOSSIER_CUAD / "CUAD_v1.json")
    jeu_de = lire_splits(RACINE / "data" / "splits" / "cuad_v1_splits.json")
    annotations_val: dict[str, list] = {}
    for a in annotations:
        if a.categorie in FAMILLE_DE and jeu_de[a.titre] == "val":
            annotations_val.setdefault(a.titre, []).append(a)

    lignes = []
    for precision_min in PRECISIONS_MIN:
        for nom, p in probas.items():
            seuils = {f: seuil_sous_contrainte(y_val[f], p[:, k], precision_min) for k, f in enumerate(FAMILLES)}
            if any(s is None for s in seuils.values()):
                lignes.append({"précision min": precision_min, "modèle": nom, "admissible": False})
                continue
            predictions = {f: p[:, k] >= seuils[f] for k, f in enumerate(FAMILLES)}
            tableau = tableau_metriques(y_val, predictions)
            rappels = rappel_par_annotation(val, predictions, 0, textes, annotations_val, DOSSIER_CUAD / "full_contract_pdf")
            lignes.append({"précision min": precision_min, "modèle": nom, "admissible": True,
                           "rappel annot. macro": round(rappels["macro"], 3),
                           **{f"R.annot {f[:5]}": round(rappels[f], 3) for f in FAMILLES},
                           "précision macro": round(float(tableau.loc["macro", "precision"]), 3),
                           "macro-F1": round(float(tableau.loc["macro", "f1"]), 3),
                           "seuils": " / ".join(f"{seuils[f]:.2f}" for f in FAMILLES)})
    pd.set_option("display.width", 250)
    print(pd.DataFrame(lignes).to_string(index=False))


if __name__ == "__main__":
    main()
