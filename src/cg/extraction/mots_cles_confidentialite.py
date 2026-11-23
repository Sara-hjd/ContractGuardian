"""Baseline par mots-clés pour la famille « confidentialité » (D-002).

Place dans le projet : point de comparaison, et solution de secours si les annotations de
ContractNLI ne peuvent pas être adaptées à l'extraction (D-002).

Comment la liste a été construite (2026-11-23) :
- à partir des **définitions officielles des 17 hypothèses** de ContractNLI (champ ``labels``
  de ``train.json``) et du vocabulaire courant des accords de confidentialité ;
- **avant** toute évaluation, sans regarder aucun segment ni aucune évidence annotée (train,
  dev ou test) ; elle est commitée avant le premier calcul de métriques et ne sera pas modifiée
  en fonction des résultats ;
- l'hypothèse nda-18 (« No solicitation », ne pas débaucher) n'est **pas** une clause de
  confidentialité : aucun mot-clé ne la vise.

Un segment relève de la famille si **au moins un** motif y apparaît (sans tenir compte des majuscules).
"""

import re

import numpy as np

# (motif d'expression régulière, justification)
MOTS_CLES_CONFIDENTIALITE: list[tuple[str, str]] = [
    (r"\bconfidential(?:ity)?\b", "Terme central de toutes les hypothèses (« Confidential Information »)."),
    (r"\bnon-?disclosure\b", "Nom même de ces accords (NDA)."),
    (r"\bdisclos(?:e|es|ed|ing|ure)\b", "nda-7, nda-8, nda-10 : partager, divulguer, divulgation forcée."),
    (r"\bproprietary\b|\btrade secrets?\b", "Synonymes usuels de l'information confidentielle."),
    (r"\breceiving party\b|\bdisclosing party\b", "Les deux rôles nommés dans toutes les hypothèses."),
    (r"\breverse[- ]engineer", "nda-11 : pas d'ingénierie inverse."),
    (r"\breturn or destroy\b|\bdestroy\b|\bdestruction\b", "nda-16, nda-20 : restitution ou destruction."),
    (r"\bneed to know\b", "nda-5 : partage avec les employés qui en ont besoin."),
    (r"\bsubpoena\b|\bcompelled\b|\brequired by law\b", "nda-8 : divulgation exigée par la loi ou un juge."),
    (r"\bindependently develop", "nda-12 : développement indépendant d'informations similaires."),
]

_MOTIF = re.compile("|".join(f"(?:{m})" for m, _ in MOTS_CLES_CONFIDENTIALITE), re.IGNORECASE)


def predire_confidentialite(textes: list[str]) -> np.ndarray:
    """Prédit, pour chaque texte, s'il contient au moins un mot-clé de confidentialité.

    Args:
        textes: Les textes des segments.

    Returns:
        Un tableau de booléens, un par texte.
    """
    return np.array([_MOTIF.search(t) is not None for t in textes], dtype=bool)
