"""Tests des baselines d'extraction (F2) et de la protection du jeu de test (règle 2).

Les phrases ci-dessous sont écrites à la main pour tester le code ; elles ne servent jamais
à entraîner un modèle du projet (règle 3).
"""

import json
from pathlib import Path

import numpy as np
import pytest

from cg.datasets.segments import charger_segments
from cg.extraction.metriques import choisir_seuil, metriques_binaires, tableau_metriques
from cg.extraction.mots_cles import predire_mots_cles
from cg.extraction.tfidf import creer_vectoriseur, entrainer_classifieur, mots_les_plus_lourds


def test_mots_cles_par_famille() -> None:
    """Chaque phrase déclenche la famille attendue, et une phrase neutre n'en déclenche aucune."""
    textes = [
        "This Agreement is made on the 8th day of May, 2014.",
        "Either party may terminate this Agreement without cause upon 30 days notice.",
        "In no event shall either party be liable for consequential damages.",
        "The price of each unit is set out in Exhibit A.",
    ]
    pred = predire_mots_cles(textes)
    assert pred["durée"].tolist() == [True, False, False, False]
    assert pred["résiliation"].tolist() == [False, True, False, False]
    assert pred["responsabilité"].tolist() == [False, False, True, False]


def test_metriques_binaires_valeurs_connues() -> None:
    """Exemple calculé à la main : 2 VP, 1 FP, 1 FN → P = 2/3, R = 2/3, F1 = 2/3."""
    y_vrai = np.array([1, 1, 1, 0, 0], dtype=bool)
    y_pred = np.array([1, 1, 0, 1, 0], dtype=bool)
    m = metriques_binaires(y_vrai, y_pred)
    assert (m["vp"], m["fp"], m["fn"], m["support"]) == (2, 1, 1, 3)
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["rappel"] == pytest.approx(2 / 3)
    assert m["f1"] == pytest.approx(2 / 3)


def test_modele_qui_ne_trouve_rien() -> None:
    """97 % d'exactitude mais F1 nul : la raison pour laquelle on ignore l'exactitude."""
    y_vrai = np.array([True] * 3 + [False] * 97)
    y_pred = np.zeros(100, dtype=bool)
    assert (y_vrai == y_pred).mean() == pytest.approx(0.97)
    assert metriques_binaires(y_vrai, y_pred)["f1"] == 0.0


def test_macro_f1_est_la_moyenne_des_familles() -> None:
    """La ligne macro est la moyenne simple des F1 des familles."""
    y_vrai = {"a": np.array([1, 0], dtype=bool), "b": np.array([1, 0], dtype=bool)}
    y_pred = {"a": np.array([1, 0], dtype=bool), "b": np.array([0, 0], dtype=bool)}
    tableau = tableau_metriques(y_vrai, y_pred)
    assert tableau.loc["macro", "f1"] == pytest.approx(0.5)


def test_choisir_seuil() -> None:
    """Le seuil retenu sépare parfaitement cet exemple simple."""
    y_vrai = np.array([0, 0, 1, 1], dtype=bool)
    probas = np.array([0.1, 0.3, 0.35, 0.9])
    seuil, f1 = choisir_seuil(y_vrai, probas)
    assert 0.3 < seuil <= 0.35
    assert f1 == pytest.approx(1.0)


def test_le_jeu_de_test_est_ferme(tmp_path: Path) -> None:
    """charger_segments refuse le test sans ouvrir_test=True, et ne lit que les jeux demandés."""
    chemin = tmp_path / "segments.jsonl"
    lignes = [
        {"titre": "a", "jeu": "train", "debut": 0, "fin": 1, "texte": "x", "categories": [], "familles": []},
        {"titre": "b", "jeu": "test", "debut": 0, "fin": 1, "texte": "y", "categories": [], "familles": []},
    ]
    chemin.write_text("\n".join(json.dumps(l) for l in lignes) + "\n", encoding="utf-8")
    with pytest.raises(PermissionError):
        charger_segments(chemin, {"train", "test"})
    df = charger_segments(chemin, {"train"})
    assert df["titre"].tolist() == ["a"]


def test_tfidf_apprend_sur_un_mini_corpus() -> None:
    """Sur un corpus jouet, le classifieur sépare les deux classes et « liable » pèse lourd."""
    textes = ["party shall be liable", "liable for damages", "price of units", "delivery of goods"] * 5
    y = np.array([True, True, False, False] * 5)
    vectoriseur = creer_vectoriseur(ngram_max=1, min_df=1)
    X = vectoriseur.fit_transform(textes)
    classifieur = entrainer_classifieur(X, y, C=10.0)
    assert (classifieur.predict_proba(X)[:, 1] >= 0.5).tolist() == y.tolist()
    assert "liable" in [mot for mot, _ in mots_les_plus_lourds(vectoriseur, classifieur, n=3)]
