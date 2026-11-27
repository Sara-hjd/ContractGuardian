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

## Confidentialité (ContractNLI, D-002)

- 607 accords de confidentialité, 17 hypothèses ; évidences → segments « confidentialité »
  (sans nda-18, non-sollicitation). Train 423 / dev 61 ; test fermé.
- Mots-clés figés avant évaluation : rappel **0,877**, précision 0,433, F1 0,580 (dev).
- 51 contrats CUAD de validation sur 61 contiennent une clause de confidentialité **non annotée** :
  on ne prend pas les négatifs dans CUAD (D-009, acceptée).
- **Bilan complet de la période : `docs/DIAGNOSTIC_2026-11-16_au_2026-11-23.md`.**

## Transformer pour F2 (Legal-BERT small, validation)

- **Confidentialité** : F1 **0,862** (TF-IDF 0,830 ; mots-clés 0,580).
- **3 familles CUAD** : macro-F1 0,625 (TF-IDF 0,656) mais **rappel par annotation 0,773** (TF-IDF
  0,724) : le Transformer trouve plus de clauses, TF-IDF reste un peu plus précis par segment.
- Leçon : un poids des positifs trop fort (≈ 100) fait dire « oui » trop souvent (F1 0,506) ;
  atténué (racine, ≈ 10) → 0,625.

## NLI sur ContractNLI (F4, dev)

- Transformer sur paires (hypothèse, phrase) : exactitude **0,778**, macro-F1 **0,717** (classe
  majoritaire : 0,681 / 0,633) ; évidences citées : précision 0,678, rappel 0,588.
- La **contradiction** reste la plus difficile (F1 0,575) : souvent une exception « sauf si… ».
- *NotMentioned* sert d'abstention : sans phrase assez probante, le système n'affirme rien.

## Questions-réponses (F5, validation)

- **Recherche hybride** (mots + sens, PostgreSQL + pgvector) : **Recall@5 = 0,586** (métrique du cahier
  des charges ; mots seuls 0,518, sens seul 0,543) et Recall@10 = 0,682 (mots 0,638, sens 0,642).
- **Réponse extractive avec abstention** : exactitude équilibrée 0,521, à peine mieux que « toujours
  s'abstenir » (0,5) : la similarité ne suffit pas pour savoir s'il faut répondre.
- **RAG avec LLM local** (qwen3-vl:8b, LangGraph) : chaque citation est vérifiée mot pour mot, sinon
  abstention ; évaluation complète à faire (le Mac s'est mis en veille pendant le calcul).

## Alertes entre clauses (F3) — annotation humaine en cours

- **47 paires** de clauses d'un même contrat (validation), en 4 types de tension ; grille des **3
  étiquettes du cahier des charges** (D-020) ; annotation **indépendante** par Sara et Ilyas, accord mesuré par le **kappa de Cohen**.
- **Règle d'alerte v1 figée avant les annotations** (preuve : date du commit) : 41 alertes sur 47,
  très peu sélective (les formules d'exception sont partout) ; le NLI de F4 ne se transfère pas.
- Les annotations ne contiennent jamais de texte de contrat (test automatique).

## Application (F6) et LLM local (F5, indicatif)

- **API FastAPI + interface React** : importer un PDF (≈ 10 s pour 9 pages), lire les clauses (4 familles),
  poser une question (extractif immédiat, ou LLM ≈ 1 min), alertes F3 (expérimental), hypothèse NLI.
  Chaque passage cité a sa **page et ses positions** ; un **avertissement** est présent partout.
- **LLM local** (qwen3-vl:8b, 20 questions, **indicatif**) : exactitude équilibrée **0,643** contre 0,423
  pour l'extractif ; **0 réponse fausse** ; 13 abstentions correctes sur 13 ; mais 2 réponses trouvées
  sur 7 et 82 s par question. Mesure de référence à refaire avec `qwen3-vl:8b-instruct` (en téléchargement).
- **Mesure de référence** (2026-11-26, `qwen3-vl:8b-instruct`, sans réflexion, **200 questions** de
  validation) : exactitude équilibrée extractif 0,477 ; RAG 0,529 ; **RAG + vérification NLI 0,561**.
  8,1 s par question. Le LLM trouve 31 réponses sur 70 (extractif : 6) mais **s'abstient trop peu**
  (50 réponses sur 130 questions sans réponse). Les 20 questions indicatives (0,643) surestimaient.
  **D-022 acceptée** (modèle de référence, NLI dans le graphe, extractif par défaut) ; seuil
  d'abstention à régler avant le gel (séance 2).
- **Bilan complet de la période : `docs/DIAGNOSTIC_2026-11-23_au_2026-11-24.md`**, avec la démonstration pas à pas.

## Séance 2 (2026-11-26) : BM25, seuil d'abstention, corpus explicatif, fidélité

- **Vrai BM25** (D-024) : même découpage en mots que PostgreSQL, seule la formule change. Validation
  (809 questions) : rappel@5 / MRR — texte intégral PostgreSQL 0,518 / 0,334 ; BM25 0,585 / 0,447 ;
  **hybride BM25 + embeddings 0,602 / 0,469** (adopté) ; seuil extractif re-réglé sur le train : 0,71.
- **Seuil d'abstention du RAG** (D-025) : critère écrit **avant** le calcul (commit `03e88b0`), courbe
  couverture / erreur sur 200 questions du **train** → seuil NLI **0,85**. Validation : exactitude
  équilibrée **0,560**, 23 réponses fausses sur 40 (contre 35 sur 57), 4,2 s par question.
- **Corpus explicatif** (D-023) : 18 sources ouvertes (Wikipédia CC BY-SA, GOV.UK OGL, FAR domaine
  public, OMPI CC BY), 6 349 segments, index séparé, attribution affichée. Sur les questions CUAD, il
  n'aide pas (2 réponses sur 105 le citent ; 0,548) : **D-027 proposée** (mode « Expliquer un terme » séparé).
- **Fidélité** (D-026) : les 6 réponses avec un chiffre absent du passage cité sont toutes rejetées par
  le filtre NLI ; 50 réponses tirées pour l'annotation humaine (Sara et Ilyas).

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
| **D-012** | Modèle Transformer F2 ; critère | Legal-BERT small, poids atténué (CUAD), TF-IDF en référence (Sara) ; critère : rappel par annotation sous précision ≥ 0,50 (Sara), appliqué sur la validation ; choix : Transformer (durée, responsabilité), TF-IDF (résiliation) |
| **D-013** | CUAD + ContractNLI | Deux modèles (Sara) |
| **D-014** | Méthode NLI (F4) | Paires hypothèse-phrase + agrégation, seuils réglés sur le dev (Sara) |
| **D-015** | Embeddings et recherche hybride (F5) | bge-small-en-v1.5 ; texte intégral PostgreSQL + pgvector, fusion RRF (Sara) |
| **D-016** | LLM local (F5) | qwen3-vl:8b via Ollama (déjà présent), paramétrable ; qwen3:8b cible ; lien avec l'OCR (Sara) |
| **D-017** | Réglages de F5 | Exactitude équilibrée (choisie après l'échec de l'exactitude, sur la validation seulement) ; 5 passages ; citations vérifiées mot pour mot, ≥ 15 caractères, sinon abstention (Sara) |
| **D-018** | Protocole F3 et alertes v1 | 47 paires, grille, kappa, consensus ; règle v1 figée ; risque n°1 du cahier des charges → plan de repli : F3 présentée comme étude expérimentale si la faiblesse est confirmée (Sara) |
| **D-020** | Grille F3 | 3 étiquettes du cahier des charges (Sara) |
| **D-021** | Cahier des charges de référence | *En attente de l'encadrant* (comparaison V1/V2 : extension ou obligatoire) |
| **D-022** | LLM de référence et vérification NLI (F5) | qwen3-vl:8b-instruct ; vérification NLI dans le graphe RAG ; extractif par défaut, LLM sur demande « à vérifier » (Sara) |
| **D-023** | Corpus explicatif (F5) | 18 sources ouvertes, index séparé, attribution affichée (Sara) |
| **D-024** | Vrai BM25 (F5) | Hybride BM25 + embeddings ; seuil extractif re-réglé sur le train (Sara) |
| **D-025** | Seuil d'abstention du RAG | Critère A (exactitude équilibrée, train) → seuil NLI 0,85 (Sara) |
| **D-026** | Mesure de la fidélité | Référence humaine (50 réponses) + éléments critiques + NLI indicatif (Sara) |
| **D-027** | Place du corpus explicatif | *Proposée* : deux modes séparés (contrat / expliquer un terme) |
| **D-019** | Seuil confidentialité ; architecture F6 | 0,95 (exception au critère de D-012, différence de domaine NDA → contrats commerciaux) ; API + interface (Sara) |
| **D-009** | Confidentialité : segmentation, négatifs | Coupe aux lignes, sans nda-18, négatifs dans les NDA (Sara, 2026-11-23) ; annotation CUAD plus tard |

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
