"""Script : segments PDF étiquetés par famille, pour train et validation (D-007, D-008).

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -m cg.datasets.preparer_segments_pdf [--seuil-fusion N]

Pour chaque contrat de **train et de validation** (le test n'est pas préparé : il ne sera ouvert
qu'avec une décision écrite) :
1. extraction PyMuPDF en mode « blocs » (D-008), segmentation v1 ;
2. option 3 de D-008 (expérience) : fusion des segments de moins de ``N`` caractères avec le
   suivant de la même page (``N = 0`` : pas de fusion) ;
3. alignement exact des annotations CUAD après normalisation étendue (D-007) ; les annotations
   non retrouvées sont comptées et listées **par référence** (titre, catégorie, positions CUAD),
   puis exclues ;
4. projection des annotations alignées sur les segments (même règle que pour CUAD).

Sorties (dans ``data/processed/``, jamais commitées) :
- ``cuad_pdf_segments_fusion{N}.jsonl`` : une ligne par segment (avec sa page) ;
- ``cuad_pdf_annotations_exclues.jsonl`` : références des annotations non alignées.
"""

import argparse
import json
from pathlib import Path

from cg.datasets.cuad import FAMILLE_DE, Annotation, charger_cuad, projeter_annotations
from cg.datasets.splits import lire_splits
from cg.ingestion.alignement import aligner, normaliser
from cg.ingestion.pdf import extraire_pdf, segmenter_pdf, trouver_pdf
from cg.ingestion.segmentation import fusionner_fragments

RACINE = Path(__file__).resolve().parents[3]
DOSSIER_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1"
CHEMIN_SPLITS = RACINE / "data" / "splits" / "cuad_v1_splits.json"
DOSSIER_SORTIE = RACINE / "data" / "processed"
JEUX = {"train", "val"}  # le test reste fermé (règle 2, CLAUDE.md)


def chemin_segments_pdf(seuil_fusion: int) -> Path:
    """Fichier de sortie pour un seuil de fusion donné.

    Args:
        seuil_fusion: Seuil de fusion des fragments (0 = aucune fusion).

    Returns:
        Le chemin du fichier JSONL.
    """
    return DOSSIER_SORTIE / f"cuad_pdf_segments_fusion{seuil_fusion}.jsonl"


def main() -> None:
    """Prépare les segments PDF étiquetés et affiche un résumé."""
    parseur = argparse.ArgumentParser(description="Segments PDF étiquetés (train + val).")
    parseur.add_argument("--seuil-fusion", type=int, default=0,
                         help="Fusionner les segments de moins de N caractères (0 = non).")
    seuil = parseur.parse_args().seuil_fusion

    textes, annotations = charger_cuad(DOSSIER_CUAD / "CUAD_v1.json")
    jeu_de = lire_splits(CHEMIN_SPLITS)
    titres = sorted(t for t, jeu in jeu_de.items() if jeu in JEUX)
    par_contrat: dict[str, list[Annotation]] = {}
    for a in annotations:
        if a.categorie in FAMILLE_DE:
            par_contrat.setdefault(a.titre, []).append(a)

    lignes: list[dict[str, object]] = []
    exclues: list[dict[str, object]] = []
    total = 0
    for titre in titres:
        document = extraire_pdf(trouver_pdf(DOSSIER_CUAD / "full_contract_pdf", titre), titre, mode="blocs")
        segments = fusionner_fragments(document.texte, segmenter_pdf(document), seuil)
        cible = normaliser(document.texte, "etendue")
        contexte = textes[titre]
        alignees: list[Annotation] = []
        for a in par_contrat.get(titre, []):
            total += 1
            position = aligner(contexte[a.debut:a.fin], cible, "etendue", a.debut / len(contexte))
            if position is None:
                exclues.append({"titre": titre, "jeu": jeu_de[titre], "categorie": a.categorie,
                                "debut_cuad": a.debut, "fin_cuad": a.fin})
            else:
                alignees.append(Annotation(titre, a.categorie, position[0], position[1]))
        for e in projeter_annotations(segments, alignees):
            s = e.segment
            lignes.append({"titre": titre, "jeu": jeu_de[titre], "page": s.page, "debut": s.debut,
                           "fin": s.fin, "categories": e.categories, "familles": e.familles,
                           "texte": s.texte})

    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)
    sortie = chemin_segments_pdf(seuil)
    with open(sortie, "w", encoding="utf-8") as fichier:
        for ligne in lignes:
            fichier.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    with open(DOSSIER_SORTIE / "cuad_pdf_annotations_exclues.jsonl", "w", encoding="utf-8") as fichier:
        for ligne in exclues:
            fichier.write(json.dumps(ligne, ensure_ascii=False) + "\n")

    longueurs = sorted(int(l["fin"]) - int(l["debut"]) for l in lignes)
    print(f"Seuil de fusion : {seuil} ; contrats : {len(titres)} (train + val)")
    print(f"Segments : {len(lignes)} ; médiane {longueurs[len(longueurs) // 2]} caractères ; "
          f"< 20 caractères : {sum(x < 20 for x in longueurs) / len(longueurs):.1%}")
    print(f"Annotations (nos 9) : {total} ; alignées {total - len(exclues)} ; "
          f"exclues {len(exclues)} ({len(exclues) / total:.1%}, références dans "
          f"data/processed/cuad_pdf_annotations_exclues.jsonl)")
    print(f"Écrit : {sortie.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
