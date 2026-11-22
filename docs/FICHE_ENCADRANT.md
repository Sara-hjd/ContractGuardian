# Fiche de révision — entretien encadrant (étape 1, données CUAD)

*Mise à jour : 2026-11-22. Branche `exp/exploration-cuad`. Détails : `docs/PROGRESS.md`,
`notebooks/01_exploration_cuad.ipynb` (section « Conclusions »), `docs/decisions.md`.*

## Ce qui a été fait

- **Étape 0** : dépôt, conventions, structure du projet, environnement Python 3.11 (`.venv`), PR #1 fusionnée.
- **Étape 1** : CUAD v1 téléchargé depuis Zenodo, **empreinte MD5 vérifiée**, provenance et licence
  (CC BY 4.0) documentées (`docs/data_provenance.md`). Exploration complète dans un notebook
  (questions a à h), résultats interprétés. Travail réalisé avec l'assistance de Claude Code
  (actions tracées dans `docs/JOURNAL_ACTIONS.md`).
- **Règle tenue** : aucune donnée ni extrait de contrat dans le dépôt public (notebook commité sans sorties).

## Chiffres clés de CUAD

| | |
|---|---|
| Contrats | **510** (25 types, EDGAR / SEC), 1 texte par contrat |
| Catégories | **41** ; aucune pour la confidentialité |
| Passages annotés (JSON) | **13 823**, positions exactes à 100 % |
| Annotations (article) | **13 101** = éléments de `master_clauses.csv` |
| Longueur des contrats | médiane **33 143** caractères (645 à 338 211) |
| Nos 9 catégories | de 470 contrats (*Agreement Date*) à 111 (*Uncapped Liability*, *Notice Period…*) |

## Les 3 découvertes importantes

1. **Cap et Uncapped se recouvrent** : les 111 contrats *Uncapped Liability* ont tous aussi
   *Cap On Liability*, et 125 des 167 passages *Uncapped* sont exactement des passages *Cap*. C'est
   souvent **une seule clause** (limite + exception). → F3 ne doit pas lever d'alerte sur la simple
   co-présence des deux catégories.
2. **L'écart 13 823 / 13 101 est expliqué** : l'article compte les éléments du CSV ; le JSON découpe
   les annotations non contiguës (`<omitted>`) en plusieurs passages. CSV + `<omitted>` = 13 834,
   soit l'écart expliqué à 11 passages près.
3. **Le texte CUAD est une référence fiable** : `context` = fichier TXT pour 510/510 contrats, et
   chaque position retombe sur le bon passage. Mais notre propre extraction PDF (F1) donnera un autre
   texte → **alignement nécessaire** pour garder la traçabilité.

## Décisions à valider

| | Sujet | Proposition |
|---|---|---|
| **D-001** | Unité de base | Le **segment** (passage + page + positions), commun à toutes les fonctionnalités. |
| **D-002** | Confidentialité absente de CUAD | Choisir : ContractNLI, annotation humaine, ou retrait du périmètre de F2. |
| **D-004** | Découpage train / val / test | 4 options : test officiel CUAD + validation tirée du train ; aléatoire par contrat ; stratifié par contrat ; validation croisée. Découpage **par contrat** dans tous les cas. |

## 5 questions probables, avec la réponse

1. **« Pourquoi avoir exploré tout CUAD, test compris ? N'est-ce pas une fuite ? »**
   L'exploration est **descriptive** : elle n'a réglé aucun hyperparamètre, seuil ou modèle (règle 2).
   Le découpage (D-004) sera fixé et enregistré **avant** le premier entraînement, et le test ne sera
   ouvert qu'une fois.
2. **« Pourquoi découper par contrat et pas par passage ? »**
   Les passages d'un même contrat se ressemblent (même rédaction, mêmes définitions). S'ils étaient
   à la fois en entraînement et en test, le modèle serait évalué sur ce qu'il a presque déjà vu :
   le score serait trop optimiste.
3. **« Comment comptez-vous traiter la confidentialité, absente de CUAD ? »**
   C'est D-002 : ContractNLI (accords de confidentialité annotés), ou annotation humaine sur des
   contrats réels avec un guide et un accord inter-annotateurs. Pas de données synthétiques (règle 3).
4. **« Les contrats font 33 000 caractères en médiane : comment un Transformer les lit-il ? »**
   Il ne lit que ~512 *tokens* (≈ 2 000 caractères) à la fois. On découpe en **segments** (D-001),
   chacun avec sa page et ses positions, ce qui sert aussi à citer la source exacte.
5. **« Qu'avez-vous appris qui change la conception ? »**
   Trois choses : (1) pour F3, une même clause peut porter deux étiquettes, donc il faut comparer
   des clauses distinctes ; (2) la classe « absente » domine, donc les métriques doivent en tenir
   compte ; (3) les positions CUAD ne valent que sur le texte CUAD, d'où l'alignement avec F1.
