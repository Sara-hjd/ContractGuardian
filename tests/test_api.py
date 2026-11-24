"""Tests de l'API (F6) avec de faux services : pas de base, pas de modèle."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from cg.api import app as module  # noqa: E402


class FauxServices:
    """Remplace la logique de l'application : réponses fixes, sans base ni modèle."""

    def lister_contrats(self, c):
        return [{"id": 1, "titre": "contrat-exemple", "nb_pages": 3, "importe_le": "2026-11-24T10:00:00"}]

    def contrat(self, c, contrat_id):
        return {"id": 1, "titre": "contrat-exemple", "nb_pages": 3, "importe_le": "x"} if contrat_id == 1 else None

    def clauses(self, c, contrat_id):
        return [{"famille": "durée", "score": 0.9, "modele": "m", "segment_id": 10, "page": 2,
                 "debut": 100, "fin": 140, "citation": "The term is two years."}]

    def repondre(self, c, contrat_id, question, mode):
        return {"abstention": True, "raison": "le LLM s'abstient", "citations": []}


@pytest.fixture
def client():
    module.app.dependency_overrides[module.services] = lambda: FauxServices()
    module.app.dependency_overrides[module.connexion] = lambda: None
    yield TestClient(module.app)
    module.app.dependency_overrides.clear()


def test_liste_et_avertissement(client) -> None:
    r = client.get("/contrats")
    assert r.status_code == 200
    assert r.json()["contrats"][0]["titre"] == "contrat-exemple"
    assert "avis juridique" in r.json()["avertissement"]


def test_clauses_avec_provenance_et_404(client) -> None:
    r = client.get("/contrats/1/clauses").json()
    clause = r["clauses"][0]
    assert (clause["page"], clause["debut"], clause["fin"]) == (2, 100, 140)
    assert client.get("/contrats/999/clauses").status_code == 404


def test_import_refuse_un_fichier_non_pdf(client) -> None:
    r = client.post("/contrats", files={"fichier": ("notes.txt", b"bonjour", "text/plain")})
    assert r.status_code == 400


def test_question_validee_et_abstention(client) -> None:
    assert client.post("/contrats/1/questions", json={"question": "Term?", "mode": "devine"}).status_code == 422
    r = client.post("/contrats/1/questions", json={"question": "What is the governing law?"}).json()
    assert r["abstention"] is True and r["citations"] == []
