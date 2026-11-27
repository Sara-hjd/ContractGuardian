"""Les fichiers de ``data/annotations/`` ne contiennent jamais de texte de contrat (règle 5, D-003).

Et le kappa de Cohen est correct (comparé à scikit-learn).
"""

import csv
from pathlib import Path

import pytest

from cg.annotation.accord import ETIQUETTES_F3, ETIQUETTES_F5, kappa_cohen

RACINE = Path(__file__).resolve().parents[1]
DOSSIER = RACINE / "data" / "annotations"

# Colonnes autorisées par type de fichier ; aucune colonne de texte libre sauf « question » (F5),
# écrite par les annotateurs avec leurs mots et limitée en longueur.
COLONNES = {
    "f3_paires/paires_v1.csv": {"id_paire", "type", "titre", "page_a", "debut_a", "fin_a", "categories_a",
                                "page_b", "debut_b", "fin_b", "categories_b"},
    "f3_paires/": {"id_paire", "annotateur", "etiquette", "date"},
    "f5_questions/": {"id_question", "titre", "question", "avec_reponse", "page", "debut", "fin", "auteur", "date"},
    # Fidélité des réponses du RAG (D-026) : identifiants seulement, jamais la réponse ni les passages.
    "f5_fidelite/reponses_v1.csv": {"id_reponse", "configuration", "titre", "categorie", "segments_cites"},
    "f5_fidelite/": {"id_reponse", "annotateur", "etiquette", "date"},
}
LONGUEUR_MAX = {"question": 300, "titre": 200, "categories_a": 200, "categories_b": 200, "configuration": 80,
                "categorie": 60, "segments_cites": 80}


def _colonnes_attendues(chemin: Path) -> set[str]:
    relatif = chemin.relative_to(DOSSIER).as_posix()
    if relatif in COLONNES:
        return COLONNES[relatif]
    for prefixe, colonnes in COLONNES.items():
        if prefixe.endswith("/") and relatif.startswith(prefixe):
            return colonnes
    raise AssertionError(f"Fichier d'annotation inattendu : {relatif}")


@pytest.mark.parametrize("chemin", sorted(DOSSIER.rglob("*.csv")), ids=lambda p: p.name)
def test_annotations_sans_texte_de_contrat(chemin: Path) -> None:
    """Seulement les colonnes prévues ; valeurs courtes ; étiquettes F3 dans la grille."""
    with open(chemin, encoding="utf-8", newline="") as f:
        lecteur = csv.DictReader(f)
        assert set(lecteur.fieldnames or []) == _colonnes_attendues(chemin), chemin.name
        for ligne in lecteur:
            for cle, valeur in ligne.items():
                assert len(valeur or "") <= LONGUEUR_MAX.get(cle, 40), f"{chemin.name} : {cle} trop long"
            if "etiquette" in ligne:
                grille = ETIQUETTES_F5 if "f5_fidelite" in chemin.as_posix() else ETIQUETTES_F3
                assert ligne["etiquette"] in grille, f"{chemin.name} : étiquette hors grille"


def test_kappa_valeurs_connues() -> None:
    """Accord parfait → 1 ; exemple calculé à la main ; même résultat que scikit-learn."""
    a = ["A", "A", "B", "B", "C", "A"]
    assert kappa_cohen(a, a) == 1.0
    b = ["A", "B", "B", "B", "C", "A"]
    # p_o = 5/6 ; p_e = (3·2 + 2·3 + 1·1) / 36 = 13/36 ; κ = (5/6 − 13/36) / (1 − 13/36) = 17/23
    assert kappa_cohen(a, b) == pytest.approx(17 / 23)
    metrics = pytest.importorskip("sklearn.metrics")
    assert kappa_cohen(a, b) == pytest.approx(metrics.cohen_kappa_score(a, b))


def test_regle_alertes_v1() -> None:
    """Délais convertis en jours ; R2 si délais différents ; R3 sur une exception ; R1 au-delà du seuil."""
    from cg.comparison.alertes import decider_alerte, delais

    assert delais("upon thirty (30) days notice and after two (2) years") == {30, 730}
    a = "Either party may terminate upon thirty (30) days prior written notice."
    b = "This Agreement may be terminated upon sixty (60) days notice."
    assert decider_alerte(a, b, 0.1).raisons == ("R2",)
    assert decider_alerte(a, a, 0.1).alerte is False
    assert decider_alerte(a, "Notwithstanding the foregoing, no termination.", 0.7).raisons == ("R1", "R3")
