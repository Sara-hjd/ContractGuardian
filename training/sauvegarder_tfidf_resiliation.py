"""Script : entraîner et sauvegarder le modèle TF-IDF de la résiliation retenu par D-012.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python training/sauvegarder_tfidf_resiliation.py

Réglages retenus **sur la validation** (D-011, D-012) : bigrammes, C = 10, poids des classes
équilibré, segments PDF par blocs du **train**. Le seuil de décision (0,54) est appliqué par
l'application (``cg.extraction.pipeline``). Sortie : ``models/f2-resiliation-tfidf.joblib`` (non commité).
"""

from pathlib import Path

import joblib

from cg.datasets.segments import charger_segments
from cg.extraction.tfidf import creer_vectoriseur, entrainer_classifieur

RACINE = Path(__file__).resolve().parents[1]
CHEMIN_SORTIE = RACINE / "models" / "f2-resiliation-tfidf.joblib"


def main() -> None:
    """Entraîne sur le train et sauvegarde le vectoriseur et le classifieur ensemble."""
    train = charger_segments(RACINE / "data" / "processed" / "cuad_pdf_segments_fusion0.jsonl", {"train"})
    vectoriseur = creer_vectoriseur(2)
    classifieur = entrainer_classifieur(vectoriseur.fit_transform(train["texte"]), train["résiliation"].to_numpy(), 10.0)
    CHEMIN_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"vectoriseur": vectoriseur, "classifieur": classifieur, "famille": "résiliation"}, CHEMIN_SORTIE)
    print(f"Sauvegardé : {CHEMIN_SORTIE.relative_to(RACINE)} ({CHEMIN_SORTIE.stat().st_size / 1e6:.1f} Mo)")


if __name__ == "__main__":
    main()
