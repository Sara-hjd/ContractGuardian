"""Script : prédire les alertes v1 sur les paires de F3, AVANT les annotations humaines.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -m cg.comparison.predire_alertes

Écrit ``docs/analyses/f3_alertes_v1_predictions.csv`` (références et décisions seulement, aucun
texte). Ce fichier est commité **avant** que Sara et Ilyas n'annotent : sa date prouve que la règle
n'a pas été ajustée sur leurs étiquettes.
"""

import csv
from pathlib import Path

from transformers import AutoModelForSequenceClassification, AutoTokenizer

from cg.comparison.alertes import decider_alerte
from cg.datasets.segments import charger_segments
from cg.extraction.transformer import choisir_appareil
from cg.nli.modele import probas_paires
from cg.nli.paires import INDICE, Paire

RACINE = Path(__file__).resolve().parents[3]
CHEMIN_PAIRES = RACINE / "data" / "annotations" / "f3_paires" / "paires_v1.csv"
CHEMIN_SEGMENTS = RACINE / "data" / "processed" / "cuad_pdf_segments_fusion0.jsonl"
CHEMIN_SORTIE = RACINE / "docs" / "analyses" / "f3_alertes_v1_predictions.csv"
DOSSIER_NLI = RACINE / "models" / "f4-nli-legal-bert-small"


def main() -> None:
    """Relit les deux clauses de chaque paire, applique le modèle NLI et la règle v1, écrit les décisions."""
    val = charger_segments(CHEMIN_SEGMENTS, {"val"})
    texte = {(t, d, f): x for t, d, f, x in zip(val["titre"], val["debut"], val["fin"], val["texte"])}
    with open(CHEMIN_PAIRES, encoding="utf-8", newline="") as f:
        paires = list(csv.DictReader(f))
    clauses = [(texte[(p["titre"], int(p["debut_a"]), int(p["fin_a"]))],
                texte[(p["titre"], int(p["debut_b"]), int(p["fin_b"]))]) for p in paires]

    appareil = choisir_appareil()
    modele = AutoModelForSequenceClassification.from_pretrained(DOSSIER_NLI).to(appareil)
    tokeniseur = AutoTokenizer.from_pretrained(DOSSIER_NLI)
    # Deux sens : (A comme hypothèse, B comme phrase) et (B, A) ; 256 tokens (clauses plus longues que les phrases de F4).
    jeux = [Paire(p["titre"], "f3", 0, a, b, 0) for p, (a, b) in zip(paires, clauses)] + \
           [Paire(p["titre"], "f3", 0, b, a, 0) for p, (a, b) in zip(paires, clauses)]
    probas = probas_paires(modele, tokeniseur, jeux, appareil, longueur_max=256)[:, INDICE["Contradiction"]]
    n = len(paires)

    CHEMIN_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHEMIN_SORTIE, "w", encoding="utf-8", newline="") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(["id_paire", "alerte", "raisons", "p_contradiction"])
        nb = 0
        for i, (p, (a, b)) in enumerate(zip(paires, clauses)):
            decision = decider_alerte(a, b, float(max(probas[i], probas[n + i])))
            nb += decision.alerte
            ecrivain.writerow([p["id_paire"], "oui" if decision.alerte else "non",
                               "|".join(decision.raisons), f"{decision.p_contradiction:.3f}"])
    print(f"{nb} alertes sur {n} paires ; écrit : {CHEMIN_SORTIE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
