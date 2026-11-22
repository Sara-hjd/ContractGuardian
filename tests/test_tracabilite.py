"""Tests de traçabilité des segments (règle absolue 1, F7).

Vérifie que chaque segment pointe exactement vers son texte source :
``texte_du_contrat[debut:fin] == texte_du_segment``.

- Les tests unitaires utilisent un petit texte écrit à la main : il sert uniquement à tester
  le code, jamais à entraîner un modèle (la règle 3 porte sur l'entraînement).
- Le test sur les données réelles lit ``data/processed/cuad_segments_v1.jsonl`` ; il est
  ignoré (« skip ») si ce fichier ou CUAD sont absents de la machine.

Lancement : ``.venv/bin/python -m pytest tests/`` (pytest à installer, avec l'accord de Sara).
"""

import json
from pathlib import Path

from cg.datasets.cuad import Annotation, projeter_annotations
from cg.ingestion.segmentation import segmenter

RACINE = Path(__file__).resolve().parents[1]
CHEMIN_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1" / "CUAD_v1.json"
CHEMIN_SEGMENTS = RACINE / "data" / "processed" / "cuad_segments_v1.jsonl"

TEXTE_EXEMPLE = (
    "EXHIBIT 10.1\n\n   \n"
    "1. Term. This Agreement starts on the Effective Date.\n"
    "It lasts two years.\n\n"
    "2. Liability. Liability is capped at fees paid.   \n"
)


def test_positions_exactes_sur_un_exemple() -> None:
    """Chaque segment de l'exemple se retrouve exactement dans le texte source."""
    segments = segmenter("exemple", TEXTE_EXEMPLE)
    assert [s.texte for s in segments] == [
        "EXHIBIT 10.1",
        "1. Term. This Agreement starts on the Effective Date.\nIt lasts two years.",
        "2. Liability. Liability is capped at fees paid.",
    ]
    for s in segments:
        assert TEXTE_EXEMPLE[s.debut:s.fin] == s.texte


def test_plafond_et_positions_sur_un_bloc_long() -> None:
    """Un bloc trop long est recoupé sous le plafond, sans perdre la traçabilité."""
    texte = "\n".join(f"Line {i} of a long clause without blank lines." for i in range(200))
    segments = segmenter("long", texte, maximum=300)
    assert len(segments) > 1
    for s in segments:
        assert len(s.texte) <= 300
        assert texte[s.debut:s.fin] == s.texte


def test_regle_de_chevauchement() -> None:
    """Date courte : comptée si entière. Clause longue : il faut au moins 20 caractères."""
    segments = segmenter("exemple", TEXTE_EXEMPLE)
    debut_date = TEXTE_EXEMPLE.index("Effective Date")
    debut_plafond = TEXTE_EXEMPLE.index("Liability is capped")
    annotations = [
        Annotation("exemple", "Effective Date", debut_date, debut_date + len("Effective Date")),
        # Clause qui commence 14 caractères avant la fin du segment « Term » (moins de 20) :
        # elle étiquette le segment « Liability » (34 caractères communs), pas « Term ».
        Annotation("exemple", "Cap On Liability", debut_plafond - 30, debut_plafond + 20),
    ]
    etiquetes = projeter_annotations(segments, annotations)
    assert etiquetes[1].familles == ["durée"]  # « Term » : la date seulement
    assert etiquetes[2].categories == ["Cap On Liability"]
    assert etiquetes[0].familles == []


def test_tracabilite_de_tous_les_segments_cuad() -> None:
    """Pour TOUS les segments produits : texte_du_contrat[debut:fin] == texte_du_segment."""
    if not (CHEMIN_SEGMENTS.exists() and CHEMIN_CUAD.exists()):
        import pytest  # importé ici pour que les autres tests restent lançables sans pytest

        pytest.skip("Données locales absentes : lancer cg.datasets.preparer_segments d'abord.")

    from cg.datasets.cuad import charger_cuad

    textes, _ = charger_cuad(CHEMIN_CUAD)
    erreurs: list[str] = []
    nb_segments = 0
    with open(CHEMIN_SEGMENTS, encoding="utf-8") as fichier:
        for ligne in fichier:
            segment = json.loads(ligne)
            nb_segments += 1
            if textes[segment["titre"]][segment["debut"]:segment["fin"]] != segment["texte"]:
                erreurs.append(f"{segment['titre']} [{segment['debut']}:{segment['fin']}]")
    assert nb_segments > 0
    assert not erreurs, f"{len(erreurs)} segment(s) non traçable(s), par ex. {erreurs[:3]}"
