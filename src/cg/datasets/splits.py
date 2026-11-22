"""Découpage des contrats CUAD en jeux entraînement / validation / test (décision D-004).

Place dans le projet : ce module fabrique et vérifie le fichier des splits, qui dit pour chaque
contrat s'il sert à entraîner (train), à régler (val) ou à évaluer une seule fois (test).

Règle D-004 (option 1) :
    - test : les contrats du ``test.json`` officiel de CUAD (``data.zip`` du dépôt GitHub) ;
    - train + val : les contrats du train officiel, découpés par contrat, avec une graine fixe.

Le fichier produit ne contient que des titres de contrats, jamais de texte.
"""

import json
import random
import zipfile
from pathlib import Path

JEUX: tuple[str, ...] = ("train", "val", "test")


def titres_dans_zip(chemin_zip: Path, nom_fichier: str) -> list[str]:
    """Lit les titres des contrats d'un fichier au format SQuAD, à l'intérieur d'un zip.

    Lire dans le zip évite d'extraire sur le disque une seconde copie des textes de CUAD.

    Args:
        chemin_zip: Chemin vers ``data.zip``.
        nom_fichier: Chemin du fichier JSON dans le zip (par exemple ``"test.json"``).

    Returns:
        Les titres, triés et sans doublon.
    """
    with zipfile.ZipFile(chemin_zip) as archive, archive.open(nom_fichier) as fichier:
        donnees = json.load(fichier)
    return sorted({contrat["title"] for contrat in donnees["data"]})


def construire_splits(
    titres_train_officiel: list[str],
    titres_test_officiel: list[str],
    proportion_val: float,
    graine: int,
) -> dict[str, list[str]]:
    """Tire la validation dans le train officiel ; le test officiel reste intact.

    Args:
        titres_train_officiel: Contrats du train officiel.
        titres_test_officiel: Contrats du test officiel.
        proportion_val: Part du train officiel envoyée en validation (entre 0 et 1).
        graine: Graine du générateur aléatoire, fixée à l'avance (D-004).

    Returns:
        Un dictionnaire ``{"train": [...], "val": [...], "test": [...]}`` de titres triés.

    Raises:
        ValueError: Si la proportion est hors de ]0, 1[.
    """
    if not 0 < proportion_val < 1:
        raise ValueError(f"proportion_val doit être dans ]0, 1[, reçu : {proportion_val}")

    # On trie avant de tirer : le résultat ne dépend alors que de la graine,
    # pas de l'ordre dans lequel les titres ont été lus.
    candidats = sorted(titres_train_officiel)
    nb_val = round(len(candidats) * proportion_val)
    val = set(random.Random(graine).sample(candidats, nb_val))
    return {
        "train": sorted(t for t in candidats if t not in val),
        "val": sorted(val),
        "test": sorted(titres_test_officiel),
    }


def verifier_partition(splits: dict[str, list[str]], tous_les_titres: set[str]) -> None:
    """Vérifie que les jeux forment une partition exacte des contrats.

    Args:
        splits: Les jeux à vérifier.
        tous_les_titres: L'ensemble attendu des contrats (les 510 titres de CUAD).

    Raises:
        ValueError: Si un contrat est dans deux jeux, manque, ou est inconnu.
    """
    vus: dict[str, str] = {}
    for jeu in JEUX:
        for titre in splits[jeu]:
            if titre in vus:
                raise ValueError(f"Contrat dans deux jeux ({vus[titre]}, {jeu}) : {titre}")
            vus[titre] = jeu
    manquants = tous_les_titres - set(vus)
    inconnus = set(vus) - tous_les_titres
    if manquants or inconnus:
        raise ValueError(f"{len(manquants)} contrat(s) manquant(s), {len(inconnus)} inconnu(s)")


def ecrire_splits(chemin: Path, splits: dict[str, list[str]], metadonnees: dict[str, object]) -> None:
    """Écrit le fichier des splits en JSON lisible (titres seulement).

    Args:
        chemin: Fichier de sortie.
        splits: Les trois jeux de titres.
        metadonnees: Informations de reproductibilité (source, graine, proportion, date…).
    """
    chemin.parent.mkdir(parents=True, exist_ok=True)
    contenu = {**metadonnees, **{jeu: splits[jeu] for jeu in JEUX}}
    chemin.write_text(json.dumps(contenu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def lire_splits(chemin: Path) -> dict[str, str]:
    """Lit le fichier des splits et renvoie le jeu de chaque contrat.

    Args:
        chemin: Fichier des splits.

    Returns:
        Un dictionnaire ``titre -> "train" | "val" | "test"``.
    """
    contenu = json.loads(chemin.read_text(encoding="utf-8"))
    return {titre: jeu for jeu in JEUX for titre in contenu[jeu]}
