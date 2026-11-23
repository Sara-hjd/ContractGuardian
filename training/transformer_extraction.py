"""Script : entraîner le Transformer d'extraction (F2) et le comparer aux baselines, sur la validation.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python training/transformer_extraction.py [--tache cuad|confidentialite|les-deux]

Deux modèles (proposition D-013) :
- ``cuad`` : 3 familles (durée, résiliation, responsabilité), segments PDF par blocs sans fusion
  (D-011) ; entraînement sur train, réglages sur val ;
- ``confidentialite`` : 1 famille, segments ContractNLI coupés aux lignes (D-009) ; entraînement sur
  train, réglages sur dev.

Réglages fixés AVANT l'entraînement (D-012) : modèle ``nlpaueb/legal-bert-small-uncased``,
taux d'apprentissage 5e-5, 3 époques, lots de 32, 256 tokens maximum, graine 0, poids des positifs
= négatifs / positifs. Sur la validation, on choisit seulement la meilleure époque (par macro-F1)
et le seuil de chaque famille. Les jeux de test restent fermés.

Sorties : un run MLflow par tâche (expérience ``F2-transformer``) ; le meilleur modèle dans
``models/`` (jamais commité).
"""

import argparse
import copy
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd

from cg.datasets.cuad import FAMILLE_DE, FAMILLES, charger_cuad
from cg.datasets.segments import charger_segments
from cg.datasets.splits import lire_splits
from cg.extraction.evaluation import rappel_par_annotation
from cg.extraction.metriques import choisir_seuil, tableau_metriques
from cg.extraction.tfidf import creer_vectoriseur, entrainer_classifieur
from cg.extraction.transformer import charger_modele, choisir_appareil, entrainer, fixer_graines, predire_probas

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1"
CHEMIN_CUAD_PDF = RACINE / "data" / "processed" / "cuad_pdf_segments_fusion0.jsonl"
CHEMIN_CONTRACTNLI = RACINE / "data" / "processed" / "contractnli_segments.jsonl"
DOSSIER_MODELES = RACINE / "models"
URI_MLFLOW = f"sqlite:///{RACINE / 'mlflow.db'}"

MODELE = "nlpaueb/legal-bert-small-uncased"
REGLAGES = {"taux_apprentissage": 5e-5, "epoques": 3, "taille_lot": 32, "longueur_max": 256, "graine": 0}
SLUG = {"durée": "duree", "résiliation": "resiliation", "responsabilité": "responsabilite",
        "confidentialité": "confidentialite"}


def donnees(tache: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Segments d'entraînement et de validation d'une tâche, avec une colonne booléenne par famille.

    Args:
        tache: ``"cuad"`` ou ``"confidentialite"``.

    Returns:
        (train, validation, liste des familles).
    """
    if tache == "cuad":
        return (charger_segments(CHEMIN_CUAD_PDF, {"train"}), charger_segments(CHEMIN_CUAD_PDF, {"val"}),
                list(FAMILLES))
    df = pd.read_json(CHEMIN_CONTRACTNLI, lines=True)
    assert set(df["jeu"]) <= {"train", "dev"}, "le test de ContractNLI ne doit pas être préparé"
    df["confidentialité"] = df["confidentialite"].astype(bool)
    return (df[df["jeu"] == "train"].reset_index(drop=True), df[df["jeu"] == "dev"].reset_index(drop=True),
            ["confidentialité"])


def evaluer(y_val: np.ndarray, probas: np.ndarray, familles: list[str]) -> tuple[pd.DataFrame, dict[str, float]]:
    """Choisit un seuil par famille sur la validation et calcule les métriques.

    Args:
        y_val: Étiquettes de validation ``(segments, familles)``.
        probas: Probabilités prédites, même forme.
        familles: Noms des familles, dans l'ordre des colonnes.

    Returns:
        Le tableau des métriques (avec la ligne ``macro``) et les seuils retenus.
    """
    seuils = {f: choisir_seuil(y_val[:, k], probas[:, k])[0] for k, f in enumerate(familles)}
    vrai = {f: y_val[:, k] for k, f in enumerate(familles)}
    pred = {f: probas[:, k] >= seuils[f] for k, f in enumerate(familles)}
    return tableau_metriques(vrai, pred), seuils


def tfidf_reference(train: pd.DataFrame, val: pd.DataFrame, familles: list[str]) -> pd.DataFrame:
    """Baseline TF-IDF (même protocole que D-006) sur les mêmes données, pour comparaison.

    Args:
        train: Segments d'entraînement.
        val: Segments de validation.
        familles: Familles à prédire.

    Returns:
        Le tableau des métriques sur la validation.
    """
    meilleures: dict[str, tuple[float, np.ndarray]] = {}
    for ngram in (1, 2):
        vectoriseur = creer_vectoriseur(ngram)
        X_train, X_val = vectoriseur.fit_transform(train["texte"]), vectoriseur.transform(val["texte"])
        for f in familles:
            for C in (0.1, 1.0, 10.0):
                probas = entrainer_classifieur(X_train, train[f].to_numpy(), C).predict_proba(X_val)[:, 1]
                seuil, f1 = choisir_seuil(val[f].to_numpy(), probas)
                if f1 > meilleures.get(f, (-1.0, None))[0]:
                    meilleures[f] = (f1, probas >= seuil)
    return tableau_metriques({f: val[f].to_numpy() for f in familles}, {f: meilleures[f][1] for f in familles})


def lancer(tache: str, poids_racine: bool = False) -> None:
    """Entraîne, choisit la meilleure époque sur la validation, compare, journalise et sauvegarde.

    Args:
        tache: ``"cuad"`` ou ``"confidentialite"``.
        poids_racine: Poids des positifs atténué (racine carrée du rapport négatifs / positifs).
    """
    fixer_graines(REGLAGES["graine"])
    train, val, familles = donnees(tache)
    y_train = train[familles].to_numpy(dtype=np.float32)
    y_val = val[familles].to_numpy(dtype=bool)
    appareil = choisir_appareil()
    print(f"\n=== {tache} : train {len(train)}, validation {len(val)}, familles {familles}, appareil {appareil} ===")

    tokeniseur, modele = charger_modele(MODELE, len(familles))
    historique: list[dict] = []
    meilleur: dict = {"macro_f1": -1.0}

    def apres_epoque(epoque: int, m) -> None:
        probas = predire_probas(m, tokeniseur, val["texte"].tolist(), appareil, REGLAGES["longueur_max"])
        tableau, seuils = evaluer(y_val, probas, familles)
        macro = float(tableau.loc["macro", "f1"])
        historique.append({"epoque": epoque, "macro_f1_val": round(macro, 4)})
        print(f"  époque {epoque} : macro-F1 val = {macro:.3f}")
        if macro > meilleur["macro_f1"]:
            meilleur.update(macro_f1=macro, epoque=epoque, tableau=tableau, seuils=seuils, probas=probas,
                            etat={k: v.detach().cpu().clone() for k, v in m.state_dict().items()})

    pertes = entrainer(modele, tokeniseur, train["texte"].tolist(), y_train, appareil,
                       REGLAGES["epoques"], REGLAGES["taux_apprentissage"], REGLAGES["taille_lot"],
                       REGLAGES["longueur_max"], REGLAGES["graine"], apres_epoque, poids_racine)

    tableau = meilleur["tableau"]
    print(f"Meilleure époque : {meilleur['epoque']} ; seuils : {meilleur['seuils']}")
    print(tableau[["precision", "rappel", "f1", "vp", "fp", "fn", "support"]].astype(float).round(3))
    reference = tfidf_reference(train, val, familles)

    rappels: dict[str, float] = {}
    if tache == "cuad":
        textes, annotations = charger_cuad(DOSSIER_CUAD / "CUAD_v1.json")
        jeu_de = lire_splits(RACINE / "data" / "splits" / "cuad_v1_splits.json")
        annotations_val: dict[str, list] = {}
        for a in annotations:
            if a.categorie in FAMILLE_DE and jeu_de[a.titre] == "val":
                annotations_val.setdefault(a.titre, []).append(a)
        predictions = {f: meilleur["probas"][:, k] >= meilleur["seuils"][f] for k, f in enumerate(familles)}
        rappels = rappel_par_annotation(val, predictions, 0, textes, annotations_val, DOSSIER_CUAD / "full_contract_pdf")
        print(f"Rappel par annotation : {({k: round(v, 3) for k, v in rappels.items()})}")

    comparaison = pd.DataFrame({"TF-IDF F1": reference["f1"], "Transformer F1": tableau["f1"]}).astype(float).round(3)
    print("\nComparaison (validation) :\n", comparaison)

    # Sauvegarde du meilleur modèle (dossier models/, ignoré par Git).
    modele.load_state_dict(meilleur["etat"])
    suffixe = "-poids-racine" if poids_racine else ""
    dossier = DOSSIER_MODELES / f"f2-{tache}-legal-bert-small{suffixe}"
    modele.save_pretrained(dossier)
    tokeniseur.save_pretrained(dossier)

    mlflow.set_tracking_uri(URI_MLFLOW)
    mlflow.set_experiment("F2-transformer")
    with mlflow.start_run(run_name=f"{tache}-legal-bert-small{suffixe}"):
        mlflow.log_params({"modele": MODELE, "tache": tache, "evaluation": "val" if tache == "cuad" else "dev",
                           "meilleure_epoque": meilleur["epoque"], **REGLAGES, "poids_positifs": "racine" if poids_racine else "rapport",
                           **{f"{SLUG[f]}_seuil": s for f, s in meilleur["seuils"].items()},
                           "dossier_modele": str(dossier.relative_to(RACINE))})
        for f in familles:
            mlflow.log_metric(f"val_{SLUG[f]}_f1", float(tableau.loc[f, "f1"]))
            mlflow.log_metric(f"val_{SLUG[f]}_tfidf_f1", float(reference.loc[f, "f1"]))
        mlflow.log_metric("val_macro_f1", float(tableau.loc["macro", "f1"]))
        mlflow.log_metric("val_macro_f1_tfidf", float(reference.loc["macro", "f1"]))
        for k, v in rappels.items():
            mlflow.log_metric(f"val_{SLUG.get(k, k)}_rappel_annotation", v)
        for i, p in enumerate(pertes, start=1):
            mlflow.log_metric("perte_entrainement", p, step=i)
        for h in historique:
            mlflow.log_metric("macro_f1_val_par_epoque", h["macro_f1_val"], step=h["epoque"])


def main() -> None:
    """Lit la tâche demandée et la lance."""
    parseur = argparse.ArgumentParser(description="Transformer d'extraction (F2).")
    parseur.add_argument("--tache", choices=["cuad", "confidentialite", "les-deux"], default="les-deux")
    parseur.add_argument("--poids-racine", action="store_true",
                         help="Poids des positifs atténué (racine carrée), expérience 2.")
    arguments = parseur.parse_args()
    for t in (["confidentialite", "cuad"] if arguments.tache == "les-deux" else [arguments.tache]):
        lancer(t, arguments.poids_racine)


if __name__ == "__main__":
    main()
