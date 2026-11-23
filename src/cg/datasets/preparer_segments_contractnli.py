"""Script : segments ContractNLI étiquetés « confidentialité », pour train et dev (D-002).

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -m cg.datasets.preparer_segments_contractnli

Pour chaque accord de **train** et de **dev** (le test reste fermé) :
1. segmentation v1 **coupée à chaque saut de ligne** (le texte de ContractNLI n'a aucune ligne
   vide : un paragraphe par ligne ; proposition de D-009), plafond 1 500 caractères ;
2. projection des spans d'évidence des hypothèses retenues (toutes sauf nda-18, proposition de
   D-009) avec la même règle de chevauchement que pour CUAD ;
3. vérification de la traçabilité : ``texte[debut:fin] == segment``.

Sortie : ``data/processed/contractnli_segments.jsonl`` (texte de contrat : jamais commité).
"""

import json
from pathlib import Path

from cg.datasets.contractnli import annotations_confidentialite, charger_contractnli
from cg.datasets.cuad import categories_par_segment
from cg.ingestion.segmentation import segmenter

RACINE = Path(__file__).resolve().parents[3]
CHEMIN_ZIP = RACINE / "data" / "raw" / "contractnli" / "contract-nli.zip"
CHEMIN_SORTIE = RACINE / "data" / "processed" / "contractnli_segments.jsonl"


def main() -> None:
    """Segmente, étiquette, vérifie et écrit les segments ; affiche un résumé par jeu."""
    lignes: list[dict[str, object]] = []
    for jeu in ("train", "dev"):
        documents, _ = charger_contractnli(CHEMIN_ZIP, jeu)
        nb_positifs = nb_segments = non_tracables = 0
        for document in documents:
            segments = segmenter(document.titre, document.texte, coupe_aux_lignes=True)
            annotations = annotations_confidentialite(document)
            for s, hypotheses in zip(segments, categories_par_segment(segments, annotations)):
                non_tracables += document.texte[s.debut:s.fin] != s.texte
                positif = bool(hypotheses)  # au moins une évidence d'une hypothèse retenue
                nb_segments += 1
                nb_positifs += positif
                lignes.append({"titre": document.titre, "jeu": jeu, "debut": s.debut, "fin": s.fin,
                               "hypotheses": hypotheses, "confidentialite": positif, "texte": s.texte})
        print(f"{jeu:5s} : {len(documents)} accords, {nb_segments} segments, "
              f"{nb_positifs / nb_segments:.1%} positifs « confidentialité », non traçables : {non_tracables}")

    CHEMIN_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHEMIN_SORTIE, "w", encoding="utf-8") as sortie:
        for ligne in lignes:
            sortie.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    print(f"Écrit : {CHEMIN_SORTIE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
