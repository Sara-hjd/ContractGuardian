"""Alertes prudentes entre deux clauses d'un même contrat (F3), version 1.

Place dans le projet : F3 ne dit jamais « ces clauses se contredisent » ; il signale un **point à
vérifier**, avec ses raisons, et cite les deux clauses (provenance). Jamais d'avis juridique.

Règle v1, **fixée le 2026-11-24 avant toute annotation humaine des paires** (aucun réglage ensuite) :
une alerte est levée si au moins une des raisons suivantes est vraie :
- **R1 (NLI)** : le modèle de F4 donne une probabilité « contredit » ≥ 0,5 entre les deux clauses,
  dans un sens ou dans l'autre (usage hors de son entraînement : heuristique à évaluer) ;
- **R2 (délais)** : les deux clauses mentionnent des délais (jours, mois, ans) et ces délais diffèrent ;
- **R3 (exception)** : l'une des clauses contient une formule d'exception (« notwithstanding »,
  « except », « unless », « provided that », « subject to »).
"""

import re
from dataclasses import dataclass

SEUIL_CONTRADICTION: float = 0.5
_NOMBRES = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
            "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30,
            "forty-five": 45, "sixty": 60, "ninety": 90}
_DELAI = re.compile(r"(?:\((\d+)\)|\b(\d+)\b|\b(" + "|".join(_NOMBRES) + r")\b)\s*(?:\(\d+\)\s*)?"
                    r"(?:calendar\s+|business\s+|consecutive\s+)?(day|month|year)s?\b", re.IGNORECASE)
_EXCEPTION = re.compile(r"\b(notwithstanding|except|unless|provided\s+that|provided,\s+however|subject\s+to)\b",
                        re.IGNORECASE)
_EN_JOURS = {"day": 1, "month": 30, "year": 365}


@dataclass(frozen=True)
class Alerte:
    """Décision pour une paire de clauses.

    Attributes:
        alerte: Vrai si un point est à vérifier.
        raisons: Codes des raisons (``R1``, ``R2``, ``R3``).
        p_contradiction: Probabilité « contredit » maximale donnée par le modèle NLI.
    """

    alerte: bool
    raisons: tuple[str, ...]
    p_contradiction: float


def delais(texte: str) -> set[int]:
    """Délais mentionnés dans un texte, convertis en jours (approximation : mois = 30, an = 365).

    Args:
        texte: Texte d'une clause.

    Returns:
        L'ensemble des délais trouvés, en jours.
    """
    resultat = set()
    for m in _DELAI.finditer(texte):
        nombre = m.group(1) or m.group(2) or m.group(3)
        valeur = int(nombre) if nombre.isdigit() else _NOMBRES[nombre.lower()]
        resultat.add(valeur * _EN_JOURS[m.group(4).lower()])
    return resultat


def decider_alerte(texte_a: str, texte_b: str, p_contradiction: float) -> Alerte:
    """Applique la règle v1 à une paire de clauses.

    Args:
        texte_a: Texte de la première clause.
        texte_b: Texte de la seconde clause.
        p_contradiction: Probabilité « contredit » maximale (modèle NLI, deux sens).

    Returns:
        La décision et ses raisons.
    """
    raisons = []
    if p_contradiction >= SEUIL_CONTRADICTION:
        raisons.append("R1")
    da, db = delais(texte_a), delais(texte_b)
    if da and db and da != db:
        raisons.append("R2")
    if _EXCEPTION.search(texte_a) or _EXCEPTION.search(texte_b):
        raisons.append("R3")
    return Alerte(alerte=bool(raisons), raisons=tuple(raisons), p_contradiction=p_contradiction)
