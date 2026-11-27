"""Tests du choix du seuil d'abstention du RAG (D-025), sur un petit exemple inventé (aucune donnée)."""

import importlib.util
from pathlib import Path

import pandas as pd

_chemin = Path(__file__).resolve().parents[1] / "evaluation" / "regler_seuil_abstention_rag.py"
_spec = importlib.util.spec_from_file_location("regler_seuil", _chemin)
regler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(regler)


def _ligne(avec: bool, abstention: bool, juste: bool, p: float | None) -> dict:
    return {"avec_reponse": avec, "abstention": abstention, "juste": juste, "p_nli": p}


LIGNES = [
    _ligne(True, False, True, 0.9),    # bonne réponse, très « impliquée »
    _ligne(True, False, False, 0.2),   # réponse fausse, peu « impliquée »
    _ligne(False, False, False, 0.6),  # répond alors qu'il n'y a pas de réponse
    _ligne(False, True, False, None),  # bonne abstention
]


def test_mesurer() -> None:
    sans = regler.mesurer(LIGNES, None)
    assert sans["couverture"] == 0.75 and round(sans["erreur"], 3) == 0.667
    m = regler.mesurer(LIGNES, 0.7)  # seule la bonne réponse reste
    assert m["couverture"] == 0.25 and m["erreur"] == 0.0
    assert m["exactitude equilibree"] == (0.5 + 1.0) / 2


def test_choisir_criteres() -> None:
    tableau = pd.DataFrame([{"seuil": s, **regler.mesurer(LIGNES, s)} for s in regler.SEUILS])
    # A : exactitude équilibrée maximale (0,75 de 0,65 à 0,90) ; égalité → seuil le plus élevé.
    assert regler.choisir(tableau, "A") == 0.9
    # B : seuil le plus bas dont l'erreur ≤ 30 % (0,65 : il ne reste que la bonne réponse).
    assert regler.choisir(tableau, "B") == 0.65
