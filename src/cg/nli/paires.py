"""Paires (hypothèse, phrase) pour l'inférence en langage naturel sur ContractNLI (F4).

Place dans le projet : le modèle de F4 juge une paire à la fois : « cette phrase du contrat
implique-t-elle l'hypothèse, la contredit-elle, ou n'en dit-elle rien ? ». L'unité est la phrase
(« span ») de ContractNLI : c'est l'unité officielle des évidences, avec des positions exactes
dans le texte (traçabilité).

Échantillonnage pour l'entraînement (fixé avant l'entraînement, D-014) : toutes les phrases
d'évidence, plus, pour chaque couple (document, hypothèse), deux phrases neutres : une au hasard
et une **difficile** (une phrase qui est évidence d'une **autre** hypothèse : elle parle de
confidentialité, mais pas de celle-ci).
"""

import random
from dataclasses import dataclass

from cg.datasets.contractnli import DocumentNli

ETIQUETTES: tuple[str, ...] = ("NotMentioned", "Entailment", "Contradiction")
INDICE: dict[str, int] = {e: i for i, e in enumerate(ETIQUETTES)}


@dataclass(frozen=True)
class Paire:
    """Une paire à juger, avec sa provenance.

    Attributes:
        titre: Document d'origine.
        hypothese: Identifiant de l'hypothèse (par exemple ``nda-11``).
        indice_span: Indice de la phrase dans ``document.spans``.
        texte_hypothese: Texte de l'hypothèse.
        texte_span: Texte de la phrase (``document.texte[debut:fin]``).
        etiquette: Indice dans ``ETIQUETTES`` (0 = neutre, 1 = implique, 2 = contredit).
    """

    titre: str
    hypothese: str
    indice_span: int
    texte_hypothese: str
    texte_span: str
    etiquette: int


def texte_span(document: DocumentNli, i: int) -> str:
    """Texte d'une phrase du document.

    Args:
        document: Le document.
        i: Indice de la phrase.

    Returns:
        ``document.texte[debut:fin]`` pour cette phrase.
    """
    debut, fin = document.spans[i]
    return document.texte[debut:fin]


def paires_entrainement(
    documents: list[DocumentNli], hypotheses: dict[str, str], graine: int = 0
) -> list[Paire]:
    """Construit les paires d'entraînement (évidences + deux neutres par document et hypothèse).

    Args:
        documents: Documents du train.
        hypotheses: Identifiant -> texte de chaque hypothèse.
        graine: Graine du tirage des phrases neutres.

    Returns:
        La liste des paires.
    """
    hasard = random.Random(graine)
    paires: list[Paire] = []
    for d in documents:
        toutes_evidences = {i for indices in d.evidences.values() for i in indices}
        for h, texte_h in hypotheses.items():
            evidences = set(d.evidences.get(h, []))
            choix = d.choix.get(h, "NotMentioned")
            for i in sorted(evidences):
                paires.append(Paire(d.titre, h, i, texte_h, texte_span(d, i), INDICE[choix]))
            neutres = [i for i in range(len(d.spans)) if i not in evidences]
            difficiles = [i for i in neutres if i in toutes_evidences]
            tirees = set()
            if neutres:
                tirees.add(hasard.choice(neutres))
            if difficiles:
                tirees.add(hasard.choice(difficiles))
            for i in sorted(tirees):
                paires.append(Paire(d.titre, h, i, texte_h, texte_span(d, i), INDICE["NotMentioned"]))
    return paires


def paires_document(document: DocumentNli, hypothese: str, texte_hypothese: str) -> list[Paire]:
    """Toutes les paires (hypothèse, phrase) d'un document, pour la prédiction.

    Args:
        document: Le document.
        hypothese: Identifiant de l'hypothèse.
        texte_hypothese: Son texte.

    Returns:
        Une paire par phrase, avec l'étiquette vraie (évidence : choix du document ; sinon neutre).
    """
    evidences = set(document.evidences.get(hypothese, []))
    choix = INDICE[document.choix.get(hypothese, "NotMentioned")]
    return [Paire(document.titre, hypothese, i, texte_hypothese, texte_span(document, i),
                  choix if i in evidences else INDICE["NotMentioned"])
            for i in range(len(document.spans))]
