"""Tests des fichiers de splits (D-004, D-005).

Les fichiers de ``data/splits/`` sont commités dans un dépôt public : ils ne doivent contenir
que des titres de contrats et les paramètres du tirage, jamais de texte (règle absolue 5).
"""

import json
from pathlib import Path

from cg.datasets.splits import JEUX

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_SPLITS = RACINE / "data" / "splits"
CHEMIN_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1" / "CUAD_v1.json"

CLES_AUTORISEES = {
    "description", "source_test", "graine_validation", "proportion_validation", "cree_le", *JEUX,
}
# Le plus long titre CUAD fait 161 caractères ; une chaîne bien plus longue
# serait probablement un extrait de contrat.
LONGUEUR_MAX_TITRE = 300


def _fichiers_splits() -> list[Path]:
    """Liste les fichiers JSON de ``data/splits/``."""
    return sorted(DOSSIER_SPLITS.glob("*.json"))


def test_splits_ne_contiennent_que_des_titres() -> None:
    """Uniquement les clés prévues, et des listes de titres courts, sans doublon entre jeux."""
    fichiers = _fichiers_splits()
    assert fichiers, "Aucun fichier dans data/splits/"
    for chemin in fichiers:
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
        assert set(contenu) <= CLES_AUTORISEES, f"{chemin.name} : clés inattendues"
        vus: set[str] = set()
        for jeu in JEUX:
            for titre in contenu[jeu]:
                assert isinstance(titre, str) and len(titre) <= LONGUEUR_MAX_TITRE
                assert "\n" not in titre, f"{chemin.name} : saut de ligne dans un titre"
                assert titre not in vus, f"{chemin.name} : contrat dans deux jeux : {titre}"
                vus.add(titre)


def test_splits_couvrent_les_510_contrats_cuad() -> None:
    """Chaque titre existe dans CUAD, et les jeux couvrent les 510 contrats (si CUAD est présent)."""
    if not CHEMIN_CUAD.exists():
        import pytest

        pytest.skip("CUAD absent de cette machine.")

    with open(CHEMIN_CUAD, encoding="utf-8") as fichier:
        titres_cuad = {contrat["title"] for contrat in json.load(fichier)["data"]}
    contenu = json.loads((DOSSIER_SPLITS / "cuad_v1_splits.json").read_text(encoding="utf-8"))
    titres_splits = {titre for jeu in JEUX for titre in contenu[jeu]}
    assert titres_splits == titres_cuad
