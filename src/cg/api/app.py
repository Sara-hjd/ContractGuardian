"""API FastAPI de ContractGuardian (F6).

Lancement, depuis la racine du projet, avec le .venv, la base démarrée et Ollama lancé :

    PYTHONPATH=src .venv/bin/python -m uvicorn cg.api.app:app --port 8000

Documentation interactive : http://127.0.0.1:8000/docs. Chaque réponse contient un
``avertissement`` (pas d'avis juridique) ; chaque citation porte sa page et ses positions.
"""

from collections.abc import Iterator

import psycopg
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from cg import config
from cg.api.services import AVERTISSEMENT, Services
from cg.stockage.connexion import connecter

app = FastAPI(title="ContractGuardian", version="0.1.0",
              description="Aide à la lecture de contrats commerciaux en anglais. " + AVERTISSEMENT)
# L'interface React tourne en développement sur le port 5173.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
_services = Services()


def services() -> Services:
    """Services partagés (remplaçables dans les tests)."""
    return _services


def connexion() -> Iterator[psycopg.Connection]:
    """Une connexion à la base par requête."""
    with connecter() as c:
        yield c


def _contrat_ou_404(s: Services, c: psycopg.Connection, contrat_id: int) -> dict:
    contrat = s.contrat(c, contrat_id)
    if contrat is None:
        raise HTTPException(status_code=404, detail="Contrat introuvable.")
    return contrat


class Question(BaseModel):
    """Question posée sur un contrat."""

    question: str = Field(min_length=3, max_length=500)
    mode: str = Field(default="rag", pattern="^(rag|extractif)$")


class Hypothese(BaseModel):
    """Hypothèse à confronter au contrat (F4)."""

    hypothese: str = Field(min_length=3, max_length=500)


@app.get("/sante")
def sante(c: psycopg.Connection = Depends(connexion)) -> dict:
    """État de l'application : base joignable, modèle de langage configuré."""
    with c.cursor() as cur:
        cur.execute("SELECT 1")
    return {"statut": "ok", "llm": config.LLM_MODELE, "avertissement": AVERTISSEMENT}


@app.get("/contrats")
def contrats(s: Services = Depends(services), c: psycopg.Connection = Depends(connexion)) -> dict:
    """Contrats importés."""
    return {"contrats": s.lister_contrats(c), "avertissement": AVERTISSEMENT}


@app.post("/contrats")
async def importer(fichier: UploadFile = File(...), s: Services = Depends(services),
                   c: psycopg.Connection = Depends(connexion)) -> dict:
    """Importe un contrat PDF : extraction, segments avec pages, vecteurs, clauses (F1, F2, F5)."""
    if not (fichier.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés.")
    resume = s.importer_pdf(c, await fichier.read(), fichier.filename)
    return {**resume, "avertissement": AVERTISSEMENT}


@app.get("/contrats/{contrat_id}/clauses")
def clauses(contrat_id: int, s: Services = Depends(services), c: psycopg.Connection = Depends(connexion)) -> dict:
    """Clauses détectées (F2), chacune avec sa citation exacte, sa page et ses positions."""
    contrat = _contrat_ou_404(s, c, contrat_id)
    return {"contrat": contrat, "clauses": s.clauses(c, contrat_id), "avertissement": AVERTISSEMENT}


@app.post("/contrats/{contrat_id}/questions")
def questions(contrat_id: int, q: Question, s: Services = Depends(services),
              c: psycopg.Connection = Depends(connexion)) -> dict:
    """Réponse citant exactement le contrat, ou abstention (F5)."""
    _contrat_ou_404(s, c, contrat_id)
    return {**s.repondre(c, contrat_id, q.question, q.mode), "avertissement": AVERTISSEMENT}


@app.get("/contrats/{contrat_id}/alertes")
def alertes(contrat_id: int, s: Services = Depends(services), c: psycopg.Connection = Depends(connexion)) -> dict:
    """Points à vérifier entre clauses (F3) — **expérimental** (D-018)."""
    _contrat_ou_404(s, c, contrat_id)
    return {"experimental": True, "alertes": s.alertes(c, contrat_id),
            "note": "Fonctionnalité expérimentale : la règle v1 signale beaucoup de paires ; "
                    "chaque alerte est un point à relire, jamais une contradiction établie.",
            "avertissement": AVERTISSEMENT}


@app.post("/contrats/{contrat_id}/nli")
def nli(contrat_id: int, h: Hypothese, s: Services = Depends(services), c: psycopg.Connection = Depends(connexion)) -> dict:
    """Le contrat implique-t-il, contredit-il ou ignore-t-il l'hypothèse ? (F4, conçu pour les NDA)."""
    _contrat_ou_404(s, c, contrat_id)
    return {**s.nli_hypothese(c, contrat_id, h.hypothese),
            "note": "Modèle entraîné sur des accords de confidentialité (ContractNLI).",
            "avertissement": AVERTISSEMENT}
