"""Tests du module Transformer (F2), sans téléchargement.

On fabrique ici un **minuscule** modèle BERT (2 couches, petit vocabulaire écrit à la main) :
il sert seulement à vérifier que la boucle d'entraînement et la prédiction fonctionnent ; il ne
sert jamais à produire un résultat du projet (règle 3).
"""

from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from cg.extraction.transformer import entrainer, fixer_graines, poids_positifs, predire_probas  # noqa: E402

VOCABULAIRE = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "party", "shall", "be", "liable",
               "for", "damages", "price", "of", "units", "delivery", "goods"]


def petit_modele(tmp_path: Path):
    """Un tokeniseur et un modèle BERT minuscules, créés localement."""
    fichier = tmp_path / "vocab.txt"
    fichier.write_text("\n".join(VOCABULAIRE), encoding="utf-8")
    tokeniseur = transformers.BertTokenizerFast(vocab_file=str(fichier))
    configuration = transformers.BertConfig(
        vocab_size=len(VOCABULAIRE), hidden_size=32, num_hidden_layers=2, num_attention_heads=2,
        intermediate_size=64, num_labels=1, problem_type="multi_label_classification",
    )
    return tokeniseur, transformers.BertForSequenceClassification(configuration)


def test_poids_positifs() -> None:
    """Poids = négatifs / positifs, famille par famille."""
    y = np.array([[1, 0], [0, 0], [0, 1], [0, 1]], dtype=np.float32)
    assert poids_positifs(y).tolist() == pytest.approx([3.0, 1.0])


def test_entrainer_et_predire(tmp_path: Path) -> None:
    """Sur un corpus jouet, la perte baisse et le modèle sépare les deux classes."""
    fixer_graines(0)
    tokeniseur, modele = petit_modele(tmp_path)
    textes = ["party shall be liable for damages", "price of units", "delivery of goods",
              "liable for damages"] * 8
    y = np.array([[1], [0], [0], [1]] * 8, dtype=np.float32)
    appareil = torch.device("cpu")
    pertes = entrainer(modele, tokeniseur, textes, y, appareil, epoques=15, taux_apprentissage=5e-3,
                       taille_lot=8, longueur_max=16)
    assert pertes[-1] < pertes[0]
    probas = predire_probas(modele, tokeniseur, textes[:4], appareil, longueur_max=16)
    assert probas.shape == (4, 1)
    assert probas[0, 0] > probas[1, 0] and probas[3, 0] > probas[2, 0]


def test_poids_positifs_racine() -> None:
    """Variante atténuée : racine carrée du rapport négatifs / positifs."""
    y = np.array([[1], [0], [0], [0], [0]], dtype=np.float32)
    assert poids_positifs(y, racine=True).tolist() == pytest.approx([2.0])
