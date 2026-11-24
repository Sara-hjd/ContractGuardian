"""Tests d'intégration de la base de données (D-010).

Ignorés (« skip ») si psycopg n'est pas installé ou si la base ne répond pas
(``docker compose up -d`` non lancé). Le petit PDF est fabriqué ici ; il est supprimé de la base
à la fin du test.
"""

import uuid
from pathlib import Path

import pytest

from cg.stockage.connexion import lire_configuration

PHRASE = "In no event shall either party be liable for consequential damages."


@pytest.fixture
def connexion():
    """Connexion à la base, ou test ignoré si elle est indisponible."""
    psycopg = pytest.importorskip("psycopg")
    from cg.stockage.connexion import connecter

    try:
        c = connecter()
    except (KeyError, psycopg.OperationalError) as erreur:
        pytest.skip(f"Base indisponible : {erreur}")
    yield c
    c.close()


def test_lire_configuration_priorite_aux_variables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Le fichier .env est lu, et une variable d'environnement l'emporte."""
    env = tmp_path / ".env"
    env.write_text("# commentaire\nPOSTGRES_USER=fichier\nPOSTGRES_DB=base\n", encoding="utf-8")
    monkeypatch.setenv("POSTGRES_USER", "variable")
    configuration = lire_configuration(env)
    assert configuration["POSTGRES_USER"] == "variable"
    assert configuration["POSTGRES_DB"] == "base"


def test_extension_vector_active(connexion) -> None:
    """pgvector est bien installé dans la base."""
    with connexion.cursor() as curseur:
        curseur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        assert curseur.fetchone() is not None


def test_enregistrer_relire_et_tracer(connexion, tmp_path: Path) -> None:
    """Un PDF de 2 pages : enregistré, relu identique, traçable en SQL, puis supprimé."""
    pymupdf = pytest.importorskip("pymupdf")
    from cg.ingestion.pdf import extraire_pdf, segmenter_pdf
    from cg.stockage.depot import (
        compter_segments_non_tracables,
        enregistrer_document,
        lire_segments,
        supprimer_contrat,
    )

    chemin = tmp_path / "contrat.pdf"
    pdf = pymupdf.open()
    for texte in ("1. Term. This Agreement lasts two years.", PHRASE):
        pdf.new_page().insert_text((72, 72), texte)
    pdf.save(chemin)
    pdf.close()

    titre = f"test-{uuid.uuid4()}"  # titre unique : le test ne gêne aucune donnée existante
    document = extraire_pdf(chemin, titre, mode="blocs")
    segments = segmenter_pdf(document)
    contrat_id = enregistrer_document(connexion, document, segments, "import", "test", chemin)
    try:
        relus = lire_segments(connexion, contrat_id)
        assert [(s.debut, s.fin, s.texte, s.page) for s in relus] == [
            (s.debut, s.fin, s.texte, s.page) for s in segments
        ]
        assert compter_segments_non_tracables(connexion, contrat_id) == 0
    finally:
        supprimer_contrat(connexion, contrat_id)
    # Vérification par une AUTRE connexion : la suppression doit être réellement validée.
    from cg.stockage.connexion import connecter

    with connecter() as autre, autre.cursor() as curseur:
        curseur.execute("SELECT count(*) FROM segments WHERE contrat_id = %s", (contrat_id,))
        assert curseur.fetchone()[0] == 0  # la suppression en cascade a tout effacé


def test_titre_libre_evite_les_doublons(connexion) -> None:
    """Un titre déjà pris reçoit un suffixe « (import n) » (cas d'un même fichier importé deux fois)."""
    pytest.importorskip("fastapi")
    from cg.api.services import titre_libre

    titre = f"test-{uuid.uuid4()}"
    assert titre_libre(connexion, titre) == titre
    with connexion.transaction(), connexion.cursor() as c:
        c.execute("INSERT INTO contrats (titre, source, mode_extraction, texte_complet, nb_pages) "
                  "VALUES (%s, 'import', 'test', 'x', 0) RETURNING id", (titre,))
        cid = c.fetchone()[0]
    try:
        assert titre_libre(connexion, titre) == f"{titre} (import 2)"
    finally:
        with connexion.transaction(), connexion.cursor() as c:
            c.execute("DELETE FROM contrats WHERE id = %s", (cid,))
