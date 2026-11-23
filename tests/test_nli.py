"""Tests de F4 (NLI) : paires, décision au niveau du document, métriques.

Les documents et le petit modèle sont fabriqués ici pour tester le code ; ils ne servent jamais
à entraîner un modèle du projet (règle 3).
"""

import numpy as np
import pytest

from cg.datasets.contractnli import DocumentNli
from cg.nli.evaluation import metriques_etiquettes, metriques_evidences
from cg.nli.modele import decider
from cg.nli.paires import INDICE, paires_document, paires_entrainement

TEXTE = "Recipient shall not disclose. Recipient may share with employees. Governing law is Delaware."
DOCUMENT = DocumentNli(
    identifiant=1, titre="nda.pdf", texte=TEXTE, spans=[(0, 29), (30, 65), (66, 93)],
    choix={"nda-5": "Entailment", "nda-11": "NotMentioned", "nda-4": "Entailment"},
    evidences={"nda-5": [1], "nda-11": [], "nda-4": [0]},
)
HYPOTHESES = {"nda-5": "Receiving Party may share some Confidential Information with employees.",
              "nda-11": "Receiving Party shall not reverse engineer."}


def test_paires_entrainement_evidences_et_neutres() -> None:
    """Évidence = étiquette du document ; neutres = phrases non-évidence, dont une « difficile »."""
    paires = paires_entrainement([DOCUMENT], HYPOTHESES, graine=0)
    evidence = [p for p in paires if p.hypothese == "nda-5" and p.etiquette == INDICE["Entailment"]]
    assert [p.indice_span for p in evidence] == [1]
    assert evidence[0].texte_span == "Recipient may share with employees."
    neutres_nda11 = [p for p in paires if p.hypothese == "nda-11"]
    assert all(p.etiquette == INDICE["NotMentioned"] for p in neutres_nda11)
    # La phrase 0 est évidence d'une autre hypothèse (nda-4) : c'est la seule « difficile » possible.
    assert 0 in {p.indice_span for p in neutres_nda11}


def test_paires_document_couvrent_toutes_les_phrases() -> None:
    """Une paire par phrase, chacune traçable vers le texte."""
    paires = paires_document(DOCUMENT, "nda-5", HYPOTHESES["nda-5"])
    assert [p.etiquette for p in paires] == [0, INDICE["Entailment"], 0]
    for p in paires:
        debut, fin = DOCUMENT.spans[p.indice_span]
        assert TEXTE[debut:fin] == p.texte_span


def test_decider_abstention_et_evidences() -> None:
    """Sous le seuil : NotMentioned sans évidence ; au-dessus : classe et phrases citées."""
    probas = np.array([[0.9, 0.05, 0.05], [0.2, 0.75, 0.05], [0.3, 0.6, 0.1]])
    assert decider(probas, seuil_document=0.8, seuil_evidence=0.5).etiquette == "NotMentioned"
    decision = decider(probas, seuil_document=0.7, seuil_evidence=0.55)
    assert decision.etiquette == "Entailment"
    assert decision.evidences == (1, 2)


def test_metriques() -> None:
    """Valeurs calculées à la main."""
    m = metriques_etiquettes(["Entailment", "NotMentioned", "Contradiction", "Entailment"],
                             ["Entailment", "NotMentioned", "Entailment", "Entailment"])
    assert m["exactitude"] == pytest.approx(0.75)
    assert m["f1_Contradiction"] == 0.0
    e = metriques_evidences([{1, 2}, {0}], [{1}, {0, 3}])
    assert (e["precision"], e["rappel"]) == (pytest.approx(2 / 3), pytest.approx(2 / 3))
