"""Script : comparer BM25, le texte intégral de PostgreSQL, les embeddings et les hybrides (F5, D-024).

Lancement, depuis la racine du projet, avec le .venv et la base démarrée :

    PYTHONPATH=src .venv/bin/python -u evaluation/evaluer_recherche_bm25.py

Questions : les mêmes que ``evaluer_qr_f5.py`` (41 questions CUAD posées à chacun des 61 contrats de
**validation**) ; seules les questions **avec réponse** comptent pour la recherche. Le test reste fermé.

Mesures (sur les 10 premiers résultats) :
- **rappel@k** (k = 1, 3, 5, 10) : part des questions dont au moins un segment de réponse est dans
  les k premiers résultats ;
- **MRR** (*Mean Reciprocal Rank*) : moyenne de 1 / rang du premier segment de réponse (0 s'il n'est
  pas dans les 10 premiers). Un MRR de 0,5 veut dire « en moyenne, la bonne réponse arrive vers le
  2e rang ».

Rien n'est réglé ici : k1 = 1,2 et b = 0,75 sont fixés d'avance (``cg.recherche.bm25``).
"""

from pathlib import Path

import mlflow
import numpy as np
import pandas as pd

from cg.datasets.splits import lire_splits
from cg.recherche.embeddings import Encodeur
from cg.recherche.hybride import rechercher
from cg.recherche.questions_cuad import questions
from cg.stockage.connexion import connecter

RACINE = Path(__file__).resolve().parents[1]
MODES = ("mots", "bm25", "sens", "hybride", "hybride_bm25")
NOMS = {"mots": "mots : texte intégral PostgreSQL (ts_rank_cd)", "bm25": "mots : BM25",
        "sens": "sens : embeddings (bge-small)", "hybride": "hybride : PostgreSQL + embeddings (actuel)",
        "hybride_bm25": "hybride : BM25 + embeddings"}
K = (1, 3, 5, 10)


def mesures(rangs: list[int | None]) -> dict[str, float]:
    """Rappel@k et MRR à partir du rang du premier bon segment de chaque question.

    Args:
        rangs: Pour chaque question, rang (1 = premier) du premier segment de réponse, ou ``None``.

    Returns:
        Les mesures, arrondies à 3 décimales.
    """
    m = {f"rappel@{k}": float(np.mean([r is not None and r <= k for r in rangs])) for k in K}
    m["MRR"] = float(np.mean([1.0 / r if r is not None else 0.0 for r in rangs]))
    return {k: round(v, 3) for k, v in m.items()}


def main() -> None:
    """Mesure chaque méthode de recherche sur les questions de validation avec réponse."""
    jeu_de = lire_splits(RACINE / "data" / "splits" / "cuad_v1_splits.json")
    with connecter() as connexion, connexion.cursor() as curseur:
        curseur.execute("SELECT titre, id FROM contrats WHERE source = 'cuad'")
        contrats = dict(curseur.fetchall())
    validation = sorted(t for t in contrats if jeu_de.get(t) == "val")
    q_val = [q for q in questions(contrats, validation) if q["avec_reponse"]]
    print(f"{len(q_val)} questions de validation avec réponse ({len(validation)} contrats)", flush=True)

    encodeur = Encodeur()
    vecteurs = {r: encodeur.encoder_requete(r) for r in {q["requete"] for q in q_val}}
    rangs: dict[str, list[int | None]] = {m: [] for m in MODES}
    with connecter() as connexion:
        for n, q in enumerate(q_val, start=1):
            for m in MODES:
                trouves = rechercher(connexion, encodeur, q["contrat_id"], q["requete"], 10, m, vecteurs[q["requete"]])
                rang = next((i for i, r in enumerate(trouves, start=1) if r.segment_id in q["or"]), None)
                rangs[m].append(rang)
            if n % 200 == 0:
                print(f"  {n} questions", flush=True)

    tableau = pd.DataFrame([{"recherche": NOMS[m], **mesures(rangs[m])} for m in MODES])
    print("\nRecherche (validation, questions avec réponse) :")
    print(tableau.to_string(index=False))

    mlflow.set_tracking_uri(f"sqlite:///{RACINE / 'mlflow.db'}")
    mlflow.set_experiment("F5-questions-reponses")
    for m in MODES:
        with mlflow.start_run(run_name=f"recherche-{m}-validation"):
            mlflow.log_params({"recherche": m, "questions": len(q_val), "k1": 1.2, "b": 0.75, "k_rrf": 60})
            mlflow.log_metrics({k.replace("@", "_a_"): v for k, v in mesures(rangs[m]).items()})


if __name__ == "__main__":
    main()
