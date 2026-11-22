"""Baseline 1 : repérer les familles de clauses par mots-clés écrits à la main.

Place dans le projet : c'est le point de comparaison le plus simple pour F2. Si un modèle appris
ne fait pas mieux que cette liste, il n'apporte rien.

Comment la liste a été construite (2026-11-22) :
- à partir des **définitions officielles** des catégories dans ``CUAD_v1_README.txt`` et du
  vocabulaire juridique courant des contrats en anglais ;
- **avant** toute évaluation, et sans regarder les segments de validation ni de test. Elle n'est
  pas modifiée après avoir vu les résultats : sinon, on « apprendrait » sur la validation à la main.

Un segment est attribué à une famille si **au moins un** motif de cette famille y apparaît
(sans tenir compte des majuscules).
"""

import re

import numpy as np

_MOIS = (
    r"(?:january|february|march|april|may|june|july|august|september|october|november|december)"
)

# famille -> liste de (motif d'expression régulière, justification)
MOTS_CLES: dict[str, list[tuple[str, str]]] = {
    "durée": [
        (r"\bday of\b", "Agreement Date : forme « 8th day of May, 2014 »."),
        (rf"\b{_MOIS}\s+\d{{1,2}},?\s+\d{{4}}\b", "Date écrite « May 8, 2014 »."),
        (r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", "Date numérique « 5/8/2014 »."),
        (r"\beffective date\b", "Effective Date : terme défini dans la plupart des contrats."),
        (r"\bdated as of\b|\bentered into as of\b", "Agreement Date : formule d'en-tête."),
        (r"\binitial term\b|\bterm of this agreement\b", "Expiration Date : durée initiale."),
        (r"\bexpir(?:e|es|ed|ation)\b", "Expiration Date : « shall expire »."),
        (r"\brenew(?:al|als|ed|s)?\b|\bsuccessive\b", "Renewal Term : « automatically renew for successive… »."),
        (r"\bnon-renewal\b|\bnot to renew\b", "Notice Period To Terminate Renewal."),
    ],
    "résiliation": [
        (r"\bfor convenience\b|\bwithout cause\b", "Termination For Convenience : définition CUAD (« without cause »)."),
        (r"\bterminat\w*\b[^.]{0,80}\b(?:at any time|for any reason)\b", "Résiliation à tout moment, sans motif."),
        (r"\b(?:upon|after|following)\s+(?:the\s+)?(?:expiration\s+or\s+)?terminat\w*\b", "Post-Termination Services : obligations après la fin."),
        (r"\bpost-termination\b", "Post-Termination Services : terme direct."),
        (r"\btransition\b|\bwind[- ]down\b|\blast[- ](?:time\s+)?buy\b", "Post-Termination Services : transition, wind-down, last-buy (définition CUAD)."),
        (r"\bsurviv\w*\b", "Clauses de survie : obligations qui continuent après la fin du contrat."),
    ],
    "responsabilité": [
        (r"\bliab(?:le|ility|ilities)\b", "Cap / Uncapped Liability : terme central."),
        (r"\bconsequential\b|\bpunitive\b|\bincidental\b", "Exclusion de dommages indirects, fréquente dans ces clauses."),
        (r"\bin no event\b", "Formule typique d'une limitation (« In no event shall… »)."),
        (r"\bshall not exceed\b|\bin the aggregate\b", "Plafond d'un montant (Cap On Liability)."),
    ],
}

_MOTIFS_COMPILES: dict[str, re.Pattern[str]] = {
    famille: re.compile("|".join(f"(?:{motif})" for motif, _ in motifs), re.IGNORECASE)
    for famille, motifs in MOTS_CLES.items()
}


def predire_mots_cles(textes: list[str]) -> dict[str, np.ndarray]:
    """Prédit, pour chaque famille, si chaque texte contient au moins un de ses mots-clés.

    Args:
        textes: Les textes des segments.

    Returns:
        Un dictionnaire ``famille -> tableau de booléens``, un booléen par texte.
    """
    return {
        famille: np.array([motif.search(texte) is not None for texte in textes], dtype=bool)
        for famille, motif in _MOTIFS_COMPILES.items()
    }
