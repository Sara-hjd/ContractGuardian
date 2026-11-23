"""Script : évaluer la baseline par mots-clés de la confidentialité sur le dev de ContractNLI.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python training/baseline_confidentialite.py

La liste de mots-clés (``cg.extraction.mots_cles_confidentialite``) a été figée et commitée avant
toute évaluation (commit e44cdf8). Rien n'est réglé ici : on mesure seulement.

Trois façons de définir les négatifs (décision D-009), sur le **dev** de ContractNLI et la
**validation** de CUAD (les jeux de test restent fermés) :
- A : NDA seulement (positifs = segments avec une évidence ; négatifs = autres segments des NDA) ;
- B : positifs des NDA + négatifs = segments PDF de validation CUAD ;
- C : tous les segments des NDA + segments PDF de validation CUAD.
Un run MLflow par option (expérience ``F2-confidentialite``).
"""

from pathlib import Path

import mlflow
import numpy as np

from cg.datasets.contractnli import annotations_confidentialite, charger_contractnli
from cg.datasets.cuad import categories_par_segment
from cg.datasets.segments import charger_segments
from cg.extraction.metriques import metriques_binaires
from cg.extraction.mots_cles_confidentialite import MOTS_CLES_CONFIDENTIALITE, predire_confidentialite
from cg.ingestion.segmentation import segmenter

RACINE = Path(__file__).resolve().parents[1]
CHEMIN_ZIP = RACINE / "data" / "raw" / "contractnli" / "contract-nli.zip"
CHEMIN_CUAD_PDF = RACINE / "data" / "processed" / "cuad_pdf_segments_fusion0.jsonl"
URI_MLFLOW = f"sqlite:///{RACINE / 'mlflow.db'}"


def main() -> None:
    """Calcule précision, rappel et F1 pour les options A, B et C ; les journalise dans MLflow."""
    documents, _ = charger_contractnli(CHEMIN_ZIP, "dev")
    textes: list[str] = []
    etiquettes: list[bool] = []
    for d in documents:
        segments = segmenter(d.titre, d.texte, coupe_aux_lignes=True)
        textes += [s.texte for s in segments]
        etiquettes += [bool(c) for c in categories_par_segment(segments, annotations_confidentialite(d))]
    y = np.array(etiquettes)
    p_nda = predire_confidentialite(textes)
    cuad = charger_segments(CHEMIN_CUAD_PDF, {"val"})
    p_cuad = predire_confidentialite(cuad["texte"].tolist())
    zeros = np.zeros(len(p_cuad), dtype=bool)

    options = {
        "A-nda-seulement": (y, p_nda),
        "B-positifs-nda-negatifs-cuad": (np.concatenate([y[y], zeros]), np.concatenate([p_nda[y], p_cuad])),
        "C-nda-et-cuad": (np.concatenate([y, zeros]), np.concatenate([p_nda, p_cuad])),
    }
    mlflow.set_tracking_uri(URI_MLFLOW)
    mlflow.set_experiment("F2-confidentialite")
    for nom, (y_vrai, y_pred) in options.items():
        m = metriques_binaires(y_vrai, y_pred)
        with mlflow.start_run(run_name=f"mots-cles-{nom}"):
            mlflow.log_params({"modele": "mots-cles", "liste_figee": "e44cdf8",
                               "nb_motifs": len(MOTS_CLES_CONFIDENTIALITE), "option_negatifs": nom,
                               "segmentation": "v1-coupe-aux-lignes", "evaluation": "dev ContractNLI + val CUAD"})
            mlflow.log_metrics({"precision": m["precision"], "rappel": m["rappel"], "f1": m["f1"],
                                "segments": len(y_vrai), "part_positifs": float(y_vrai.mean())})
        print(f"{nom:30s} n={len(y_vrai):6d} positifs={y_vrai.mean():5.1%} "
              f"P={m['precision']:.3f} R={m['rappel']:.3f} F1={m['f1']:.3f}")
    print(f"\nSegments NDA sans évidence contenant un mot-clé : {p_nda[~y].mean():.1%}")
    print(f"Segments PDF val CUAD contenant un mot-clé : {p_cuad.mean():.1%} "
          f"({cuad.loc[p_cuad, 'titre'].nunique()} contrats sur {cuad['titre'].nunique()})")


if __name__ == "__main__":
    main()
