"""Lecture de CUAD v1 et projection de ses annotations sur nos segments.

Place dans le projet : ce module transforme les données brutes de CUAD (``CUAD_v1.json``) en
données d'entraînement pour F2 : des segments (D-001) étiquetés par famille de clauses.
Les positions sont celles du texte ``context`` de CUAD, vérifiées exactes pendant l'exploration
(``notebooks/01_exploration_cuad.ipynb``, section a.4).

Règle de projection (fixée avant de voir les résultats) : un segment reçoit la catégorie C si
son chevauchement avec une annotation de C atteint au moins ``min(SEUIL_CHEVAUCHEMENT,
longueur de l'annotation)`` caractères.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from cg.ingestion.segmentation import Segment

# Nos familles de clauses et les catégories CUAD correspondantes (voir docs/data_provenance.md).
# La confidentialité n'a pas de catégorie dans CUAD (D-002).
FAMILLES: dict[str, list[str]] = {
    "durée": [
        "Agreement Date",
        "Effective Date",
        "Expiration Date",
        "Renewal Term",
        "Notice Period To Terminate Renewal",
    ],
    "résiliation": ["Termination For Convenience", "Post-Termination Services"],
    "responsabilité": ["Cap On Liability", "Uncapped Liability"],
}
FAMILLE_DE: dict[str, str] = {cat: fam for fam, cats in FAMILLES.items() for cat in cats}
NOS_CATEGORIES: list[str] = list(FAMILLE_DE)

# 20 caractères : assez pour ignorer un segment qui ne touche que le bord d'une longue clause,
# assez peu pour qu'une date courte (médiane : 16 caractères) compte si elle est entière.
SEUIL_CHEVAUCHEMENT: int = 20


@dataclass(frozen=True)
class Annotation:
    """Un passage annoté par CUAD.

    Attributes:
        titre: Titre du contrat.
        categorie: Catégorie CUAD (par exemple ``"Cap On Liability"``).
        debut: Position de début dans le texte ``context``.
        fin: Position juste après la fin du passage.
    """

    titre: str
    categorie: str
    debut: int
    fin: int


@dataclass
class SegmentEtiquete:
    """Un segment et les étiquettes héritées des annotations CUAD.

    Attributes:
        segment: Le segment et sa provenance.
        categories: Catégories CUAD (parmi les nôtres) projetées sur ce segment, triées.
        familles: Familles correspondantes, triées ; vide si le segment n'en a aucune.
    """

    segment: Segment
    categories: list[str] = field(default_factory=list)
    familles: list[str] = field(default_factory=list)


def charger_cuad(chemin_json: Path) -> tuple[dict[str, str], list[Annotation]]:
    """Lit ``CUAD_v1.json`` : textes des contrats et annotations de toutes les catégories.

    Args:
        chemin_json: Chemin vers ``CUAD_v1.json``.

    Returns:
        Un couple (textes, annotations) : ``textes`` associe chaque titre à son ``context`` ;
        ``annotations`` contient tous les passages-réponses.

    Raises:
        ValueError: Si une position ``answer_start`` ne retombe pas sur le texte annoté.
    """
    with open(chemin_json, encoding="utf-8") as fichier:
        cuad = json.load(fichier)

    textes: dict[str, str] = {}
    annotations: list[Annotation] = []
    for contrat in cuad["data"]:
        titre = contrat["title"]
        for paragraphe in contrat["paragraphs"]:  # un seul par contrat dans CUAD v1
            texte = paragraphe["context"]
            textes[titre] = texte
            for qa in paragraphe["qas"]:
                categorie = qa["id"].rsplit("__", 1)[1]
                for reponse in qa["answers"]:
                    debut = reponse["answer_start"]
                    fin = debut + len(reponse["text"])
                    # Garde-fou de traçabilité : on refuse une position fausse plutôt que de
                    # propager une erreur silencieuse jusqu'aux étiquettes.
                    if texte[debut:fin] != reponse["text"]:
                        raise ValueError(f"Position inexacte : {qa['id']} à {debut}")
                    annotations.append(Annotation(titre, categorie, debut, fin))
    return textes, annotations


def chevauchement(debut_a: int, fin_a: int, debut_b: int, fin_b: int) -> int:
    """Nombre de caractères communs à deux intervalles [debut, fin).

    Args:
        debut_a: Début du premier intervalle.
        fin_a: Fin (exclue) du premier intervalle.
        debut_b: Début du second intervalle.
        fin_b: Fin (exclue) du second intervalle.

    Returns:
        La longueur de l'intersection, 0 si les intervalles sont disjoints.
    """
    return max(0, min(fin_a, fin_b) - max(debut_a, debut_b))


def categories_par_segment(
    segments: list[Segment],
    annotations: list[Annotation],
    seuil: int = SEUIL_CHEVAUCHEMENT,
) -> list[list[str]]:
    """Règle de chevauchement, pour n'importe quelles catégories (CUAD, hypothèses ContractNLI…).

    Un segment reçoit la catégorie C si son chevauchement avec une annotation de C atteint au
    moins ``min(seuil, longueur de l'annotation)`` caractères. Les annotations vides sont ignorées.

    Args:
        segments: Segments d'un seul document.
        annotations: Annotations de ce même document.
        seuil: Chevauchement minimal, plafonné à la longueur de l'annotation.

    Returns:
        Pour chaque segment (même ordre), la liste triée de ses catégories.
    """
    utiles = [a for a in annotations if a.fin > a.debut]
    return [
        sorted({a.categorie for a in utiles
                if chevauchement(s.debut, s.fin, a.debut, a.fin) >= min(seuil, a.fin - a.debut)})
        for s in segments
    ]


def projeter_annotations(
    segments: list[Segment],
    annotations: list[Annotation],
    seuil: int = SEUIL_CHEVAUCHEMENT,
) -> list[SegmentEtiquete]:
    """Étiquette les segments d'un contrat avec nos catégories, selon la règle de chevauchement.

    Args:
        segments: Segments d'un seul contrat.
        annotations: Annotations de ce même contrat (les catégories hors de nos familles
            sont ignorées).
        seuil: Chevauchement minimal, plafonné à la longueur de l'annotation.

    Returns:
        Un ``SegmentEtiquete`` par segment, dans le même ordre.
    """
    # Une annotation vide aurait un seuil de 0 et étiquetterait tous les segments : on l'exclut.
    nos_annotations = [a for a in annotations if a.categorie in FAMILLE_DE and a.fin > a.debut]
    resultats: list[SegmentEtiquete] = []
    for segment in segments:
        categories = {
            a.categorie
            for a in nos_annotations
            if chevauchement(segment.debut, segment.fin, a.debut, a.fin)
            >= min(seuil, a.fin - a.debut)
        }
        resultats.append(
            SegmentEtiquete(
                segment=segment,
                categories=sorted(categories),
                familles=sorted({FAMILLE_DE[c] for c in categories}),
            )
        )
    return resultats
