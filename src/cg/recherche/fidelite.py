"""Contrôle automatique des éléments critiques d'une réponse du RAG (fidélité, F5, D-026, niveau 2).

Place dans le projet : une réponse est **fidèle** si tout ce qu'elle affirme est dans les passages
cités. Ce contrôle, simple et indépendant des modèles, vérifie seulement les **éléments critiques** :
nombres (y compris écrits en lettres), durées, montants, pourcentages et mois. Chacun doit figurer
dans au moins un passage cité. Il repère les chiffres inventés (« 60 days » alors que le passage dit
« thirty (30) days ») ; il **ne voit pas** les paraphrases ni les négations (limite écrite dans D-026).

Exemple : réponse « Either party may terminate with 30 days notice. » ; passage « … upon thirty (30)
days prior written notice … » → élément 30 retrouvé (« thirty » et « (30) » valent 30) : fidèle.
"""

import re
from dataclasses import dataclass

_UNITES = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
           "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
           "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
_DIZAINES = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
             "ninety": 90}
_MULTIPLES = {"hundred": 100, "thousand": 1_000, "million": 1_000_000, "billion": 1_000_000_000}
MOIS = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
        "november", "december")
# « may » est aussi un verbe (« may terminate ») : on ne le compte comme mois que suivi d'un jour ou d'une année.
_MOT_NOMBRE = "|".join(list(_UNITES) + list(_DIZAINES) + list(_MULTIPLES))
_NOMBRE_LETTRES = re.compile(rf"\b(?:{_MOT_NOMBRE})(?:[\s-]+(?:and[\s-]+)?(?:{_MOT_NOMBRE}))*\b", re.I)
_NOMBRE_CHIFFRES = re.compile(r"(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w])|(?<![\w.,])\d+(?:\.\d+)?(?![\w])")
_MOIS = re.compile(r"\b(" + "|".join(m for m in MOIS if m != "may") + r")\b|\bmay(?=\s+\d)", re.I)


@dataclass(frozen=True)
class ControleFidelite:
    """Résultat du contrôle d'une réponse.

    Attributes:
        elements: Éléments critiques trouvés dans la réponse (nombres normalisés, mois).
        absents: Éléments de la réponse introuvables dans les passages cités.
    """

    elements: frozenset[str]
    absents: frozenset[str]

    @property
    def fidele(self) -> bool:
        """Vrai si tous les éléments critiques de la réponse sont dans les passages (ou s'il n'y en a pas)."""
        return not self.absents


def _valeur_lettres(texte: str) -> int:
    """Valeur d'un nombre écrit en lettres (« thirty-six » → 36, « two hundred » → 200)."""
    total, courant = 0, 0
    for mot in re.split(r"[\s-]+", texte.lower()):
        if mot in _UNITES:
            courant += _UNITES[mot]
        elif mot in _DIZAINES:
            courant += _DIZAINES[mot]
        elif mot in _MULTIPLES:
            courant = max(courant, 1) * _MULTIPLES[mot]
            if _MULTIPLES[mot] >= 1_000:
                total, courant = total + courant, 0
    return total + courant


def _normaliser_nombre(valeur: float) -> str:
    return str(int(valeur)) if float(valeur).is_integer() else f"{valeur:g}"


def elements_critiques(texte: str) -> set[str]:
    """Nombres (chiffres ou lettres, normalisés) et mois cités dans un texte.

    Args:
        texte: Réponse ou passage.

    Returns:
        L'ensemble des éléments, par exemple ``{"30", "1000000", "mois:june"}``.
    """
    elements = {_normaliser_nombre(float(m.group().replace(",", ""))) for m in _NOMBRE_CHIFFRES.finditer(texte)}
    elements |= {_normaliser_nombre(_valeur_lettres(m.group())) for m in _NOMBRE_LETTRES.finditer(texte)}
    elements |= {"mois:" + (m.group(1) or "may").lower() for m in _MOIS.finditer(texte)}
    return elements


def controler(reponse: str, passages: list[str]) -> ControleFidelite:
    """Vérifie que chaque élément critique de la réponse figure dans au moins un passage cité.

    Args:
        reponse: Phrase de réponse du LLM.
        passages: Textes des passages cités.

    Returns:
        Les éléments trouvés et ceux qui manquent dans les passages.
    """
    dans_reponse = elements_critiques(reponse)
    dans_passages: set[str] = set()
    for p in passages:
        dans_passages |= elements_critiques(p)
    return ControleFidelite(frozenset(dans_reponse), frozenset(dans_reponse - dans_passages))
