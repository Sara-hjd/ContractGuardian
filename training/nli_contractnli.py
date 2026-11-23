"""Script : NLI sur ContractNLI (F4) — baseline et Transformer, évalués sur le dev.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -u training/nli_contractnli.py

- **Baseline** (article de ContractNLI) : pour chaque hypothèse, l'étiquette la plus fréquente dans
  le train ; aucune évidence citée.
- **Transformer** (D-014 proposée) : paires (hypothèse, phrase) à 3 classes, Legal-BERT small
  (D-012) ; décision au niveau du document par agrégation (``cg.nli.modele.decider``).
- Réglages fixés avant l'entraînement : 2 époques, taux 5e-5, lots de 32, 128 tokens, graine 0.
  Seuils (document, évidence) réglés sur le **dev**. Le test de ContractNLI reste fermé.

Sorties : run MLflow (expérience ``F4-nli``) ; modèle dans ``models/f4-nli-legal-bert-small``.
"""

from collections import Counter
from pathlib import Path

import mlflow
import numpy as np
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from cg.datasets.contractnli import charger_contractnli
from cg.extraction.transformer import choisir_appareil, fixer_graines
from cg.nli.evaluation import metriques_etiquettes, metriques_evidences
from cg.nli.modele import decider, entrainer_paires, probas_paires
from cg.nli.paires import ETIQUETTES, paires_document, paires_entrainement

RACINE = Path(__file__).resolve().parents[1]
CHEMIN_ZIP = RACINE / "data" / "raw" / "contractnli" / "contract-nli.zip"
MODELE = "nlpaueb/legal-bert-small-uncased"
REGLAGES = {"epoques": 2, "taux_apprentissage": 5e-5, "taille_lot": 32, "longueur_max": 128, "graine": 0}
SEUILS_DOCUMENT = np.round(np.arange(0.30, 0.951, 0.05), 2)
SEUILS_EVIDENCE = np.round(np.arange(0.10, 0.951, 0.05), 2)


def main() -> None:
    """Baseline, entraînement, réglage des seuils sur le dev, métriques, MLflow, sauvegarde."""
    fixer_graines(REGLAGES["graine"])
    train, labels = charger_contractnli(CHEMIN_ZIP, "train")
    dev, _ = charger_contractnli(CHEMIN_ZIP, "dev")
    hypotheses = {h: v["hypothesis"] for h, v in sorted(labels.items())}
    couples = [(d, h) for d in dev for h in hypotheses]
    vraies = [d.choix.get(h, "NotMentioned") for d, h in couples]
    print(f"Train : {len(train)} accords ; dev : {len(dev)} accords, {len(couples)} couples (document, hypothèse)")
    print("Étiquettes vraies (dev) :", dict(Counter(vraies)))

    # --- Baseline : classe majoritaire par hypothèse -------------------------------------------------
    majoritaire = {h: Counter(d.choix.get(h, "NotMentioned") for d in train).most_common(1)[0][0] for h in hypotheses}
    base = metriques_etiquettes(vraies, [majoritaire[h] for _, h in couples])
    print("Baseline majoritaire :", {k: round(v, 3) for k, v in base.items()})

    # --- Transformer ------------------------------------------------------------------------------
    paires = paires_entrainement(train, hypotheses, REGLAGES["graine"])
    print(f"Paires d'entraînement : {len(paires)} ; répartition :",
          dict(Counter(ETIQUETTES[p.etiquette] for p in paires)))
    appareil = choisir_appareil()
    tokeniseur = AutoTokenizer.from_pretrained(MODELE)
    modele = AutoModelForSequenceClassification.from_pretrained(MODELE, num_labels=len(ETIQUETTES))
    pertes = entrainer_paires(modele, tokeniseur, paires, appareil, REGLAGES["epoques"],
                              REGLAGES["taux_apprentissage"], REGLAGES["taille_lot"],
                              REGLAGES["longueur_max"], REGLAGES["graine"])
    print("Pertes par époque :", [round(p, 4) for p in pertes])

    toutes, bornes = [], []
    for d, h in couples:
        p = paires_document(d, h, hypotheses[h])
        bornes.append((len(toutes), len(toutes) + len(p)))
        toutes.extend(p)
    probas = probas_paires(modele, tokeniseur, toutes, appareil, REGLAGES["longueur_max"])
    print(f"Paires évaluées sur le dev : {len(toutes)}")

    def evaluer(seuil_doc: float, seuil_ev: float) -> tuple[dict, dict]:
        decisions = [decider(probas[a:b], seuil_doc, seuil_ev) for a, b in bornes]
        etiquettes = metriques_etiquettes(vraies, [x.etiquette for x in decisions])
        avec = [i for i, v in enumerate(vraies) if v != "NotMentioned"]
        evid = metriques_evidences([set(couples[i][0].evidences.get(couples[i][1], [])) for i in avec],
                                   [set(decisions[i].evidences) for i in avec])
        return etiquettes, evid

    # Réglage sur le dev : d'abord le seuil du document (macro-F1), puis celui des évidences (F1).
    seuil_doc = max(SEUILS_DOCUMENT, key=lambda s: evaluer(float(s), 0.5)[0]["macro_f1"])
    seuil_ev = max(SEUILS_EVIDENCE, key=lambda s: evaluer(float(seuil_doc), float(s))[1]["f1"])
    etiquettes, evidences = evaluer(float(seuil_doc), float(seuil_ev))
    print(f"Seuils retenus (dev) : document {seuil_doc}, évidence {seuil_ev}")
    print("Transformer, étiquettes :", {k: round(v, 3) for k, v in etiquettes.items()})
    print("Transformer, évidences  :", {k: round(v, 3) for k, v in evidences.items()})

    dossier = RACINE / "models" / "f4-nli-legal-bert-small"
    modele.save_pretrained(dossier)
    tokeniseur.save_pretrained(dossier)
    mlflow.set_tracking_uri(f"sqlite:///{RACINE / 'mlflow.db'}")
    mlflow.set_experiment("F4-nli")
    with mlflow.start_run(run_name="baseline-majoritaire"):
        mlflow.log_params({"modele": "classe majoritaire par hypothèse", "evaluation": "dev"})
        mlflow.log_metrics({f"dev_{k}": v for k, v in base.items()})
    with mlflow.start_run(run_name="legal-bert-small-paires"):
        mlflow.log_params({"modele": MODELE, **REGLAGES, "paires_entrainement": len(paires),
                           "seuil_document": float(seuil_doc), "seuil_evidence": float(seuil_ev),
                           "evaluation": "dev", "dossier_modele": str(dossier.relative_to(RACINE))})
        mlflow.log_metrics({f"dev_{k}": v for k, v in etiquettes.items()})
        mlflow.log_metrics({f"dev_evidence_{k}": v for k, v in evidences.items()})
        for i, p in enumerate(pertes, start=1):
            mlflow.log_metric("perte_entrainement", p, step=i)


if __name__ == "__main__":
    main()
