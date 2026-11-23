"""Script : critère de D-012 appliqué « à la lettre » sur la VALIDATION, famille par famille.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -u evaluation/critere_selection_f2_equitable.py

Pour chaque modèle (TF-IDF, Transformer à poids atténué) et chaque famille : parmi **tous** les
seuils de la grille dont la précision par segment est ≥ 0,50, on retient celui qui **maximise le
rappel par annotation**, puis on compare les rappels obtenus. Test non ouvert.

Pour aller vite, on calcule une seule fois, pour chaque annotation de la validation (alignée selon
D-007), la liste des segments qu'elle étiquette (même règle de chevauchement que partout) ; une
annotation est « trouvée » si l'un de ces segments est prédit positif dans sa famille.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from cg.datasets.cuad import FAMILLE_DE, FAMILLES, SEUIL_CHEVAUCHEMENT, charger_cuad, chevauchement
from cg.datasets.segments import charger_segments, etiquettes
from cg.datasets.splits import lire_splits
from cg.extraction.metriques import metriques_binaires
from cg.extraction.tfidf import creer_vectoriseur, entrainer_classifieur
from cg.extraction.transformer import choisir_appareil, predire_probas
from cg.ingestion.alignement import aligner, normaliser
from cg.ingestion.pdf import extraire_pdf, trouver_pdf

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1"
CHEMIN = RACINE / "data" / "processed" / "cuad_pdf_segments_fusion0.jsonl"
SEUILS = np.unique(np.concatenate([np.round(np.arange(0.01, 0.991, 0.01), 2), [0.995, 0.999]]))
PRECISION_MIN = 0.50


def segments_par_annotation(val: pd.DataFrame) -> dict[str, list[list[int]]]:
    """Pour chaque famille, la liste (une entrée par annotation alignée) des indices de segments étiquetés.

    Args:
        val: Segments PDF de validation (index 0..n-1).

    Returns:
        ``famille -> [[indices des segments de l'annotation 1], …]``.
    """
    textes, annotations = charger_cuad(DOSSIER_CUAD / "CUAD_v1.json")
    jeu_de = lire_splits(RACINE / "data" / "splits" / "cuad_v1_splits.json")
    par_titre = {t: g for t, g in val.groupby("titre")}
    resultat: dict[str, list[list[int]]] = {f: [] for f in FAMILLES}
    for titre, segs in par_titre.items():
        document = extraire_pdf(trouver_pdf(DOSSIER_CUAD / "full_contract_pdf", titre), titre, mode="blocs")
        cible = normaliser(document.texte, "etendue")
        contexte = textes[titre]
        for a in annotations:
            if a.titre != titre or a.categorie not in FAMILLE_DE or jeu_de[titre] != "val":
                continue
            position = aligner(contexte[a.debut:a.fin], cible, "etendue", a.debut / len(contexte))
            if position is None:
                continue  # D-007 : exclue
            d, f = position
            seuil = min(SEUIL_CHEVAUCHEMENT, f - d)
            indices = [int(i) for i, sd, sf in zip(segs.index, segs["debut"], segs["fin"])
                       if chevauchement(sd, sf, d, f) >= seuil]
            resultat[FAMILLE_DE[a.categorie]].append(indices)
    return resultat


def main() -> None:
    """Probabilités des deux modèles, puis recherche exhaustive du seuil, famille par famille."""
    train = charger_segments(CHEMIN, {"train"})
    val = charger_segments(CHEMIN, {"val"})
    y_val = etiquettes(val)
    vectoriseur = creer_vectoriseur(2)  # réglages TF-IDF retenus sur la validation (D-011) : bigrammes, C = 10
    X_train, X_val = vectoriseur.fit_transform(train["texte"]), vectoriseur.transform(val["texte"])
    probas = {"TF-IDF": np.column_stack([
        entrainer_classifieur(X_train, train[f].to_numpy(), 10.0).predict_proba(X_val)[:, 1] for f in FAMILLES])}
    chemin = RACINE / "models" / "f2-cuad-legal-bert-small-poids-racine"
    appareil = choisir_appareil()
    modele = AutoModelForSequenceClassification.from_pretrained(chemin).to(appareil)
    probas["Transformer (poids atténué)"] = predire_probas(
        modele, AutoTokenizer.from_pretrained(chemin), val["texte"].tolist(), appareil, 256)

    annotations = segments_par_annotation(val)
    lignes = []
    for k, famille in enumerate(FAMILLES):
        for nom, p in probas.items():
            meilleur = None
            for seuil in SEUILS:
                pred = p[:, k] >= seuil
                m = metriques_binaires(y_val[famille], pred)
                if not pred.any() or m["precision"] < PRECISION_MIN:
                    continue
                rappel_annot = float(np.mean([pred[idx].any() if idx else False for idx in annotations[famille]]))
                if meilleur is None or rappel_annot > meilleur["rappel par annotation"]:
                    meilleur = {"famille": famille, "modèle": nom, "seuil": float(seuil),
                                "rappel par annotation": rappel_annot, "précision": m["precision"],
                                "rappel (segments)": m["rappel"], "F1 (segments)": m["f1"],
                                "annotations": len(annotations[famille])}
            lignes.append(meilleur or {"famille": famille, "modèle": nom, "seuil": None})
    tableau = pd.DataFrame(lignes)
    pd.set_option("display.width", 220)
    print(tableau.round(3).to_string(index=False))
    print("\nMoyenne (macro) du rappel par annotation :")
    print(tableau.groupby("modèle")["rappel par annotation"].mean().round(3).to_string())


if __name__ == "__main__":
    main()
