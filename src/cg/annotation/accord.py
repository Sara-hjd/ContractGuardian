"""Accord entre deux annotateurs : kappa de Cohen (F3, cahier des charges).

Place dans le projet : avant d'évaluer les alertes de F3 sur les annotations de Sara et d'Ilyas,
on mesure si les deux annotateurs sont d'accord. Si ce n'est pas le cas, la grille est trop floue.

**Kappa de Cohen** : ``κ = (p_o − p_e) / (1 − p_e)``, où ``p_o`` est la part de paires où les deux
annotateurs ont mis la même étiquette, et ``p_e`` la part attendue **par hasard** (si chacun
étiquetait au hasard avec ses propres fréquences). κ = 1 : accord parfait ; κ = 0 : pas mieux que le
hasard. Repères usuels (Landis et Koch) : 0,41–0,60 modéré, 0,61–0,80 substantiel, > 0,80 presque parfait.

Lancement :

    PYTHONPATH=src .venv/bin/python -m cg.annotation.accord FICHIER_1.csv FICHIER_2.csv
"""

import argparse
import csv
from collections import Counter
from pathlib import Path

ETIQUETTES_F3: tuple[str, ...] = ("COMPATIBLES", "A_VERIFIER", "CONTRADICTION_APPARENTE", "NON_COMPARABLE")
ALERTE: frozenset[str] = frozenset({"A_VERIFIER", "CONTRADICTION_APPARENTE"})


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


def lire_annotations(chemin: Path) -> dict[str, str]:
    """Lit un fichier d'annotations F3 (``id_paire, annotateur, etiquette, date``).

    Args:
        chemin: Fichier CSV d'un annotateur.

    Returns:
        ``id_paire -> étiquette``.

    Raises:
        ValueError: Si une étiquette n'appartient pas à la grille.
    """
    with open(chemin, encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f))
    inconnues = {l["etiquette"] for l in lignes if l["etiquette"] not in ETIQUETTES_F3}
    if inconnues:
        raise ValueError(f"Étiquettes hors grille dans {chemin.name} : {sorted(inconnues)}")
    return {l["id_paire"]: l["etiquette"] for l in lignes}


def main() -> None:
    """Compare deux fichiers : kappa (4 étiquettes et alerte oui/non), matrice, désaccords."""
    parseur = argparse.ArgumentParser(description="Kappa de Cohen entre deux annotateurs (F3).")
    parseur.add_argument("fichier_1", type=Path)
    parseur.add_argument("fichier_2", type=Path)
    arguments = parseur.parse_args()
    a, b = lire_annotations(arguments.fichier_1), lire_annotations(arguments.fichier_2)
    communes = sorted(set(a) & set(b))
    print(f"Paires annotées par les deux : {len(communes)} (seulement 1 : {len(set(a) ^ set(b))})")
    e1, e2 = [a[i] for i in communes], [b[i] for i in communes]
    print(f"Kappa (4 étiquettes)          : {kappa_cohen(e1, e2):.3f}")
    print(f"Kappa (alerte oui / non)      : {kappa_cohen([x in ALERTE for x in e1], [x in ALERTE for x in e2]):.3f}".replace("True", "oui"))
    print("\nMatrice (lignes : fichier 1 ; colonnes : fichier 2) :")
    print(" " * 26 + "".join(f"{e[:12]:>14s}" for e in ETIQUETTES_F3))
    for x in ETIQUETTES_F3:
        print(f"{x:26s}" + "".join(f"{sum(1 for i in communes if a[i] == x and b[i] == y):14d}" for y in ETIQUETTES_F3))
    desaccords = [i for i in communes if a[i] != b[i]]
    print(f"\nDésaccords à discuter ({len(desaccords)}) : {', '.join(desaccords) or 'aucun'}")


if __name__ == "__main__":
    main()
