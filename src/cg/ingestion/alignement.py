"""Alignement : retrouver un passage annoté par CUAD dans le texte extrait d'un PDF (F1, F7).

Place dans le projet : les annotations CUAD ont des positions dans le texte ``context`` de CUAD,
pas dans le texte que PyMuPDF extrait du PDF (limite 3 de ``docs/data_provenance.md``). Pour
qu'une annotation garde sa provenance (page, positions) dans **notre** texte, on la recherche
dans le texte PyMuPDF.

Principe : on compare des versions **normalisées** des deux textes, en gardant pour chaque
caractère normalisé la position du caractère d'origine. Une fois le passage trouvé dans le texte
normalisé, on revient aux positions exactes du texte PyMuPDF.

Deux niveaux de normalisation :
- ``"espaces"`` : toute suite d'espaces et de sauts de ligne devient un seul espace ;
- ``"etendue"`` : en plus, minuscules, ligatures décomposées (NFKC), guillemets et tirets
  typographiques unifiés, tirets de césure invisibles supprimés.
"""

import unicodedata
from dataclasses import dataclass
from typing import Literal

Niveau = Literal["espaces", "etendue"]

# Caractères typographiques ramenés à leur équivalent simple (niveau « etendue »).
_EQUIVALENTS: dict[str, str] = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "−": "-", " ": " ",
}
_CESURE_INVISIBLE = "­"


@dataclass(frozen=True)
class TexteNormalise:
    """Un texte normalisé et, pour chaque caractère, sa position dans le texte d'origine.

    Attributes:
        texte: Le texte normalisé.
        origine: ``origine[i]`` = position dans le texte d'origine du caractère ``texte[i]``.
    """

    texte: str
    origine: list[int]


def _forme(caractere: str, niveau: Niveau) -> str:
    """Forme normalisée d'un caractère (chaîne vide s'il doit disparaître).

    Args:
        caractere: Un caractère du texte d'origine.
        niveau: Niveau de normalisation.

    Returns:
        Zéro, un ou plusieurs caractères (une ligature « ﬁ » donne « fi »).
    """
    if caractere.isspace():
        return " "
    if niveau == "espaces":
        return caractere
    if caractere == _CESURE_INVISIBLE:
        return ""
    caractere = _EQUIVALENTS.get(caractere, caractere)
    return unicodedata.normalize("NFKC", caractere).lower()


def normaliser(texte: str, niveau: Niveau = "espaces") -> TexteNormalise:
    """Normalise un texte en gardant le lien avec les positions d'origine.

    Args:
        texte: Texte d'origine.
        niveau: ``"espaces"`` ou ``"etendue"``.

    Returns:
        Le texte normalisé, sans espace au début ni à la fin, et sans espaces consécutifs.
    """
    caracteres: list[str] = []
    origine: list[int] = []
    for position, caractere in enumerate(texte):
        for c in _forme(caractere, niveau):
            if c == " " and (not caracteres or caracteres[-1] == " "):
                continue  # pas d'espace en tête ni d'espaces consécutifs
            caracteres.append(c)
            origine.append(position)
    if caracteres and caracteres[-1] == " ":
        caracteres.pop()
        origine.pop()
    return TexteNormalise(texte="".join(caracteres), origine=origine)


def aligner(
    passage: str,
    cible: TexteNormalise,
    niveau: Niveau = "espaces",
    position_relative: float | None = None,
) -> tuple[int, int] | None:
    """Cherche un passage dans un texte cible normalisé et renvoie ses positions d'origine.

    Args:
        passage: Le passage à retrouver (par exemple le texte d'une annotation CUAD).
        cible: Le texte cible, normalisé **au même niveau** avec ``normaliser``.
        niveau: Niveau de normalisation à appliquer au passage.
        position_relative: Place approximative du passage dans son texte source, entre 0 et 1
            (``debut / longueur``). Sert à choisir entre plusieurs occurrences identiques.

    Returns:
        ``(debut, fin)`` dans le texte d'origine de la cible, ou ``None`` si le passage est absent.
    """
    motif = normaliser(passage, niveau).texte
    if not motif:
        return None
    occurrences: list[int] = []
    depart = cible.texte.find(motif)
    while depart != -1:
        occurrences.append(depart)
        depart = cible.texte.find(motif, depart + 1)
    if not occurrences:
        return None
    if position_relative is not None and len(occurrences) > 1:
        longueur = max(len(cible.texte), 1)
        meilleure = min(occurrences, key=lambda i: abs(i / longueur - position_relative))
    else:
        meilleure = occurrences[0]
    debut = cible.origine[meilleure]
    fin = cible.origine[meilleure + len(motif) - 1] + 1
    return debut, fin
