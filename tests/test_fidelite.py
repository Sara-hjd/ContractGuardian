"""Tests du contrôle des éléments critiques (fidélité, D-026) sur des phrases inventées."""

from cg.recherche.fidelite import controler, elements_critiques


def test_nombres_en_chiffres_et_en_lettres() -> None:
    assert elements_critiques("thirty (30) days") == {"30"}
    assert elements_critiques("twenty-four months") == {"24"}
    assert elements_critiques("$1,000,000 or two hundred thousand dollars") == {"1000000", "200000"}
    assert elements_critiques("a 2.5% fee") == {"2.5"}


def test_mai_verbe_ou_mois() -> None:
    assert elements_critiques("Either party may terminate.") == set()
    assert elements_critiques("on May 1, 2020") == {"mois:may", "1", "2020"}
    assert "mois:june" in elements_critiques("until June 30")


def test_controler() -> None:
    passage = "Either party may terminate this Agreement upon thirty (30) days prior written notice."
    assert controler("Termination requires 30 days notice.", [passage]).fidele
    invente = controler("Termination requires 60 days notice.", [passage])
    assert not invente.fidele and invente.absents == {"60"}
    assert controler("Either party may terminate.", [passage]).fidele  # aucun élément critique
