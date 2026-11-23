"""Tests de la lecture de ContractNLI (D-002) et de la baseline de confidentialité.

Le petit zip est fabriqué ici, au format de ContractNLI, pour tester le code ; il ne sert jamais
à entraîner un modèle (règle 3).
"""

import json
import zipfile
from pathlib import Path

import pytest

from cg.datasets.contractnli import annotations_confidentialite, charger_contractnli
from cg.datasets.cuad import Annotation, categories_par_segment
from cg.extraction.mots_cles_confidentialite import predire_confidentialite
from cg.ingestion.segmentation import segmenter

TEXTE = "Recipient shall keep the information confidential.\nRecipient shall not solicit employees.\n"


def fabriquer_zip(chemin: Path) -> None:
    """Écrit un mini zip au format de ContractNLI (train et test)."""
    document = {
        "id": 1, "file_name": "nda-exemple.pdf", "text": TEXTE, "document_type": "search-pdf",
        "url": "", "spans": [[0, 51], [52, 90]],
        "annotation_sets": [{"annotations": {
            "nda-4": {"choice": "Entailment", "spans": [0]},
            "nda-18": {"choice": "Entailment", "spans": [1]},
        }}],
    }
    contenu = json.dumps({"documents": [document], "labels": {}})
    with zipfile.ZipFile(chemin, "w") as archive:
        archive.writestr("contract-nli/train.json", contenu)
        archive.writestr("contract-nli/test.json", contenu)


def test_test_ferme_et_lecture(tmp_path: Path) -> None:
    """Le test est refusé sans ouvrir_test=True ; le train est lu avec ses évidences."""
    chemin = tmp_path / "contract-nli.zip"
    fabriquer_zip(chemin)
    with pytest.raises(PermissionError):
        charger_contractnli(chemin, "test")
    documents, _ = charger_contractnli(chemin, "train")
    assert documents[0].evidences == {"nda-4": [0], "nda-18": [1]}


def test_nda18_exclue_et_projection(tmp_path: Path) -> None:
    """nda-18 (non-sollicitation) est exclue : seule la ligne de confidentialité est positive."""
    chemin = tmp_path / "contract-nli.zip"
    fabriquer_zip(chemin)
    document = charger_contractnli(chemin, "train")[0][0]
    annotations = annotations_confidentialite(document)
    assert annotations == [Annotation("nda-exemple.pdf", "nda-4", 0, 51)]
    segments = segmenter(document.titre, document.texte, coupe_aux_lignes=True)
    assert categories_par_segment(segments, annotations) == [["nda-4"], []]


def test_mots_cles_confidentialite() -> None:
    """Un mot-clé de confidentialité déclenche la famille ; une phrase neutre non."""
    assert predire_confidentialite([
        "The Receiving Party shall not disclose Confidential Information.",
        "The price of each unit is set out in Exhibit A.",
    ]).tolist() == [True, False]
