# NLI sur ContractNLI (F4) — dev

*2026-11-23. Modèle `nlpaueb/legal-bert-small-uncased` (D-012). Méthode : D-014 (proposée).
Expérience MLflow : `F4-nli`. Scripts : `training/nli_contractnli.py`,
`evaluation/reevaluer_seuils_nli.py`. Test de ContractNLI fermé.*

## Tâche

Pour chaque couple (accord, hypothèse) — 61 accords × 17 hypothèses = **1 037 couples** sur le dev
(519 *Entailment*, 423 *NotMentioned*, 95 *Contradiction*) — prédire l'étiquette et **citer les
phrases d'évidence** (positions exactes dans le texte).

## Méthode

- Paires (hypothèse, phrase) à 3 classes ; entraînement sur 22 606 paires (toutes les évidences du
  train + 2 phrases neutres par accord et hypothèse, dont une « difficile ») ; 2 époques, 5e-5,
  lots de 32, 128 tokens, graine 0.
- Décision de l'accord : si aucune phrase n'atteint la confiance minimale (0,85, réglée sur le dev)
  pour « implique » ou « contredit » → *NotMentioned* (abstention) ; sinon la classe la plus
  probable, et les phrases citées sont celles dont la probabilité atteint 0,95 (réglé sur le dev).
- Grilles de seuils élargies jusqu'à 0,999 : mêmes seuils retenus (pas d'effet de bord).

## Résultats (dev)

| Système | Exactitude | Macro-F1 | F1 *NotMentioned* | F1 *Entailment* | F1 *Contradiction* | Évidences P / R / F1 |
|---|---|---|---|---|---|---|
| Classe majoritaire par hypothèse | 0,681 | 0,633 | 0,629 | 0,753 | 0,516 | — (aucune citée) |
| **Transformer (paires)** | **0,778** | **0,717** | **0,739** | **0,836** | **0,575** | 0,678 / 0,588 / 0,630 |

## Lecture

1. Le Transformer gagne **≈ 10 points d'exactitude** et 8 points de macro-F1 sur une baseline déjà
   forte (beaucoup d'hypothèses ont presque toujours la même réponse).
2. **La contradiction reste difficile** (F1 0,575, 95 cas seulement) : c'est souvent une
   **exception** (« sauf si… ») ; l'article de ContractNLI fait le même constat.
3. **Évidences** : environ 2 phrases citées sur 3 sont justes (précision 0,678), et 6 vraies
   évidences sur 10 sont citées (rappel 0,588).
4. Ici l'exactitude a un sens (les classes ne sont pas écrasées par une classe à 97 %), mais on la
   lit avec le macro-F1.

## Limites

- Chiffres du **dev**, optimistes (seuils réglés dessus) ; test fermé.
- Seules les phrases vues une par une : une contradiction qui ne se comprend qu'en combinant
  deux phrases peut échapper au modèle.
- Les NDA seulement (ContractNLI) ; une hypothèse doit être rédigée comme celles de ContractNLI.
