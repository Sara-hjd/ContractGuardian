"""Script : seuil de la famille confidentialité selon le critère de D-012, sur le DEV de ContractNLI.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -u evaluation/seuil_confidentialite.py

Critère (D-012) : rappel par annotation maximal sous précision par segment ≥ 0,50. Ici une
« annotation » est une phrase d'évidence de ContractNLI (hypothèses retenues par D-009) ; elle est
trouvée si un segment qu'elle étiquette est prédit positif. Test de ContractNLI fermé.
"""

from pathlib import Path

import numpy as np
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from cg.datasets.contractnli import annotations_confidentialite, charger_contractnli
from cg.datasets.cuad import categories_par_segment, chevauchement, SEUIL_CHEVAUCHEMENT
from cg.extraction.metriques import metriques_binaires
from cg.extraction.transformer import choisir_appareil, predire_probas
from cg.ingestion.segmentation import segmenter

RACINE = Path(__file__).resolve().parents[1]
SEUILS = np.unique(np.concatenate([np.round(np.arange(0.01, 0.991, 0.01), 2), [0.995, 0.999]]))


def main() -> None:
    """Prédit le dev, puis cherche le seuil admissible au meilleur rappel par évidence."""
    dev, _ = charger_contractnli(RACINE / "data" / "raw" / "contractnli" / "contract-nli.zip", "dev")
    textes, y, evidences = [], [], []  # evidences : pour chaque évidence, indices (globaux) des segments étiquetés
    for d in dev:
        segments = segmenter(d.titre, d.texte, coupe_aux_lignes=True)
        annotations = annotations_confidentialite(d)
        base = len(textes)
        textes += [s.texte for s in segments]
        y += [bool(c) for c in categories_par_segment(segments, annotations)]
        for a in annotations:
            seuil = min(SEUIL_CHEVAUCHEMENT, a.fin - a.debut)
            evidences.append([base + i for i, s in enumerate(segments)
                              if chevauchement(s.debut, s.fin, a.debut, a.fin) >= seuil])
    y = np.array(y)
    chemin = RACINE / "models" / "f2-confidentialite-legal-bert-small"
    appareil = choisir_appareil()
    probas = predire_probas(AutoModelForSequenceClassification.from_pretrained(chemin).to(appareil),
                            AutoTokenizer.from_pretrained(chemin), textes, appareil, 256)[:, 0]
    meilleur = None
    for s in SEUILS:
        pred = probas >= s
        m = metriques_binaires(y, pred)
        if not pred.any() or m["precision"] < 0.50:
            continue
        rappel = float(np.mean([pred[idx].any() if idx else False for idx in evidences]))
        if meilleur is None or rappel > meilleur[1]:
            meilleur = (float(s), rappel, m)
    s, rappel, m = meilleur
    print(f"Dev : {len(textes)} segments, {len(evidences)} phrases d'évidence")
    print(f"Seuil retenu : {s} ; rappel par évidence {rappel:.3f} ; précision {m['precision']:.3f} ; "
          f"rappel par segment {m['rappel']:.3f} ; F1 {m['f1']:.3f}")


if __name__ == "__main__":
    main()
