# Fiche de révision — entretien encadrant (étape 1, données CUAD)

*Mise à jour : 2026-11-22 (fin d'étape 1). Branche `exp/exploration-cuad`. Détails :
`docs/PROGRESS.md`, `notebooks/01_exploration_cuad.ipynb` (« Conclusions »), `docs/decisions.md`,
`docs/data_provenance.md`.*

## Ce qui a été fait

- **Étape 0** : dépôt, conventions, structure, environnement Python 3.11 (`.venv`), PR #1 fusionnée.
- **Étape 1 (terminée)** :
  - CUAD v1 (Zenodo) et découpage officiel (`data.zip`, GitHub) téléchargés, **empreintes vérifiées**,
    provenance et licence documentées ;
  - exploration complète (notebook, questions a à h) ;
  - **splits par contrat** (D-004) : train 347, validation 61, test 102 contrats ;
  - **segmentation v1** et projection des annotations : 79 510 segments étiquetés par famille ;
  - **test de traçabilité** automatique : les 79 510 segments retombent exactement sur le texte.
- Travail réalisé avec l'assistance de Claude Code (actions tracées dans `docs/JOURNAL_ACTIONS.md`).
- Aucune donnée ni extrait de contrat dans le dépôt public.

## Chiffres clés

| | |
|---|---|
| Contrats CUAD | **510** (25 types, EDGAR / SEC) ; 41 catégories, aucune pour la confidentialité |
| Passages annotés | **13 823** (JSON) ; **13 101** éléments dans le CSV = chiffre de l'article |
| Longueur des contrats | médiane **33 143** caractères |
| Splits | train **347** / val **61** / test **102** (test = test officiel) ; 9 catégories présentes partout |
| Segments v1 | **79 510** ; médiane 154 caractères, plafond 1 500 |
| Segments par famille (train) | durée 1,35 % · résiliation 0,88 % · responsabilité 0,81 % · **aucune 97 %** |

## Les découvertes importantes

1. **Cap et Uncapped se recouvrent** : 125 des 167 passages *Uncapped* sont exactement des passages
   *Cap* (une limite avec exception). → Tâche **multi-étiquette** ; pas d'alerte F3 sur la simple
   co-présence.
2. **L'écart 13 823 / 13 101 est expliqué** : le JSON découpe les annotations non contiguës
   (`<omitted>`) ; expliqué à 11 passages près.
3. **Positions fiables, mais seulement sur le texte CUAD** : `context` = TXT pour 510/510, positions
   exactes à 100 %. Notre extraction PDF devra être alignée.
4. **Fort déséquilibre** : 97 % des segments n'ont aucune famille → évaluer par précision, rappel
   et F1 par famille, jamais par l'exactitude globale.

## Baselines d'extraction F2 (validation, test fermé)

| Famille | Mots-clés F1 | TF-IDF + rég. log. F1 (précision / rappel) |
|---|---|---|
| durée | 0,18 | **0,73** (0,79 / 0,67) |
| résiliation | 0,30 | **0,52** (0,51 / 0,54) — la plus difficile |
| responsabilité | 0,26 | **0,76** (0,89 / 0,66) — la plus facile |
| **macro-F1** | **0,25** | **0,67** |

- Mots-clés : bon rappel, précision très faible (les mots « term », « liable » sont partout).
- Analyse de 24 erreurs : **9 étiquettes discutables** (CUAD n'annote pas chaque occurrence),
  7 liées à la segmentation. Détail : `docs/analyses/erreurs_baseline_tfidf_val.md`.
- **Planning** : baseline faite avant l'ingestion PDF (D-006), à valider.

## Lecture des PDF (étape 2, début)

- PyMuPDF lit les 510 PDF ; chaque segment garde **sa page** et ses positions (traçabilité 100 %).
- **98,3 %** des annotations de nos 9 catégories retrouvées dans le texte PDF (train), par
  correspondance **exacte** après normalisation (D-007) ; les autres sont exclues, jamais devinées.
- Segmentation des PDF à choisir (D-008) : par **blocs** PyMuPDF, 2 % de segments coupés au plafond
  contre 18,8 % en texte brut.

## Base de données et segments PDF (étape 2)

- **PostgreSQL 17 + pgvector 0.8.7** dans Docker, accès local seulement, mot de passe hors dépôt.
  408 contrats (train + val) importés : 96 244 segments, **traçabilité vérifiée en SQL (0 erreur)**.
- Baseline réentraînée sur les **segments PDF** (blocs) : macro rappel par annotation 0,724, contre
  0,719 pour le modèle entraîné sur le texte CUAD (écart = 1 à 2 annotations, non significatif).
  La fusion des fragments n'apporte rien de mesurable.

## Décisions prises par Sara le 2026-11-22, à présenter pour validation

| | Sujet | Décision |
|---|---|---|
| **D-001** | Unité de base | Le **segment** (texte + provenance) ; implémenté (v1) et testé |
| **D-002** | Confidentialité absente de CUAD | **ContractNLI** (données réelles, passages d'évidence) **+ baseline par mots-clés** (comparaison et secours) |
| **D-004** | Splits CUAD | Test officiel + validation 15 % du train, par contrat, graine 42 |
| **D-005** | Fichier des splits | Commité (titres seulement), exception de la règle 5 étendue |
| **D-006** | Protocole des baselines ; planning | Baseline avant l'étape 2 (ingestion PDF, base de données) |
| **D-007** | Alignement des annotations sur le texte PDF | Exact après normalisation étendue (Sara, 2026-11-23) |
| **D-008** | Segmentation des PDF | Blocs PyMuPDF (Sara, 2026-11-23) ; fusion testée en expérience |
| **D-010** | Base de données | PostgreSQL 17 + pgvector, Docker, `.env`, SQL sans ORM (Sara, 2026-11-23) |
| **D-011** | Données d'entraînement F2 | Segments PDF blocs, sans fusion (Sara, 2026-11-23) |

Point à discuter pour D-002 : dans un NDA, presque tout le texte parle de confidentialité ;
d'où viendront les exemples **négatifs** ?

## 5 questions probables, avec la réponse

1. **« Pourquoi le test officiel plutôt que votre propre découpage ? »**
   Il a été fixé par les auteurs de CUAD, avant nous : on ne peut pas le choisir à notre avantage,
   et c'est le même test que les travaux publiés. Mais notre tâche (classer des segments par
   famille) diffère de la leur : nos chiffres ne sont **pas directement comparables**.
2. **« Votre exploration a porté sur tout CUAD, test compris. Fuite ? »**
   Non : elle était descriptive et n'a réglé aucun modèle. Les splits et la règle d'étiquetage ont
   été fixés **avant** tout entraînement ; tout réglage se fera sur la validation (règle 2).
3. **« Comment passez-vous des annotations CUAD à vos segments ? »**
   Un segment reçoit une catégorie si son chevauchement avec un passage annoté atteint
   min(20 caractères, longueur du passage). Règle fixée à l'avance ; une seule annotation sur 3 257
   n'étiquette aucun segment.
4. **« Comment garantissez-vous la traçabilité ? »**
   Chaque segment garde ses positions `[debut, fin)` dans le texte source ; un test automatique
   vérifie `texte[debut:fin] == segment` pour les 79 510 segments.
5. **« 97 % de segments sans famille : comment évaluer ? »**
   L'exactitude serait trompeuse (97 % en répondant toujours « aucune »). On mesure précision,
   rappel et F1 **par famille**, sur la validation pour régler, puis une fois sur le test.
6. **« Pourquoi la résiliation est-elle la plus difficile ? »**
   Résilier *sans motif* et résilier *pour faute* emploient les mêmes mots ; TF-IDF compte les mots
   sans comprendre la phrase. Et la famille mélange deux catégories assez différentes
   (résiliation sans motif, obligations après la fin du contrat). Un Transformer, qui tient compte
   du contexte, devrait aider.
