"""Tests de l'extraction PDF et de l'alignement (F1, F7).

Les textes et le petit PDF sont fabriqués ici pour tester le code ; ils ne servent jamais à
entraîner un modèle (règle 3).
"""

from pathlib import Path

import pytest

from cg.ingestion.alignement import aligner, normaliser

PHRASE = "In no event shall either party be liable for consequential damages."


def test_normaliser_garde_le_lien_avec_l_origine() -> None:
    """Chaque caractère normalisé pointe vers le bon caractère du texte d'origine."""
    texte = "  Term:\n\n   two   years. "
    resultat = normaliser(texte)
    assert resultat.texte == "Term: two years."
    for i, c in enumerate(resultat.texte):
        assert c == " " and texte[resultat.origine[i]].isspace() or texte[resultat.origine[i]] == c


def test_aligner_malgre_les_sauts_de_ligne() -> None:
    """Le passage est retrouvé alors que la cible coupe la phrase par des sauts de ligne."""
    cible = "1. Liability.\nIn no event shall either\nparty be liable for consequential\n damages.\n"
    position = aligner(PHRASE, normaliser(cible))
    assert position is not None
    debut, fin = position
    assert " ".join(cible[debut:fin].split()) == PHRASE


def test_niveau_etendu_gere_casse_et_guillemets() -> None:
    """Majuscules et guillemets typographiques : seul le niveau étendu retrouve le passage."""
    passage = 'the "Effective Date"'
    cible = "This Agreement, THE “EFFECTIVE DATE”, starts today."
    assert aligner(passage, normaliser(cible, "espaces"), "espaces") is None
    position = aligner(passage, normaliser(cible, "etendue"), "etendue")
    assert position is not None
    assert cible[position[0]:position[1]] == "THE “EFFECTIVE DATE”"


def test_aligner_choisit_l_occurrence_la_plus_proche() -> None:
    """Deux occurrences identiques : on prend celle dont la place relative est la plus proche."""
    cible = "Term. " + "x" * 100 + " Term. " + "y" * 100
    premiere = aligner("Term.", normaliser(cible), position_relative=0.0)
    seconde = aligner("Term.", normaliser(cible), position_relative=0.5)
    assert premiere is not None and seconde is not None
    assert premiere[0] == 0
    assert seconde[0] == cible.index("Term.", 1)


def test_passage_absent() -> None:
    """Un passage absent renvoie None (on ne fabrique jamais de position)."""
    assert aligner("Governing law", normaliser("Nothing here.")) is None


def test_extraire_et_segmenter_un_pdf(tmp_path: Path) -> None:
    """Un PDF de 2 pages : chaque segment est traçable et sur la bonne page."""
    pymupdf = pytest.importorskip("pymupdf")
    from cg.ingestion.pdf import extraire_pdf, segmenter_pdf

    chemin = tmp_path / "contrat.pdf"
    document = pymupdf.open()
    for texte in ("1. Term. This Agreement lasts two years.", PHRASE):
        page = document.new_page()
        page.insert_text((72, 72), texte)
    document.save(chemin)
    document.close()

    extrait = extraire_pdf(chemin, "contrat")
    assert [p.numero for p in extrait.pages] == [1, 2]
    segments = segmenter_pdf(extrait)
    assert [s.page for s in segments] == [1, 2]
    for s in segments:
        assert extrait.texte[s.debut:s.fin] == s.texte
        page = extrait.pages[s.page - 1]
        assert page.debut <= s.debut and s.fin <= page.fin
    assert "liable" in segments[1].texte


def test_trouver_pdf_tolere_les_differences_de_nom(tmp_path: Path) -> None:
    """Espace final, tiret final, suffixe ajouté : le bon fichier est retrouvé."""
    pytest.importorskip("pymupdf")
    from cg.ingestion.pdf import trouver_pdf

    for nom in ("Alpha Agreement .pdf", "Beta Agreement-.PDF", "Gamma Agreement_Option.pdf"):
        (tmp_path / nom).write_bytes(b"%PDF-1.4")
    assert trouver_pdf(tmp_path, "Alpha Agreement").name == "Alpha Agreement .pdf"
    assert trouver_pdf(tmp_path, "Beta Agreement").name == "Beta Agreement-.PDF"
    assert trouver_pdf(tmp_path, "Gamma Agreement").name == "Gamma Agreement_Option.pdf"
    with pytest.raises(FileNotFoundError):
        trouver_pdf(tmp_path, "Delta Agreement")
