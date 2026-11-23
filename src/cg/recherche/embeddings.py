"""Embeddings : transformer un texte en vecteur pour la recherche « par le sens » (F5, D-015).

Place dans le projet : deux textes de sens proche ont des vecteurs proches (cosinus élevé), même
s'ils n'emploient pas les mêmes mots. Modèle proposé : ``BAAI/bge-small-en-v1.5`` (384 dimensions).

Conventions du modèle bge : vecteur = représentation du token [CLS], normalisé (longueur 1) ; les
**questions** reçoivent un préfixe d'instruction, pas les passages.
"""

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from cg.extraction.transformer import choisir_appareil, decouper_en_lots

MODELE_EMBEDDINGS: str = "BAAI/bge-small-en-v1.5"
DIMENSION: int = 384
PREFIXE_REQUETE: str = "Represent this sentence for searching relevant passages: "


class Encodeur:
    """Transforme des textes en vecteurs normalisés.

    Attributes:
        appareil: Puce de calcul utilisée.
    """

    def __init__(self, nom: str = MODELE_EMBEDDINGS, longueur_max: int = 256) -> None:
        """Charge le modèle (téléchargé une fois, puis lu en cache).

        Args:
            nom: Identifiant Hugging Face du modèle.
            longueur_max: Nombre maximal de tokens lus par texte.
        """
        self.appareil = choisir_appareil()
        self._tokeniseur = AutoTokenizer.from_pretrained(nom)
        self._modele = AutoModel.from_pretrained(nom).to(self.appareil).eval()
        self._longueur_max = longueur_max

    @torch.no_grad()
    def encoder(self, textes: list[str], taille_lot: int = 64) -> np.ndarray:
        """Vecteurs normalisés de passages.

        Args:
            textes: Textes à encoder.
            taille_lot: Textes traités ensemble.

        Returns:
            Un tableau ``(textes, 384)`` ; chaque ligne a une longueur de 1.
        """
        sorties = []
        for lot in decouper_en_lots(len(textes), taille_lot, melanger=False, graine=0):
            entree = self._tokeniseur([textes[i] for i in lot], truncation=True, max_length=self._longueur_max,
                                      padding=True, return_tensors="pt").to(self.appareil)
            cls = self._modele(**entree).last_hidden_state[:, 0]
            sorties.append(torch.nn.functional.normalize(cls, dim=-1).float().cpu().numpy())
        return np.concatenate(sorties) if sorties else np.zeros((0, DIMENSION), dtype=np.float32)

    def encoder_requete(self, question: str) -> np.ndarray:
        """Vecteur d'une question (avec le préfixe d'instruction de bge).

        Args:
            question: La question de l'utilisateur.

        Returns:
            Un vecteur de 384 nombres, de longueur 1.
        """
        return self.encoder([PREFIXE_REQUETE + question])[0]


def vers_pgvector(vecteur: np.ndarray) -> str:
    """Écrit un vecteur au format texte de pgvector (``[0.1,0.2,…]``).

    Args:
        vecteur: Le vecteur.

    Returns:
        Le texte à passer à PostgreSQL avec ``::vector``.
    """
    return "[" + ",".join(f"{x:.6f}" for x in vecteur) + "]"
