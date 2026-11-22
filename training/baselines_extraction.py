"""Script : entraîner et comparer les deux baselines d'extraction (F2) sur la validation.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python training/baselines_extraction.py

Protocole (décision D-006) :
- entraînement sur ``train`` ; tous les réglages (n-grammes, C, seuil par famille) sur ``val`` ;
- le jeu de test n'est PAS chargé (``charger_segments`` le refuse) ;
- un run MLflow par baseline (paramètres + métriques), base locale ``mlflow.db`` (non commitée) ;
- les erreurs de validation de la baseline 2 sont écrites dans ``data/processed/`` (elles
  contiennent du texte de contrat : jamais commitées).

Les métriques de validation sont un peu optimistes, puisque les seuils y sont aussi réglés.
"""

import json
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd

from cg.datasets.cuad import FAMILLES
from cg.datasets.segments import charger_segments, etiquettes
from cg.extraction.metriques import choisir_seuil, tableau_metriques
from cg.extraction.mots_cles import MOTS_CLES, predire_mots_cles
from cg.extraction.tfidf import creer_vectoriseur, entrainer_classifieur, mots_les_plus_lourds

RACINE = Path(__file__).resolve().parents[1]
CHEMIN_SEGMENTS = RACINE / "data" / "processed" / "cuad_segments_v1.jsonl"
CHEMIN_ERREURS = RACINE / "data" / "processed" / "erreurs_val_tfidf.jsonl"
URI_MLFLOW = f"sqlite:///{RACINE / 'mlflow.db'}"
EXPERIENCE = "F2-extraction-baselines"

# Grille de réglage, fixée avant de lancer (D-006).
GRILLE_NGRAM: list[int] = [1, 2]
GRILLE_C: list[float] = [0.1, 1.0, 10.0]
MIN_DF = 2
GRAINE = 0

# MLflow : noms de métriques sans accents, par prudence.
SLUG: dict[str, str] = {"durée": "duree", "résiliation": "resiliation", "responsabilité": "responsabilite"}


def journaliser_metriques(tableau: pd.DataFrame, prefixe: str = "") -> None:
    """Envoie à MLflow la précision, le rappel et le F1 de chaque famille, et le macro-F1.

    Args:
        tableau: Tableau produit par ``tableau_metriques``.
        prefixe: Préfixe ajouté aux noms de métriques (par exemple ``"seuil05_"``).
    """
    for famille in FAMILLES:
        for mesure in ("precision", "rappel", "f1"):
            mlflow.log_metric(f"{prefixe}val_{SLUG[famille]}_{mesure}", float(tableau.loc[famille, mesure]))
    mlflow.log_metric(f"{prefixe}val_macro_f1", float(tableau.loc["macro", "f1"]))


def afficher(titre: str, tableau: pd.DataFrame) -> None:
    """Affiche un tableau de métriques arrondi.

    Args:
        titre: Titre affiché au-dessus.
        tableau: Tableau produit par ``tableau_metriques``.
    """
    print(f"\n=== {titre} ===")
    print(tableau[["precision", "rappel", "f1", "vp", "fp", "fn", "support"]].astype(float).round(3))


def main() -> None:
    """Entraîne, règle sur la validation, évalue, journalise et écrit les erreurs."""
    train = charger_segments(CHEMIN_SEGMENTS, {"train"})
    val = charger_segments(CHEMIN_SEGMENTS, {"val"})
    y_train, y_val = etiquettes(train), etiquettes(val)
    print(f"Segments : train {len(train)}, val {len(val)} (test fermé)")

    mlflow.set_tracking_uri(URI_MLFLOW)
    mlflow.set_experiment(EXPERIENCE)

    # --- Baseline 1 : mots-clés --------------------------------------------------------------
    pred_mots_cles = predire_mots_cles(val["texte"].tolist())
    tableau_1 = tableau_metriques(y_val, pred_mots_cles)
    afficher("Baseline 1 : mots-clés (validation)", tableau_1)
    with mlflow.start_run(run_name="baseline-1-mots-cles"):
        mlflow.log_params({"modele": "mots-cles", "segments": "cuad_segments_v1", "evaluation": "val"})
        mlflow.log_params({f"nb_motifs_{SLUG[f]}": len(m) for f, m in MOTS_CLES.items()})
        journaliser_metriques(tableau_1)

    # --- Baseline 2 : TF-IDF + régression logistique, réglée sur val ----------------------------
    grille: list[dict[str, object]] = []
    meilleurs: dict[str, dict[str, object]] = {}
    for ngram in GRILLE_NGRAM:
        vectoriseur = creer_vectoriseur(ngram, MIN_DF)
        X_train = vectoriseur.fit_transform(train["texte"])  # vocabulaire appris sur train seulement
        X_val = vectoriseur.transform(val["texte"])
        for famille in FAMILLES:
            for C in GRILLE_C:
                classifieur = entrainer_classifieur(X_train, y_train[famille], C, GRAINE)
                probas = classifieur.predict_proba(X_val)[:, 1]
                seuil, f1 = choisir_seuil(y_val[famille], probas)
                grille.append({"famille": famille, "ngram_max": ngram, "C": C,
                               "seuil": seuil, "f1_val": round(f1, 4),
                               "f1_val_seuil05": round(float(
                                   tableau_metriques({famille: y_val[famille]},
                                                     {famille: probas >= 0.5}).loc[famille, "f1"]), 4)})
                if f1 > float(meilleurs.get(famille, {}).get("f1", -1.0)):
                    meilleurs[famille] = {"ngram_max": ngram, "C": C, "seuil": seuil, "f1": f1,
                                          "probas": probas,
                                          "mots": mots_les_plus_lourds(vectoriseur, classifieur)}
        print(f"  grille : n-grammes 1..{ngram} terminés")

    pred_tfidf = {f: meilleurs[f]["probas"] >= meilleurs[f]["seuil"] for f in FAMILLES}
    pred_tfidf_05 = {f: meilleurs[f]["probas"] >= 0.5 for f in FAMILLES}
    tableau_2 = tableau_metriques(y_val, pred_tfidf)
    tableau_2_05 = tableau_metriques(y_val, pred_tfidf_05)
    afficher("Baseline 2 : TF-IDF + rég. logistique, seuil 0,5 (validation)", tableau_2_05)
    afficher("Baseline 2 : TF-IDF + rég. logistique, seuil réglé (validation)", tableau_2)

    tableau_grille = pd.DataFrame(grille)
    print("\nGrille (F1 sur val au meilleur seuil) :")
    print(tableau_grille.pivot_table(index=["famille", "ngram_max"], columns="C", values="f1_val"))
    print("\nRéglages retenus :")
    for famille in FAMILLES:
        m = meilleurs[famille]
        print(f"  {famille:15s} n-grammes 1..{m['ngram_max']}  C={m['C']}  seuil={m['seuil']}")

    with mlflow.start_run(run_name="baseline-2-tfidf-logreg"):
        mlflow.log_params({"modele": "tfidf+logreg", "segments": "cuad_segments_v1",
                           "evaluation": "val", "min_df": MIN_DF, "class_weight": "balanced",
                           "sublinear_tf": True, "grille_ngram": str(GRILLE_NGRAM),
                           "grille_C": str(GRILLE_C)})
        for famille in FAMILLES:
            m = meilleurs[famille]
            mlflow.log_params({f"{SLUG[famille]}_ngram_max": m["ngram_max"],
                               f"{SLUG[famille]}_C": m["C"], f"{SLUG[famille]}_seuil": m["seuil"]})
        journaliser_metriques(tableau_2)
        journaliser_metriques(tableau_2_05, prefixe="seuil05_")
        mlflow.log_text(tableau_grille.to_csv(index=False), "grille_validation.csv")
        mlflow.log_text(json.dumps({f: meilleurs[f]["mots"] for f in FAMILLES},
                                   ensure_ascii=False, indent=2), "mots_les_plus_lourds.json")

    # --- Comparaison ---------------------------------------------------------------------------
    comparaison = pd.DataFrame({
        "mots-clés F1": tableau_1["f1"], "tfidf F1": tableau_2["f1"],
        "mots-clés P": tableau_1["precision"], "tfidf P": tableau_2["precision"],
        "mots-clés R": tableau_1["rappel"], "tfidf R": tableau_2["rappel"],
    }).astype(float).round(3)
    print("\n=== Comparaison (validation) ===")
    print(comparaison)

    print("\nMots les plus lourds (baseline 2) :")
    for famille in FAMILLES:
        print(f"  {famille:15s}", ", ".join(mot for mot, _ in meilleurs[famille]["mots"]))

    # --- Erreurs de validation (pour l'analyse ; contient du texte : jamais commité) -----------
    nb = 0
    with open(CHEMIN_ERREURS, "w", encoding="utf-8") as sortie:
        for famille in FAMILLES:
            probas = meilleurs[famille]["probas"]
            for i in np.flatnonzero(pred_tfidf[famille] != y_val[famille]):
                ligne = val.iloc[i]
                sortie.write(json.dumps({
                    "famille": famille,
                    "type": "faux_positif" if pred_tfidf[famille][i] else "faux_negatif",
                    "proba": round(float(probas[i]), 3),
                    "titre": ligne["titre"], "debut": int(ligne["debut"]), "fin": int(ligne["fin"]),
                    "categories": ligne["categories"], "texte": ligne["texte"],
                }, ensure_ascii=False) + "\n")
                nb += 1
    print(f"\n{nb} erreurs de validation écrites dans {CHEMIN_ERREURS.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
