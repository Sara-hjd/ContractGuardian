"""Lecture de ContractNLI et conversion de ses évidences en annotations (D-002).

Place dans le projet : ContractNLI (607 accords de confidentialité, 17 hypothèses) est la source
de données **réelles** de la famille « confidentialité » (D-002) et servira à F4 (NLI).

Format (``README.md`` du zip) : chaque document a un texte, des *spans* (phrases ou éléments de
liste, en positions de caractères) et, pour chaque hypothèse, un choix (``Entailment``,
``Contradiction``, ``NotMentioned``) et les indices des spans d'**évidence**. Les positions portent
sur le champ ``text`` du document : pas besoin d'alignement (contrairement à CUAD sur PDF).

Le jeu de test n'est chargé qu'avec ``ouvrir_test=True`` (règle 2).
"""

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from cg.datasets.cuad import Annotation

# Toutes les hypothèses sauf nda-18 (« No solicitation » : ne pas débaucher, ce n'est pas de la
# confidentialité). Proposition de D-009, modifiable.
HYPOTHESES_EXCLUES: frozenset[str] = frozenset({"nda-18"})
FICHIERS: dict[str, str] = {
    "train": "contract-nli/train.json",
    "dev": "contract-nli/dev.json",
    "test": "contract-nli/test.json",
}


@dataclass
class DocumentNli:
    """Un accord de confidentialité de ContractNLI.

    Attributes:
        identifiant: Identifiant unique du document dans ContractNLI.
        titre: Nom du fichier d'origine (sert d'identifiant de contrat dans le projet).
        texte: Texte complet du document.
        spans: Spans (phrases ou éléments de liste) en positions de caractères ``(debut, fin)``.
        choix: Hypothèse -> ``Entailment`` / ``Contradiction`` / ``NotMentioned``.
        evidences: Hypothèse -> indices des spans d'évidence.
    """

    identifiant: int
    titre: str
    texte: str
    spans: list[tuple[int, int]]
    choix: dict[str, str] = field(default_factory=dict)
    evidences: dict[str, list[int]] = field(default_factory=dict)


def charger_contractnli(chemin_zip: Path, jeu: str, ouvrir_test: bool = False) -> tuple[list[DocumentNli], dict[str, dict]]:
    """Lit un jeu de ContractNLI directement dans le zip.

    Args:
        chemin_zip: Chemin de ``contract-nli.zip``.
        jeu: ``"train"``, ``"dev"`` ou ``"test"``.
        ouvrir_test: Doit valoir ``True`` pour lire le test (évaluation finale seulement).

    Returns:
        Les documents, et les définitions des hypothèses (``labels``).

    Raises:
        PermissionError: Si le test est demandé sans ``ouvrir_test=True``.
        KeyError: Si le jeu est inconnu.
    """
    if jeu == "test" and not ouvrir_test:
        raise PermissionError("Le jeu de test de ContractNLI est fermé (règle 2) : ouvrir_test=True requis.")
    with zipfile.ZipFile(chemin_zip) as archive, archive.open(FICHIERS[jeu]) as fichier:
        donnees = json.load(fichier)
    documents = []
    for d in donnees["documents"]:
        annotations = d["annotation_sets"][0]["annotations"]
        documents.append(DocumentNli(
            identifiant=int(d["id"]),
            titre=d["file_name"],
            texte=d["text"],
            spans=[(int(a), int(b)) for a, b in d["spans"]],
            choix={h: a["choice"] for h, a in annotations.items()},
            evidences={h: list(a["spans"]) for h, a in annotations.items()},
        ))
    return documents, donnees["labels"]


def annotations_confidentialite(
    document: DocumentNli, exclues: frozenset[str] = HYPOTHESES_EXCLUES
) -> list[Annotation]:
    """Transforme les spans d'évidence en annotations de la famille confidentialité.

    Chaque span d'évidence d'une hypothèse retenue devient une annotation dont la « catégorie »
    est l'identifiant de l'hypothèse (par exemple ``nda-11``).

    Args:
        document: Le document ContractNLI.
        exclues: Hypothèses qui ne relèvent pas de la confidentialité.

    Returns:
        Les annotations, en positions de caractères dans ``document.texte``.
    """
    annotations = []
    for hypothese, indices in document.evidences.items():
        if hypothese in exclues:
            continue
        for i in indices:
            debut, fin = document.spans[i]
            annotations.append(Annotation(document.titre, hypothese, debut, fin))
    return annotations
