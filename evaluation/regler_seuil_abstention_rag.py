"""Script : choisir le seuil d'abstention du RAG avec la courbe couverture / erreur (F5, D-025, étape 3).

À lancer **seulement après l'accord de Sara sur le critère de D-025** :

    PYTHONPATH=src .venv/bin/python -u evaluation/regler_seuil_abstention_rag.py --critere A [--recherche hybride_bm25]

Entrée : les réponses collectées sur les 200 questions de réglage du **train**
(``collecter_reglage_abstention_rag.py``). Pour chaque seuil s, une réponse vérifiée mot pour mot est
gardée si sa probabilité « implique » (NLI de F4) est ≥ s ; sinon, abstention.

- **Couverture** = réponses données / questions ; **erreur** = réponses fausses / réponses données.
- Critère **A** : maximiser l'exactitude équilibrée ; égalité → seuil le plus élevé (le plus prudent).
- Critère **B** : seuil le plus bas dont l'erreur ≤ 30 % ; si aucun, repli sur A.

Sorties : le tableau des seuils, le seuil choisi, la figure ``docs/analyses/courbe_abstention_rag_train_<recherche>.png``
et une exécution MLflow. La validation et le test ne sont pas lus.
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mlflow  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]
SEUILS: list[float | None] = [None] + [round(float(s), 2) for s in np.arange(0.05, 0.951, 0.05)]  # None = sans NLI
ERREUR_MAX_B = 0.30


def mesurer(lignes: list[dict], seuil: float | None) -> dict[str, float]:
    """Couverture, erreur et exactitude équilibrée pour un seuil donné.

    Args:
        lignes: Réponses collectées (une par question).
        seuil: Seuil sur la probabilité NLI ; ``None`` = pas de vérification NLI.

    Returns:
        Les mesures pour ce seuil.
    """
    avec = [l for l in lignes if l["avec_reponse"]]
    sans = [l for l in lignes if not l["avec_reponse"]]

    def repond(l: dict) -> bool:
        return (not l["abstention"]) and (seuil is None or (l["p_nli"] or 0.0) >= seuil)

    donnees = [l for l in lignes if repond(l)]
    fausses = [l for l in donnees if not l["juste"]]
    bonnes_rep = sum(repond(l) and l["juste"] for l in avec) / max(len(avec), 1)
    bonnes_abs = sum(not repond(l) for l in sans) / max(len(sans), 1)
    return {"couverture": len(donnees) / len(lignes), "erreur": len(fausses) / max(len(donnees), 1),
            "bonnes reponses": bonnes_rep, "bonnes abstentions": bonnes_abs,
            "exactitude equilibree": (bonnes_rep + bonnes_abs) / 2}


def choisir(tableau: pd.DataFrame, critere: str) -> float | None:
    """Applique le critère de D-025 au tableau des seuils.

    Args:
        tableau: Une ligne par seuil (colonne ``seuil``, ``None`` = sans NLI) avec les mesures.
        critere: ``"A"`` ou ``"B"``.

    Returns:
        Le seuil choisi (``None`` = sans NLI).
    """
    avec_nli = tableau[tableau["seuil"].notna()]
    if critere == "B":
        possibles = avec_nli[avec_nli["erreur"] <= ERREUR_MAX_B]
        if len(possibles):
            return float(possibles["seuil"].min())
        print(f"Critère B : aucun seuil n'atteint une erreur ≤ {ERREUR_MAX_B:.0%} ; repli sur le critère A.")
    meilleur = tableau["exactitude equilibree"].max()
    ex_aequo = tableau[np.isclose(tableau["exactitude equilibree"], meilleur)]
    seuils = [s for s in ex_aequo["seuil"] if pd.notna(s)]
    return float(max(seuils)) if seuils else None


def main() -> None:
    """Calcule la courbe couverture / erreur sur le train et choisit le seuil selon le critère accepté."""
    parseur = argparse.ArgumentParser(description="Seuil d'abstention du RAG (D-025).")
    parseur.add_argument("--critere", required=True, choices=("A", "B"))
    parseur.add_argument("--recherche", default="hybride", choices=("hybride", "hybride_bm25"))
    arguments = parseur.parse_args()
    nom = "rag_reglage_train.jsonl" if arguments.recherche == "hybride" else f"rag_reglage_train_{arguments.recherche}.jsonl"
    lignes = [json.loads(l) for l in (RACINE / "data" / "processed" / nom).read_text(encoding="utf-8").splitlines()]
    assert len(lignes) == 200, f"collecte incomplète : {len(lignes)} questions sur 200"

    tableau = pd.DataFrame([{"seuil": s, **mesurer(lignes, s)} for s in SEUILS])
    print(tableau.round(3).to_string(index=False))
    seuil = choisir(tableau, arguments.critere)
    print(f"\nCritère {arguments.critere} → seuil choisi : {seuil if seuil is not None else 'sans NLI'}")

    courbe = tableau[tableau["seuil"].notna()]
    figure, axe = plt.subplots(figsize=(6, 4.5))
    axe.plot(courbe["couverture"], courbe["erreur"], marker="o")
    for _, ligne in courbe.iloc[::2].iterrows():
        axe.annotate(f"{ligne['seuil']:.2f}", (ligne["couverture"], ligne["erreur"]), fontsize=7,
                     xytext=(3, 3), textcoords="offset points")
    sans_nli = tableau[tableau["seuil"].isna()].iloc[0]
    axe.scatter([sans_nli["couverture"]], [sans_nli["erreur"]], marker="x", color="grey", label="sans NLI")
    if seuil is not None:
        choisi = courbe[np.isclose(courbe["seuil"], seuil)].iloc[0]
        axe.scatter([choisi["couverture"]], [choisi["erreur"]], s=120, facecolors="none", edgecolors="red",
                    label=f"seuil choisi ({seuil:.2f}, critère {arguments.critere})")
    axe.set_xlabel("Couverture (réponses données / questions)")
    axe.set_ylabel("Erreur (réponses fausses / réponses données)")
    axe.set_title(f"RAG : couverture / erreur, 200 questions de réglage (train)\nrecherche {arguments.recherche}")
    axe.legend(fontsize=8)
    figure.tight_layout()
    chemin = RACINE / "docs" / "analyses" / f"courbe_abstention_rag_train_{arguments.recherche}.png"
    figure.savefig(chemin, dpi=150)
    print(f"Figure : {chemin.relative_to(RACINE)}")

    mlflow.set_tracking_uri(f"sqlite:///{RACINE / 'mlflow.db'}")
    mlflow.set_experiment("F5-questions-reponses")
    with mlflow.start_run(run_name=f"seuil-abstention-rag-train-{arguments.recherche}-critere{arguments.critere}"):
        mlflow.log_params({"critere": arguments.critere, "recherche": arguments.recherche,
                           "questions": "200 questions de réglage (60 contrats du train, graine 0)",
                           "seuil_choisi": "sans NLI" if seuil is None else seuil})
        ligne = tableau[tableau["seuil"].isna()] if seuil is None else tableau[np.isclose(tableau["seuil"].fillna(-1), seuil)]
        mlflow.log_metrics({k.replace(" ", "_"): float(v) for k, v in ligne.iloc[0].items() if k != "seuil"})
        mlflow.log_artifact(str(chemin))


if __name__ == "__main__":
    main()
