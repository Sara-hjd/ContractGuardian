"""Script : segmenter les contrats CUAD et étiqueter les segments par famille (D-001, F2).

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -m cg.datasets.preparer_segments

Entrées : ``CUAD_v1.json`` et le fichier des splits (``data/splits/cuad_v1_splits.json``).
Sortie : ``data/processed/cuad_segments_v1.jsonl``, une ligne JSON par segment, avec sa
provenance (titre, début, fin), son jeu, ses catégories, ses familles et son texte.
Ce fichier contient du texte de contrat : il reste dans ``data/processed/``, jamais commité.
"""

import json
from pathlib import Path

import pandas as pd

from cg.datasets.cuad import (
    FAMILLES,
    SEUIL_CHEVAUCHEMENT,
    Annotation,
    charger_cuad,
    chevauchement,
    projeter_annotations,
)
from cg.datasets.splits import JEUX, lire_splits
from cg.ingestion.segmentation import MAX_CARACTERES, segmenter

RACINE = Path(__file__).resolve().parents[3]
CHEMIN_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1" / "CUAD_v1.json"
CHEMIN_SPLITS = RACINE / "data" / "splits" / "cuad_v1_splits.json"
CHEMIN_SORTIE = RACINE / "data" / "processed" / "cuad_segments_v1.jsonl"


def main() -> None:
    """Segmente, étiquette, écrit le JSONL et affiche les statistiques."""
    textes, annotations = charger_cuad(CHEMIN_CUAD)
    jeu_de = lire_splits(CHEMIN_SPLITS)

    annotations_par_contrat: dict[str, list[Annotation]] = {}
    for annotation in annotations:
        annotations_par_contrat.setdefault(annotation.titre, []).append(annotation)

    lignes: list[dict[str, object]] = []
    nb_nos_annotations = 0
    annotations_perdues = 0  # annotations de nos catégories qui n'étiquettent aucun segment
    for titre in sorted(textes):
        segments = segmenter(titre, textes[titre])
        annotations_contrat = annotations_par_contrat.get(titre, [])
        for etiquete in projeter_annotations(segments, annotations_contrat):
            s = etiquete.segment
            lignes.append({
                "titre": s.titre,
                "jeu": jeu_de[titre],
                "debut": s.debut,
                "fin": s.fin,
                "page": s.page,
                "categories": etiquete.categories,
                "familles": etiquete.familles,
                "texte": s.texte,
            })
        for a in annotations_contrat:
            if a.categorie not in {c for cats in FAMILLES.values() for c in cats}:
                continue
            nb_nos_annotations += 1
            seuil = min(SEUIL_CHEVAUCHEMENT, a.fin - a.debut)
            if not any(chevauchement(s.debut, s.fin, a.debut, a.fin) >= seuil for s in segments):
                annotations_perdues += 1

    CHEMIN_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHEMIN_SORTIE, "w", encoding="utf-8") as sortie:
        for ligne in lignes:
            sortie.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    print(f"Écrit : {CHEMIN_SORTIE.relative_to(RACINE)} ({len(lignes)} segments)")
    print(f"Règle v1 : lignes vides, plafond {MAX_CARACTERES} caractères ; "
          f"seuil de chevauchement min({SEUIL_CHEVAUCHEMENT}, longueur de l'annotation)")

    # --- Statistiques -------------------------------------------------------------------
    df = pd.DataFrame(lignes)
    df["longueur"] = df["fin"] - df["debut"]
    for famille in FAMILLES:
        df[famille] = df["familles"].map(lambda fams, f=famille: f in fams)
    df["aucune"] = df["familles"].map(len) == 0

    print("\nContrats et segments par jeu :")
    par_jeu = df.groupby("jeu").agg(contrats=("titre", "nunique"), segments=("titre", "size"))
    print(par_jeu.reindex(list(JEUX)))

    print("\nProportion de segments par famille (en %, un segment peut avoir plusieurs familles) :")
    colonnes = [*FAMILLES, "aucune"]
    print((df.groupby("jeu")[colonnes].mean() * 100).round(2).reindex(list(JEUX)))

    print("\nNombre de segments par famille :")
    print(df.groupby("jeu")[colonnes].sum().reindex(list(JEUX)))

    print("\nLongueur des segments (caractères) :")
    print(df["longueur"].describe(percentiles=[0.1, 0.5, 0.9]).round(1))
    print(f"Segments de moins de 20 caractères : {(df['longueur'] < 20).mean() * 100:.1f} %")
    print(f"Segments au plafond ({MAX_CARACTERES}) ou presque (>= 1400) : "
          f"{(df['longueur'] >= 1400).mean() * 100:.1f} %")

    print(f"\nAnnotations de nos 9 catégories : {nb_nos_annotations}")
    print(f"... qui n'étiquettent aucun segment : {annotations_perdues}")


if __name__ == "__main__":
    main()
