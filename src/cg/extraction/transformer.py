"""Modèle Transformer pour l'extraction de clauses (F2), multi-étiquette.

Place dans le projet : succède aux baselines (D-006). Un modèle préentraîné (D-012) lit chaque
segment et donne, pour chaque famille, une probabilité ; un seuil par famille, réglé sur la
validation, transforme la probabilité en oui / non.

Choix d'écriture : boucle d'entraînement PyTorch écrite à la main (plutôt que ``Trainer``), pour
pouvoir expliquer chaque étape : lot → tokenisation → prédiction → perte → rétropropagation → mise
à jour des poids.

Déséquilibre : la perte (entropie croisée binaire) donne aux exemples positifs un poids
``pos_weight`` (rapport négatifs / positifs du train), comme ``class_weight="balanced"`` pour TF-IDF.
"""

import random
from collections.abc import Callable

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, PreTrainedModel, PreTrainedTokenizerBase


def choisir_appareil() -> torch.device:
    """Choisit la puce de calcul : la puce graphique du Mac (MPS) si elle existe, sinon le processeur.

    Returns:
        L'appareil PyTorch à utiliser.
    """
    return torch.device("mps" if torch.backends.mps.is_available() else "cpu")


def fixer_graines(graine: int) -> None:
    """Fixe les graines aléatoires (Python, NumPy, PyTorch) pour un résultat reproductible.

    Args:
        graine: La graine.
    """
    random.seed(graine)
    np.random.seed(graine)
    torch.manual_seed(graine)


def charger_modele(
    nom: str, nb_etiquettes: int
) -> tuple[PreTrainedTokenizerBase, PreTrainedModel]:
    """Télécharge (ou relit en cache) le tokeniseur et le modèle, avec une tête multi-étiquette.

    Args:
        nom: Identifiant Hugging Face, par exemple ``"nlpaueb/legal-bert-small-uncased"``.
        nb_etiquettes: Nombre de familles à prédire.

    Returns:
        Le tokeniseur et le modèle (tête de classification neuve, à entraîner).
    """
    tokeniseur = AutoTokenizer.from_pretrained(nom)
    modele = AutoModelForSequenceClassification.from_pretrained(
        nom, num_labels=nb_etiquettes, problem_type="multi_label_classification"
    )
    return tokeniseur, modele


def poids_positifs(y: np.ndarray, racine: bool = False) -> torch.Tensor:
    """Poids des exemples positifs pour chaque famille : nombre de négatifs / nombre de positifs.

    Args:
        y: Étiquettes du train, tableau ``(segments, familles)`` de 0 et 1.
        racine: Si vrai, prendre la racine carrée du rapport (poids atténué : ≈ 10 au lieu de
            ≈ 100 quand il y a 1 % de positifs), pour éviter un modèle qui dit « oui » trop souvent.

    Returns:
        Un tenseur d'un poids par famille.
    """
    positifs = y.sum(axis=0)
    negatifs = len(y) - positifs
    rapport = negatifs / np.maximum(positifs, 1)
    return torch.tensor(np.sqrt(rapport) if racine else rapport, dtype=torch.float32)


def decouper_en_lots(nb: int, taille: int, melanger: bool, graine: int) -> list[np.ndarray]:
    """Découpe les indices ``0..nb-1`` en lots.

    Args:
        nb: Nombre d'exemples.
        taille: Taille d'un lot.
        melanger: Mélanger l'ordre (entraînement) ou non (prédiction).
        graine: Graine du mélange.

    Returns:
        La liste des lots d'indices.
    """
    ordre = np.random.default_rng(graine).permutation(nb) if melanger else np.arange(nb)
    return [ordre[i:i + taille] for i in range(0, nb, taille)]


@torch.no_grad()
def predire_probas(
    modele: PreTrainedModel, tokeniseur: PreTrainedTokenizerBase, textes: list[str],
    appareil: torch.device, longueur_max: int = 256, taille_lot: int = 64,
) -> np.ndarray:
    """Probabilités de chaque famille pour chaque texte.

    Args:
        modele: Modèle entraîné.
        tokeniseur: Son tokeniseur.
        textes: Textes des segments.
        appareil: Appareil de calcul.
        longueur_max: Nombre maximal de tokens lus par segment (au-delà : tronqué).
        taille_lot: Nombre de segments traités ensemble.

    Returns:
        Un tableau ``(segments, familles)`` de probabilités entre 0 et 1.
    """
    modele.eval()
    sorties = []
    for lot in decouper_en_lots(len(textes), taille_lot, melanger=False, graine=0):
        entree = tokeniseur([textes[i] for i in lot], truncation=True, max_length=longueur_max,
                            padding=True, return_tensors="pt").to(appareil)
        sorties.append(torch.sigmoid(modele(**entree).logits).float().cpu().numpy())
    return np.concatenate(sorties)


def entrainer(
    modele: PreTrainedModel, tokeniseur: PreTrainedTokenizerBase, textes: list[str], y: np.ndarray,
    appareil: torch.device, epoques: int, taux_apprentissage: float, taille_lot: int = 32,
    longueur_max: int = 256, graine: int = 0,
    apres_epoque: Callable[[int, PreTrainedModel], None] | None = None,
    poids_racine: bool = False,
) -> list[float]:
    """Entraîne le modèle (entropie croisée binaire pondérée, optimiseur AdamW).

    Args:
        modele: Modèle à entraîner (modifié sur place).
        tokeniseur: Son tokeniseur.
        textes: Textes des segments d'entraînement.
        y: Étiquettes ``(segments, familles)`` de 0 et 1.
        appareil: Appareil de calcul.
        epoques: Nombre de passages complets sur le train.
        taux_apprentissage: Taille des pas de mise à jour des poids.
        taille_lot: Nombre de segments par mise à jour.
        longueur_max: Nombre maximal de tokens par segment.
        graine: Graine du mélange des lots.
        apres_epoque: Fonction appelée après chaque époque (par exemple : évaluer sur la validation).
        poids_racine: Atténuer le poids des positifs (racine carrée), voir ``poids_positifs``.

    Returns:
        La perte moyenne de chaque époque.
    """
    modele.to(appareil)
    perte_fn = torch.nn.BCEWithLogitsLoss(pos_weight=poids_positifs(y, poids_racine).to(appareil))
    optimiseur = torch.optim.AdamW(modele.parameters(), lr=taux_apprentissage)
    cibles = torch.tensor(y, dtype=torch.float32)
    pertes: list[float] = []
    for epoque in range(1, epoques + 1):
        modele.train()
        total = 0.0
        lots = decouper_en_lots(len(textes), taille_lot, melanger=True, graine=graine + epoque)
        for lot in lots:
            entree = tokeniseur([textes[i] for i in lot], truncation=True, max_length=longueur_max,
                                padding=True, return_tensors="pt").to(appareil)
            perte = perte_fn(modele(**entree).logits, cibles[lot].to(appareil))
            optimiseur.zero_grad()
            perte.backward()      # rétropropagation : comment chaque poids influence l'erreur
            optimiseur.step()     # mise à jour des poids dans le sens qui réduit l'erreur
            total += float(perte.detach())
        pertes.append(total / len(lots))
        if apres_epoque is not None:
            apres_epoque(epoque, modele)
    return pertes
