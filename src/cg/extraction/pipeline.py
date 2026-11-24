"""Extraction de clauses dans l'application (F2) : les modèles et seuils retenus par D-012 et D-013.

Place dans le projet : l'API (F6) appelle ce module pour étiqueter les segments d'un contrat importé.
Chaque famille utilise le modèle choisi **sur la validation, avant toute ouverture du test** :

| Famille | Modèle | Seuil | Décision |
|---|---|---|---|
| durée | Transformer Legal-BERT small (poids atténué) | 0,27 | D-012 |
| résiliation | TF-IDF + régression logistique | 0,54 | D-012 |
| responsabilité | Transformer Legal-BERT small (poids atténué) | 0,34 | D-012 |
| confidentialité | Transformer Legal-BERT small (ContractNLI) | 0,95 (exception au critère, D-019) | D-013, D-019 |

Les modèles sont chargés une seule fois (au premier appel), depuis ``models/`` (jamais commité).
"""

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import joblib
import numpy as np
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from cg.extraction.transformer import choisir_appareil, predire_probas

RACINE = Path(__file__).resolve().parents[3]
DOSSIER_MODELES = RACINE / "models"
SEUILS: dict[str, float] = {"durée": 0.27, "résiliation": 0.54, "responsabilité": 0.34, "confidentialité": 0.95}
FAMILLES_CUAD = ("durée", "résiliation", "responsabilité")  # ordre des sorties du modèle CUAD
NOM_MODELES: dict[str, str] = {
    "durée": "legal-bert-small-poids-racine", "responsabilité": "legal-bert-small-poids-racine",
    "résiliation": "tfidf-bigrammes-C10", "confidentialité": "legal-bert-small-contractnli",
}


@dataclass(frozen=True)
class ClauseDetectee:
    """Une famille détectée dans un segment.

    Attributes:
        indice: Indice du segment dans la liste fournie.
        famille: Famille de clause.
        score: Probabilité donnée par le modèle.
        modele: Nom du modèle (traçabilité, F7).
    """

    indice: int
    famille: str
    score: float
    modele: str


class ExtracteurClauses:
    """Applique les modèles retenus à une liste de textes de segments."""

    def __init__(self, dossier: Path = DOSSIER_MODELES) -> None:
        """Prépare le chargement paresseux des modèles.

        Args:
            dossier: Dossier des modèles entraînés.
        """
        self._dossier = dossier
        self._appareil = choisir_appareil()

    @cached_property
    def _cuad(self):
        chemin = self._dossier / "f2-cuad-legal-bert-small-poids-racine"
        return (AutoTokenizer.from_pretrained(chemin),
                AutoModelForSequenceClassification.from_pretrained(chemin).to(self._appareil))

    @cached_property
    def _confidentialite(self):
        chemin = self._dossier / "f2-confidentialite-legal-bert-small"
        return (AutoTokenizer.from_pretrained(chemin),
                AutoModelForSequenceClassification.from_pretrained(chemin).to(self._appareil))

    @cached_property
    def _resiliation(self) -> dict:
        return joblib.load(self._dossier / "f2-resiliation-tfidf.joblib")

    def probabilites(self, textes: list[str]) -> dict[str, np.ndarray]:
        """Probabilité de chaque famille pour chaque texte, avec le modèle retenu pour cette famille.

        Args:
            textes: Textes des segments.

        Returns:
            ``famille -> tableau de probabilités`` (une par texte).
        """
        if not textes:
            return {f: np.zeros(0) for f in SEUILS}
        tokeniseur, modele = self._cuad
        cuad = predire_probas(modele, tokeniseur, textes, self._appareil, 256)
        tokeniseur_c, modele_c = self._confidentialite
        conf = predire_probas(modele_c, tokeniseur_c, textes, self._appareil, 256)[:, 0]
        r = self._resiliation
        resil = r["classifieur"].predict_proba(r["vectoriseur"].transform(textes))[:, 1]
        return {"durée": cuad[:, FAMILLES_CUAD.index("durée")],
                "responsabilité": cuad[:, FAMILLES_CUAD.index("responsabilité")],
                "résiliation": resil, "confidentialité": conf}

    def detecter(self, textes: list[str]) -> list[ClauseDetectee]:
        """Familles détectées (probabilité ≥ seuil retenu) pour chaque texte.

        Args:
            textes: Textes des segments.

        Returns:
            Une entrée par (segment, famille) détectée.
        """
        probas = self.probabilites(textes)
        return [ClauseDetectee(int(i), f, float(p[i]), NOM_MODELES[f])
                for f, p in probas.items() for i in np.flatnonzero(p >= SEUILS[f])]
