"""Script : réentraîner la baseline TF-IDF sur les segments PDF et comparer sur la validation.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python training/baselines_extraction_pdf.py

Prérequis : ``cg.datasets.preparer_segments_pdf`` lancé avec ``--seuil-fusion`` 0, 20, 40 et 80,
et ``cg.datasets.preparer_segments`` (segments CUAD).

Configurations comparées (toutes réglées sur la VALIDATION, test fermé) :
- ``cuad->pdf`` : modèle entraîné sur les segments du texte CUAD, appliqué aux segments PDF
  « blocs » de la validation (ce que ferait l'application sans réentraînement) ;
- ``pdf-fusion{N}`` : modèle entraîné et évalué sur les segments PDF « blocs », avec fusion des
  fragments de moins de N caractères (option 3 de D-008 ; N = 0 : pas de fusion).

Même protocole que D-006 : TF-IDF + régression logistique pondérée, grille n-grammes {1, 2} ×
C {0,1 ; 1 ; 10}, seuil par famille, tout choisi par F1 sur la validation.

Deux mesures :
- F1 **par segment** : dépend de la segmentation, donc comparable seulement à segmentation égale ;
- **rappel par annotation** : part des clauses annotées de la validation (nos 9 catégories,
  alignées selon D-007) dont au moins un segment est détecté dans la bonne famille ; ne dépend
  pas de la segmentation.
"""

from pathlib import Path

import mlflow
import numpy as np
import pandas as pd

from cg.datasets.cuad import FAMILLE_DE, FAMILLES, charger_cuad
from cg.datasets.segments import charger_segments, etiquettes
from cg.datasets.splits import lire_splits
from cg.extraction.evaluation import rappel_par_annotation
from cg.extraction.metriques import choisir_seuil, tableau_metriques
from cg.extraction.tfidf import creer_vectoriseur, entrainer_classifieur

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1"
CHEMIN_SPLITS = RACINE / "data" / "splits" / "cuad_v1_splits.json"
CHEMIN_SEGMENTS_CUAD = RACINE / "data" / "processed" / "cuad_segments_v1.jsonl"
URI_MLFLOW = f"sqlite:///{RACINE / 'mlflow.db'}"
EXPERIENCE = "F2-extraction-segments-pdf"

SEUILS_FUSION: list[int] = [0, 20, 40, 80]  # fixés avant tout entraînement
GRILLE_NGRAM: list[int] = [1, 2]
GRILLE_C: list[float] = [0.1, 1.0, 10.0]
GRAINE = 0
SLUG: dict[str, str] = {"durée": "duree", "résiliation": "resiliation", "responsabilité": "responsabilite"}


def chemin_pdf(seuil: int) -> Path:
    """Fichier des segments PDF pour un seuil de fusion.

    Args:
        seuil: Seuil de fusion (0 = aucune fusion).

    Returns:
        Le chemin du JSONL produit par ``cg.datasets.preparer_segments_pdf``.
    """
    return RACINE / "data" / "processed" / f"cuad_pdf_segments_fusion{seuil}.jsonl"


def regler(train: pd.DataFrame, val: pd.DataFrame) -> tuple[dict[str, np.ndarray], dict[str, dict]]:
    """Entraîne sur ``train`` et choisit n-grammes, C et seuil par famille sur ``val``.

    Args:
        train: Segments d'entraînement (colonnes ``texte`` et une par famille).
        val: Segments de validation.

    Returns:
        Les prédictions retenues sur ``val`` (par famille) et les réglages retenus.
    """
    y_train, y_val = etiquettes(train), etiquettes(val)
    meilleurs: dict[str, dict] = {}
    for ngram in GRILLE_NGRAM:
        vectoriseur = creer_vectoriseur(ngram)
        X_train = vectoriseur.fit_transform(train["texte"])
        X_val = vectoriseur.transform(val["texte"])
        for famille in FAMILLES:
            for C in GRILLE_C:
                probas = entrainer_classifieur(X_train, y_train[famille], C, GRAINE).predict_proba(X_val)[:, 1]
                seuil, f1 = choisir_seuil(y_val[famille], probas)
                if f1 > meilleurs.get(famille, {}).get("f1", -1.0):
                    meilleurs[famille] = {"ngram_max": ngram, "C": C, "seuil": seuil, "f1": f1, "probas": probas}
    predictions = {f: meilleurs[f]["probas"] >= meilleurs[f]["seuil"] for f in FAMILLES}
    return predictions, meilleurs


def main() -> None:
    """Règle, évalue et journalise chaque configuration ; affiche la comparaison."""
    textes, annotations = charger_cuad(DOSSIER_CUAD / "CUAD_v1.json")
    jeu_de = lire_splits(CHEMIN_SPLITS)
    annotations_val: dict[str, list] = {}
    for a in annotations:
        if a.categorie in FAMILLE_DE and jeu_de[a.titre] == "val":
            annotations_val.setdefault(a.titre, []).append(a)

    mlflow.set_tracking_uri(URI_MLFLOW)
    mlflow.set_experiment(EXPERIENCE)

    configurations = [("cuad->pdf", 0)] + [(f"pdf-fusion{s}", s) for s in SEUILS_FUSION]
    lignes = []
    for nom, seuil_fusion in configurations:
        val = charger_segments(chemin_pdf(seuil_fusion), {"val"})
        source_train = CHEMIN_SEGMENTS_CUAD if nom == "cuad->pdf" else chemin_pdf(seuil_fusion)
        train = charger_segments(source_train, {"train"})
        predictions, reglages = regler(train, val)
        tableau = tableau_metriques(etiquettes(val), predictions)
        rappels = rappel_par_annotation(val, predictions, seuil_fusion, textes, annotations_val,
                                        DOSSIER_CUAD / "full_contract_pdf")

        with mlflow.start_run(run_name=nom):
            mlflow.log_params({"configuration": nom, "seuil_fusion": seuil_fusion,
                               "segments_train": source_train.name, "evaluation": "val",
                               "segments_val": len(val), "segments_train_n": len(train)})
            for f in FAMILLES:
                mlflow.log_params({f"{SLUG[f]}_ngram_max": reglages[f]["ngram_max"],
                                   f"{SLUG[f]}_C": reglages[f]["C"], f"{SLUG[f]}_seuil": reglages[f]["seuil"]})
                mlflow.log_metric(f"val_{SLUG[f]}_f1", float(tableau.loc[f, "f1"]))
                mlflow.log_metric(f"val_{SLUG[f]}_rappel_annotation", rappels[f])
            mlflow.log_metric("val_macro_f1", float(tableau.loc["macro", "f1"]))
            mlflow.log_metric("val_macro_rappel_annotation", rappels["macro"])

        lignes.append({"configuration": nom, "segments val": len(val),
                       **{f"F1 {f}": tableau.loc[f, "f1"] for f in FAMILLES},
                       "macro-F1 (segments)": tableau.loc["macro", "f1"],
                       **{f"R. annot. {f}": rappels[f] for f in FAMILLES},
                       "macro rappel annot.": rappels["macro"]})
        print(f"  {nom} terminé ; réglages : "
              + "  ".join(f"{f} n{reglages[f]['ngram_max']}/C{reglages[f]['C']}/s{reglages[f]['seuil']}"
                          for f in FAMILLES))

    comparaison = pd.DataFrame(lignes).set_index("configuration")
    pd.set_option("display.width", 200)
    print("\n=== Validation (test fermé) ===")
    print(comparaison.astype(float).round(3))


if __name__ == "__main__":
    main()
