"""Script : réévaluer les Transformers de F2 avec une grille de seuils élargie (validation).

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -u evaluation/reevaluer_seuils_transformer.py

Pourquoi : au premier entraînement (journal K5), tous les seuils choisis valaient 0,95, le
**maximum** de la grille ; le vrai meilleur seuil pouvait donc être plus haut (le poids des
positifs, ≈ négatifs / positifs, pousse les probabilités vers 1). On recharge les modèles
sauvegardés (pas de réentraînement) et on choisit le seuil sur une grille élargie, **sur la
validation** (le dev pour la confidentialité). Les tests restent fermés.
"""

from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from cg.datasets.cuad import FAMILLE_DE, FAMILLES, charger_cuad
from cg.datasets.segments import charger_segments
from cg.datasets.splits import lire_splits
from cg.extraction.evaluation import rappel_par_annotation
from cg.extraction.metriques import choisir_seuil, tableau_metriques
from cg.extraction.transformer import choisir_appareil, predire_probas

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1"
SEUILS = np.unique(np.concatenate([np.round(np.arange(0.05, 0.951, 0.05), 2),
                                   [0.96, 0.97, 0.98, 0.99, 0.995, 0.999]]))
SLUG = {"durée": "duree", "résiliation": "resiliation", "responsabilité": "responsabilite",
        "confidentialité": "confidentialite"}


def main() -> None:
    """Recharge chaque modèle, prédit la validation, choisit les seuils sur la grille élargie."""
    appareil = choisir_appareil()
    cuad_val = charger_segments(RACINE / "data" / "processed" / "cuad_pdf_segments_fusion0.jsonl", {"val"})
    nli = pd.read_json(RACINE / "data" / "processed" / "contractnli_segments.jsonl", lines=True)
    nli_dev = nli[nli["jeu"] == "dev"].reset_index(drop=True)
    nli_dev["confidentialité"] = nli_dev["confidentialite"].astype(bool)
    taches = {"confidentialite": (nli_dev, ["confidentialité"]), "cuad": (cuad_val, list(FAMILLES))}

    mlflow.set_tracking_uri(f"sqlite:///{RACINE / 'mlflow.db'}")
    mlflow.set_experiment("F2-transformer")
    for tache, (val, familles) in taches.items():
        dossier = RACINE / "models" / f"f2-{tache}-legal-bert-small"
        tokeniseur = AutoTokenizer.from_pretrained(dossier)
        modele = AutoModelForSequenceClassification.from_pretrained(dossier).to(appareil)
        probas = predire_probas(modele, tokeniseur, val["texte"].tolist(), appareil, 256)
        seuils = {f: choisir_seuil(val[f].to_numpy(), probas[:, k], SEUILS)[0] for k, f in enumerate(familles)}
        predictions = {f: probas[:, k] >= seuils[f] for k, f in enumerate(familles)}
        tableau = tableau_metriques({f: val[f].to_numpy() for f in familles}, predictions)
        print(f"\n=== {tache} (grille de seuils élargie) ; seuils : {seuils}")
        print(tableau[["precision", "rappel", "f1", "vp", "fp", "fn", "support"]].astype(float).round(3))
        rappels: dict[str, float] = {}
        if tache == "cuad":
            textes, annotations = charger_cuad(DOSSIER_CUAD / "CUAD_v1.json")
            jeu_de = lire_splits(RACINE / "data" / "splits" / "cuad_v1_splits.json")
            annotations_val: dict[str, list] = {}
            for a in annotations:
                if a.categorie in FAMILLE_DE and jeu_de[a.titre] == "val":
                    annotations_val.setdefault(a.titre, []).append(a)
            rappels = rappel_par_annotation(val, predictions, 0, textes, annotations_val,
                                            DOSSIER_CUAD / "full_contract_pdf")
            print("Rappel par annotation :", {k: round(v, 3) for k, v in rappels.items()})
        with mlflow.start_run(run_name=f"{tache}-legal-bert-small-seuils-elargis"):
            mlflow.log_params({"tache": tache, "modele_relu": str(dossier.relative_to(RACINE)),
                               "grille_seuils": "0,05..0,95 + 0,96..0,999",
                               **{f"{SLUG[f]}_seuil": s for f, s in seuils.items()}})
            for f in familles:
                mlflow.log_metric(f"val_{SLUG[f]}_f1", float(tableau.loc[f, "f1"]))
            mlflow.log_metric("val_macro_f1", float(tableau.loc["macro", "f1"]))
            for k, v in rappels.items():
                mlflow.log_metric(f"val_{SLUG.get(k, k)}_rappel_annotation", v)


if __name__ == "__main__":
    main()
