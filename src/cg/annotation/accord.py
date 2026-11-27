"""Accord entre deux annotateurs : kappa de Cohen (F3 et fidélité de F5, cahier des charges).

Place dans le projet : avant d'évaluer les alertes de F3 (ou la fidélité des réponses de F5, D-026)
sur les annotations de Sara et d'Ilyas, on mesure si les deux annotateurs sont d'accord. Si ce n'est
pas le cas, la grille est trop floue.

**Kappa de Cohen** : ``κ = (p_o − p_e) / (1 − p_e)``, où ``p_o`` est la part de paires où les deux
annotateurs ont mis la même étiquette, et ``p_e`` la part attendue **par hasard** (si chacun
étiquetait au hasard avec ses propres fréquences). κ = 1 : accord parfait ; κ = 0 : pas mieux que le
hasard. Repères usuels (Landis et Koch) : 0,41–0,60 modéré, 0,61–0,80 substantiel, > 0,80 presque parfait.

Lancement :

    PYTHONPATH=src .venv/bin/python -m cg.annotation.accord FICHIER_1.csv FICHIER_2.csv [--grille f5]
"""

import argparse
import csv
from collections import Counter
from pathlib import Path

# Les trois étiquettes de F3 imposées par le cahier des charges (D-020).
ETIQUETTES_F3: tuple[str, ...] = ("POTENTIELLEMENT_INCOMPATIBLE", "COMPATIBLE", "INFORMATION_INSUFFISANTE")
# Une paire « mérite une alerte » si elle est potentiellement incompatible.
ALERTE: frozenset[str] = frozenset({"POTENTIELLEMENT_INCOMPATIBLE"})

# Fidélité des réponses du RAG (D-026) ; « fidèle oui / non » = FIDELE contre le reste.
ETIQUETTES_F5: tuple[str, ...] = ("FIDELE", "PARTIELLEMENT_FIDELE", "NON_FIDELE")
FIDELE: frozenset[str] = frozenset({"FIDELE"})

# Grille -> (étiquettes, étiquettes « positives » du kappa binaire, nom du binaire, colonne identifiant).
GRILLES: dict[str, tuple[tuple[str, ...], frozenset[str], str, str]] = {
    "f3": (ETIQUETTES_F3, ALERTE, "alerte oui / non", "id_paire"),
    "f5": (ETIQUETTES_F5, FIDELE, "fidèle oui / non", "id_reponse"),
}


def kappa_cohen(etiquettes_1: list[str], etiquettes_2: list[str]) -> float:
    """Kappa de Cohen entre deux suites d'étiquettes (mêmes éléments, même ordre).

    Args:
        etiquettes_1: Étiquettes du premier annotateur.
        etiquettes_2: Étiquettes du second, pour les mêmes éléments.

    Returns:
        Le kappa (1 si les deux annotateurs n'emploient qu'une seule et même étiquette).

    Raises:
        ValueError: Si les deux listes n'ont pas la même longueur ou sont vides.
    """
    if len(etiquettes_1) != len(etiquettes_2) or not etiquettes_1:
        raise ValueError("Il faut deux listes non vides de même longueur.")
    n = len(etiquettes_1)
    p_o = sum(a == b for a, b in zip(etiquettes_1, etiquettes_2)) / n
    f1, f2 = Counter(etiquettes_1), Counter(etiquettes_2)
    p_e = sum(f1[e] * f2[e] for e in set(f1) | set(f2)) / (n * n)
    return 1.0 if p_e == 1 else (p_o - p_e) / (1 - p_e)


def lire_annotations(chemin: Path, grille: str = "f3") -> dict[str, str]:
    """Lit un fichier d'annotations (``id_paire`` ou ``id_reponse``, ``annotateur``, ``etiquette``, ``date``).

    Args:
        chemin: Fichier CSV d'un annotateur.
        grille: ``"f3"`` (paires de clauses) ou ``"f5"`` (fidélité des réponses, D-026).

    Returns:
        ``identifiant -> étiquette``.

    Raises:
        ValueError: Si une étiquette n'appartient pas à la grille.
    """
    with open(chemin, encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f))
    etiquettes, _, _, colonne = GRILLES[grille]
    inconnues = {l["etiquette"] for l in lignes if l["etiquette"] not in etiquettes}
    if inconnues:
        raise ValueError(f"Étiquettes hors grille dans {chemin.name} : {sorted(inconnues)}")
    return {l[colonne]: l["etiquette"] for l in lignes}


def main() -> None:
    """Compare deux fichiers : kappa (3 étiquettes et binaire), matrice, désaccords."""
    parseur = argparse.ArgumentParser(description="Kappa de Cohen entre deux annotateurs (F3 ou F5).")
    parseur.add_argument("fichier_1", type=Path)
    parseur.add_argument("fichier_2", type=Path)
    parseur.add_argument("--grille", default="f3", choices=tuple(GRILLES))
    arguments = parseur.parse_args()
    etiquettes, positives, nom_binaire, _ = GRILLES[arguments.grille]
    a = lire_annotations(arguments.fichier_1, arguments.grille)
    b = lire_annotations(arguments.fichier_2, arguments.grille)
    communes = sorted(set(a) & set(b))
    print(f"Éléments annotés par les deux : {len(communes)} (seulement 1 : {len(set(a) ^ set(b))})")
    e1, e2 = [a[i] for i in communes], [b[i] for i in communes]
    print(f"Kappa (3 étiquettes)          : {kappa_cohen(e1, e2):.3f}")
    print(f"Kappa ({nom_binaire:20s}): {kappa_cohen([x in positives for x in e1], [x in positives for x in e2]):.3f}")
    print("\nMatrice (lignes : fichier 1 ; colonnes : fichier 2) :")
    print(" " * 30 + "".join(f"{e[:14]:>16s}" for e in etiquettes))
    for x in etiquettes:
        print(f"{x:30s}" + "".join(f"{sum(1 for i in communes if a[i] == x and b[i] == y):16d}" for y in etiquettes))
    desaccords = [i for i in communes if a[i] != b[i]]
    print(f"\nDésaccords à discuter ({len(desaccords)}) : {', '.join(desaccords) or 'aucun'}")


if __name__ == "__main__":
    main()
