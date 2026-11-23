"""Script : réévaluer F4 (NLI) avec des grilles de seuils élargies, sur le dev de ContractNLI.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -u evaluation/reevaluer_seuils_nli.py

Pourquoi : à l'entraînement (journal L6), le seuil d'évidence retenu valait 0,95, le maximum de sa
grille. On recharge le modèle sauvegardé (pas de réentraînement) et on règle les deux seuils sur
des grilles allant jusqu'à 0,999, sur le **dev** seulement. Test fermé.
"""

from pathlib import Path

import mlflow
import numpy as np
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from cg.datasets.contractnli import charger_contractnli
from cg.extraction.transformer import choisir_appareil
from cg.nli.evaluation import metriques_etiquettes, metriques_evidences
from cg.nli.modele import decider, probas_paires
from cg.nli.paires import paires_document

RACINE = Path(__file__).resolve().parents[1]
FIN = [0.96, 0.97, 0.98, 0.99, 0.995, 0.999]
SEUILS_DOCUMENT = np.unique(np.concatenate([np.round(np.arange(0.30, 0.951, 0.05), 2), FIN]))
SEUILS_EVIDENCE = np.unique(np.concatenate([np.round(np.arange(0.10, 0.951, 0.05), 2), FIN]))


def main() -> None:
    """Recharge le modèle, prédit le dev, règle les deux seuils sur les grilles élargies."""
    dev, labels = charger_contractnli(RACINE / "data" / "raw" / "contractnli" / "contract-nli.zip", "dev")
    hypotheses = {h: v["hypothesis"] for h, v in sorted(labels.items())}
    couples = [(d, h) for d in dev for h in hypotheses]
    vraies = [d.choix.get(h, "NotMentioned") for d, h in couples]
    toutes, bornes = [], []
    for d, h in couples:
        p = paires_document(d, h, hypotheses[h])
        bornes.append((len(toutes), len(toutes) + len(p)))
        toutes.extend(p)
    dossier = RACINE / "models" / "f4-nli-legal-bert-small"
    appareil = choisir_appareil()
    modele = AutoModelForSequenceClassification.from_pretrained(dossier).to(appareil)
    probas = probas_paires(modele, AutoTokenizer.from_pretrained(dossier), toutes, appareil, 128)

    def evaluer(sd: float, se: float) -> tuple[dict, dict]:
        decisions = [decider(probas[a:b], sd, se) for a, b in bornes]
        avec = [i for i, v in enumerate(vraies) if v != "NotMentioned"]
        return (metriques_etiquettes(vraies, [x.etiquette for x in decisions]),
                metriques_evidences([set(couples[i][0].evidences.get(couples[i][1], [])) for i in avec],
                                    [set(decisions[i].evidences) for i in avec]))

    seuil_doc = float(max(SEUILS_DOCUMENT, key=lambda s: evaluer(float(s), 0.5)[0]["macro_f1"]))
    seuil_ev = float(max(SEUILS_EVIDENCE, key=lambda s: evaluer(seuil_doc, float(s))[1]["f1"]))
    etiquettes, evidences = evaluer(seuil_doc, seuil_ev)
    print(f"Seuils (dev, grilles élargies) : document {seuil_doc}, évidence {seuil_ev}")
    print("Étiquettes :", {k: round(v, 3) for k, v in etiquettes.items()})
    print("Évidences  :", {k: round(v, 3) for k, v in evidences.items()})
    mlflow.set_tracking_uri(f"sqlite:///{RACINE / 'mlflow.db'}")
    mlflow.set_experiment("F4-nli")
    with mlflow.start_run(run_name="legal-bert-small-paires-seuils-elargis"):
        mlflow.log_params({"modele_relu": str(dossier.relative_to(RACINE)), "seuil_document": seuil_doc,
                           "seuil_evidence": seuil_ev, "evaluation": "dev"})
        mlflow.log_metrics({f"dev_{k}": v for k, v in etiquettes.items()})
        mlflow.log_metrics({f"dev_evidence_{k}": v for k, v in evidences.items()})


if __name__ == "__main__":
    main()
