# Transformer pour F2 — validation (séance 1/5)

*2026-11-23. Modèle `nlpaueb/legal-bert-small-uncased` (D-012 proposée). Tests fermés.
Expérience MLflow : `F2-transformer`. Scripts : `training/transformer_extraction.py`,
`evaluation/reevaluer_seuils_transformer.py`.*

## Protocole

- Deux modèles (D-013 proposée) : **3 familles CUAD** sur les segments PDF par blocs (D-011),
  train 84 779 / validation 11 465 segments ; **confidentialité** sur ContractNLI (D-009),
  train 18 355 / dev 2 872 segments.
- Réglages fixés avant chaque entraînement : taux d'apprentissage 5e-5, 3 époques, lots de 32,
  256 tokens, graine 0. Sur la validation : meilleure époque (macro-F1) et seuil par famille.
- Perte pondérée : poids des positifs = négatifs / positifs (expérience 1), puis sa **racine
  carrée** (expérience 2, décidée après le diagnostic de l'expérience 1, avant de la lancer).

## Résultats

### Confidentialité (dev ContractNLI)

| Modèle | Précision | Rappel | F1 |
|---|---|---|---|
| Mots-clés (figés) | 0,433 | 0,877 | 0,580 |
| TF-IDF + régression logistique | — | — | 0,830 |
| **Transformer** (poids ≈ 4, époque 3, seuil 0,95) | 0,852 | 0,873 | **0,862** |

### Trois familles CUAD (validation, 61 contrats)

| Modèle | F1 durée | F1 résiliation | F1 responsabilité | **macro-F1** | **macro rappel par annotation** |
|---|---|---|---|---|---|
| TF-IDF (D-011) | 0,723 | **0,554** | **0,689** | **0,656** | 0,724 |
| Transformer, poids = rapport (≈ 100) | 0,673 | 0,344 | 0,502 | 0,506 | **0,786** |
| … même modèle, grille de seuils élargie | 0,678 | 0,344 | 0,570 | 0,531 | 0,717 |
| **Transformer, poids = racine du rapport (≈ 10)** | **0,732** | 0,473 | 0,670 | 0,625 | 0,773 |

Macro-F1 par époque (expérience 2) : 0,510 → 0,614 → 0,625 (encore en hausse à l'époque 3).

## Comment lire ces chiffres

1. **Confidentialité : le Transformer est le meilleur** (0,862 contre 0,830 pour TF-IDF).
2. **Un poids trop fort fait dire « oui » trop souvent** : avec un poids ≈ 100, le modèle signale
   beaucoup de segments (résiliation : 156 fausses alertes pour 52 justes). Le seuil ne compense
   pas : même avec une grille élargie, le F1 reste à 0,53. Avec un poids ≈ 10, les fausses alertes
   de résiliation tombent à 74 et le macro-F1 monte à 0,625.
3. **Trois familles : le Transformer et TF-IDF sont proches**, avec deux lectures différentes :
   - par segment, TF-IDF reste un peu meilleur (0,656 contre 0,625), surtout en résiliation ;
   - par clause annotée, le Transformer en trouve davantage (0,773 contre 0,724, soit environ
     5 annotations de plus par famille en résiliation et 8 en responsabilité).
   Avec 61 contrats de validation, l'écart de F1 par segment (3 points) n'est pas décisif.
4. **La résiliation reste la plus difficile** pour les deux modèles (même vocabulaire pour une
   résiliation sans motif et pour faute).
5. Chiffres **optimistes** (époque et seuils choisis sur la validation) ; le modèle progressait
   encore à l'époque 3 : plus d'époques ou un modèle plus grand (legal-bert-base) pourraient aider.

## Limites

- **Contamination possible du préentraînement** : Legal-BERT a été préentraîné sur des textes
  juridiques incluant des contrats EDGAR ; certains contrats CUAD (aussi issus d'EDGAR) ont pu y
  figurer. Cela ne donne pas les étiquettes au modèle, mais peut l'avantager sur ces textes.
- Une seule graine : la variabilité d'un entraînement à l'autre n'est pas mesurée.
- 256 tokens par segment : les segments plus longs sont tronqués (rares avec les blocs : 2 % au plafond).
