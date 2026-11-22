"""Script : créer le fichier des splits train / val / test de CUAD (D-004).

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -m cg.datasets.creer_splits

Entrées : ``data/raw/cuad/CUAD_v1/CUAD_v1.json`` et ``data/raw/cuad_official/data.zip``.
Sortie : ``data/splits/cuad_v1_splits.json`` (titres seulement, aucun texte de contrat).
Le script vérifie la partition des 510 contrats et affiche la présence de nos 9 catégories.
"""

from datetime import date
from pathlib import Path

from cg.datasets.cuad import NOS_CATEGORIES, charger_cuad
from cg.datasets.splits import (
    JEUX,
    construire_splits,
    ecrire_splits,
    titres_dans_zip,
    verifier_partition,
)

RACINE = Path(__file__).resolve().parents[3]
CHEMIN_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1" / "CUAD_v1.json"
CHEMIN_ZIP_OFFICIEL = RACINE / "data" / "raw" / "cuad_official" / "data.zip"
CHEMIN_SPLITS = RACINE / "data" / "splits" / "cuad_v1_splits.json"

# Noms des fichiers dans data.zip, d'après run.sh du dépôt officiel.
FICHIER_TRAIN_OFFICIEL = "train_separate_questions.json"
FICHIER_TEST_OFFICIEL = "test.json"

# Fixés dans D-004 AVANT le tirage : ne pas les modifier pour « améliorer » un résultat.
GRAINE = 42
PROPORTION_VAL = 0.15


def main() -> None:
    """Construit, vérifie, écrit et résume le fichier des splits."""
    textes, annotations = charger_cuad(CHEMIN_CUAD)
    tous_les_titres = set(textes)

    train_officiel = titres_dans_zip(CHEMIN_ZIP_OFFICIEL, FICHIER_TRAIN_OFFICIEL)
    test_officiel = titres_dans_zip(CHEMIN_ZIP_OFFICIEL, FICHIER_TEST_OFFICIEL)
    commun = set(train_officiel) & set(test_officiel)
    union = set(train_officiel) | set(test_officiel)
    print("Découpage officiel")
    print(f"  train officiel : {len(train_officiel)} contrats")
    print(f"  test officiel  : {len(test_officiel)} contrats")
    print(f"  en commun      : {len(commun)}")
    print(f"  union = les {len(tous_les_titres)} contrats de CUAD_v1.json ? {union == tous_les_titres}")

    splits = construire_splits(train_officiel, test_officiel, PROPORTION_VAL, GRAINE)
    verifier_partition(splits, tous_les_titres)  # lève une erreur en cas de problème
    print("\nPartition vérifiée : chaque contrat est dans un seul jeu.")

    ecrire_splits(
        CHEMIN_SPLITS,
        splits,
        {
            "description": "Splits de CUAD v1 par contrat (D-004, option 1). Titres seulement.",
            "source_test": "test.json de data.zip, github.com/TheAtticusProject/cuad@7aad649",
            "graine_validation": GRAINE,
            "proportion_validation": PROPORTION_VAL,
            "cree_le": date.today().isoformat(),
        },
    )
    print(f"Fichier écrit : {CHEMIN_SPLITS.relative_to(RACINE)}")

    # Présence de nos catégories : nombre de contrats de chaque jeu qui en ont au moins une.
    jeu_de = {titre: jeu for jeu in JEUX for titre in splits[jeu]}
    presence = {jeu: {cat: set() for cat in NOS_CATEGORIES} for jeu in JEUX}
    for annotation in annotations:
        if annotation.categorie in NOS_CATEGORIES:
            presence[jeu_de[annotation.titre]][annotation.categorie].add(annotation.titre)

    print("\nContrats par jeu :", {jeu: len(splits[jeu]) for jeu in JEUX})
    print(f"\n{'Catégorie (contrats qui l ont)':40s}" + "".join(f"{jeu:>8s}" for jeu in JEUX))
    for cat in NOS_CATEGORIES:
        print(f"{cat:40s}" + "".join(f"{len(presence[jeu][cat]):8d}" for jeu in JEUX))
    absentes = [(jeu, cat) for jeu in JEUX for cat in NOS_CATEGORIES if not presence[jeu][cat]]
    print("\nToutes nos catégories présentes dans chaque jeu ?", not absentes)
    if absentes:
        print("Absentes :", absentes)


if __name__ == "__main__":
    main()
