"""Modèle de paires (hypothèse, phrase) à trois classes, et décision au niveau du document (F4).

Place dans le projet : le Transformer (D-012, D-014) lit l'hypothèse et la phrase ensemble
(« [CLS] hypothèse [SEP] phrase [SEP] ») et donne trois probabilités : neutre, implique, contredit.

Décision au niveau du document (règle fixée avant le réglage, D-014) :
- ``s_E`` = probabilité « implique » maximale sur les phrases, ``s_C`` = probabilité « contredit »
  maximale ;
- si ``max(s_E, s_C) < seuil_document`` : **NotMentioned** (abstention : rien de fiable) ;
- sinon : la classe du maximum, et les **évidences citées** sont les phrases dont la probabilité de
  cette classe atteint ``seuil_evidence``.
Les deux seuils sont réglés sur le **dev**.
"""

from dataclasses import dataclass

import numpy as np
import torch
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from cg.extraction.transformer import decouper_en_lots
from cg.nli.paires import ETIQUETTES, INDICE, Paire


@dataclass(frozen=True)
class DecisionDocument:
    """Décision pour un couple (document, hypothèse).

    Attributes:
        etiquette: ``NotMentioned``, ``Entailment`` ou ``Contradiction``.
        evidences: Indices des phrases citées comme évidence (vide si ``NotMentioned``).
        score: Probabilité maximale de la classe retenue (0 si ``NotMentioned``).
    """

    etiquette: str
    evidences: tuple[int, ...]
    score: float


def entrainer_paires(
    modele: PreTrainedModel, tokeniseur: PreTrainedTokenizerBase, paires: list[Paire],
    appareil: torch.device, epoques: int, taux_apprentissage: float, taille_lot: int = 32,
    longueur_max: int = 128, graine: int = 0,
) -> list[float]:
    """Entraîne le modèle sur les paires (entropie croisée à trois classes, AdamW).

    Args:
        modele: Modèle à 3 sorties (modifié sur place).
        tokeniseur: Son tokeniseur.
        paires: Paires d'entraînement.
        appareil: Appareil de calcul.
        epoques: Nombre de passages sur les paires.
        taux_apprentissage: Taille des pas de mise à jour.
        taille_lot: Paires par mise à jour.
        longueur_max: Tokens maximum pour l'ensemble hypothèse + phrase.
        graine: Graine du mélange.

    Returns:
        La perte moyenne de chaque époque.
    """
    modele.to(appareil)
    perte_fn = torch.nn.CrossEntropyLoss()
    optimiseur = torch.optim.AdamW(modele.parameters(), lr=taux_apprentissage)
    cibles = torch.tensor([p.etiquette for p in paires], dtype=torch.long)
    pertes: list[float] = []
    for epoque in range(1, epoques + 1):
        modele.train()
        total = 0.0
        lots = decouper_en_lots(len(paires), taille_lot, melanger=True, graine=graine + epoque)
        for lot in lots:
            entree = tokeniseur([paires[i].texte_hypothese for i in lot], [paires[i].texte_span for i in lot],
                                truncation="only_second", max_length=longueur_max, padding=True,
                                return_tensors="pt").to(appareil)
            perte = perte_fn(modele(**entree).logits, cibles[lot].to(appareil))
            optimiseur.zero_grad()
            perte.backward()
            optimiseur.step()
            total += float(perte.detach())
        pertes.append(total / len(lots))
    return pertes


@torch.no_grad()
def probas_paires(
    modele: PreTrainedModel, tokeniseur: PreTrainedTokenizerBase, paires: list[Paire],
    appareil: torch.device, longueur_max: int = 128, taille_lot: int = 128,
) -> np.ndarray:
    """Probabilités des trois classes pour chaque paire.

    Args:
        modele: Modèle entraîné.
        tokeniseur: Son tokeniseur.
        paires: Paires à juger.
        appareil: Appareil de calcul.
        longueur_max: Tokens maximum par paire.
        taille_lot: Paires traitées ensemble.

    Returns:
        Un tableau ``(paires, 3)`` dans l'ordre de ``ETIQUETTES``.
    """
    modele.eval()
    sorties = []
    for lot in decouper_en_lots(len(paires), taille_lot, melanger=False, graine=0):
        entree = tokeniseur([paires[i].texte_hypothese for i in lot], [paires[i].texte_span for i in lot],
                            truncation="only_second", max_length=longueur_max, padding=True,
                            return_tensors="pt").to(appareil)
        sorties.append(torch.softmax(modele(**entree).logits, dim=-1).float().cpu().numpy())
    return np.concatenate(sorties) if sorties else np.zeros((0, len(ETIQUETTES)))


def decider(probas: np.ndarray, seuil_document: float, seuil_evidence: float) -> DecisionDocument:
    """Décision pour un couple (document, hypothèse) à partir des probabilités de ses phrases.

    Args:
        probas: Probabilités ``(phrases, 3)`` de toutes les phrases du document pour l'hypothèse.
        seuil_document: Confiance minimale pour affirmer « implique » ou « contredit ».
        seuil_evidence: Probabilité minimale pour citer une phrase comme évidence.

    Returns:
        La décision, avec les indices des phrases citées.
    """
    if len(probas) == 0:
        return DecisionDocument("NotMentioned", (), 0.0)
    s_e = float(probas[:, INDICE["Entailment"]].max())
    s_c = float(probas[:, INDICE["Contradiction"]].max())
    if max(s_e, s_c) < seuil_document:
        return DecisionDocument("NotMentioned", (), 0.0)
    classe = "Entailment" if s_e >= s_c else "Contradiction"
    colonne = probas[:, INDICE[classe]]
    evidences = tuple(int(i) for i in np.flatnonzero(colonne >= seuil_evidence))
    if not evidences:  # on cite toujours au moins la phrase la plus probable
        evidences = (int(colonne.argmax()),)
    return DecisionDocument(classe, evidences, max(s_e, s_c))
