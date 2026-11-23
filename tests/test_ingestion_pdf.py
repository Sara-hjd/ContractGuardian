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


def test_mode_blocs_coupe_a_chaque_paragraphe(tmp_path: Path) -> None:
    """Deux paragraphes éloignés sur une même page : deux blocs, donc deux segments traçables."""
    pymupdf = pytest.importorskip("pymupdf")
    from cg.ingestion.pdf import extraire_pdf, segmenter_pdf

    chemin = tmp_path / "contrat.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "1. Term. This Agreement lasts two years.")
    page.insert_text((72, 400), PHRASE)
    document.save(chemin)
    document.close()

    for mode, attendu in (("blocs", 2), ("texte", 1)):
        extrait = extraire_pdf(chemin, "contrat", mode)
        segments = segmenter_pdf(extrait)
        assert len(segments) == attendu, mode
        for s in segments:
            assert s.page == 1
            assert extrait.texte[s.debut:s.fin] == s.texte


def test_fusionner_fragments() -> None:
    """Un fragment court rejoint le suivant (même page) ; jamais à travers deux pages."""
    from cg.ingestion.segmentation import Segment, fusionner_fragments

    texte = "12.\n\nLiability is capped at fees paid.\n\n3\n\nNext page text here."
    def seg(mot: str, page: int) -> Segment:
        d = texte.index(mot)
        return Segment("t", d, d + len(mot), mot, page)
    segments = [seg("12.", 1), seg("Liability is capped at fees paid.", 1), seg("3", 1),
                seg("Next page text here.", 2)]

    fusionnes = fusionner_fragments(texte, segments, seuil=5)
    assert [s.texte for s in fusionnes] == [
        "12.\n\nLiability is capped at fees paid.", "3", "Next page text here."]
    for s in fusionnes:
        assert texte[s.debut:s.fin] == s.texte
    assert fusionner_fragments(texte, segments, seuil=0) == segments  # seuil 0 : aucune fusion


def test_segmenter_coupe_aux_lignes() -> None:
    """Texte sans ligne vide : la v1 garde un bloc, l'option coupe_aux_lignes donne un segment par ligne."""
    from cg.ingestion.segmentation import segmenter

    texte = "1. Definitions. Confidential Information means...\n2. Use. Recipient shall not disclose.\n"
    assert len(segmenter("t", texte)) == 1
    segments = segmenter("t", texte, coupe_aux_lignes=True)
    assert [s.texte[:2] for s in segments] == ["1.", "2."]
    for s in segments:
        assert texte[s.debut:s.fin] == s.texte
