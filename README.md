# ContractGuardian

Outil d'aide à la lecture de **contrats commerciaux en anglais** : extraction des clauses clés
(durée, résiliation, responsabilité, confidentialité), détection prudente d'incohérences entre
clauses, et questions-réponses avec **citation exacte** du contrat ou **abstention**.

Projet de fin d'année (PFA), EMSI.

> ⚠️ **Avertissement** : ContractGuardian est un **outil d'aide à la lecture**.
> Il ne fournit **pas d'avis juridique** et ne remplace pas un professionnel du droit.
> Chaque résultat renvoie au passage exact du contrat pour être vérifié par un humain.

## Fonctionnalités

| ID | Fonctionnalité | Description | Statut |
|---|---|---|---|
| F1 | Ingestion PDF et provenance | Lire un contrat PDF et le découper en segments, chacun avec sa page et ses positions. | En cours (extraction PDF PyMuPDF par blocs avec pages, alignement D-007, base PostgreSQL + pgvector dans Docker) |
| F2 | Extraction de clauses | Repérer les clauses (durée, résiliation, responsabilité, confidentialité) : d'abord une baseline classique, puis un modèle Transformer. | En cours (baselines mots-clés et TF-IDF sur la validation ; segments PDF ; confidentialité via ContractNLI) |
| F3 | Comparaison de paires de clauses | Comparer deux clauses pour signaler, avec prudence, une incohérence possible. | En cours (47 paires et grille prêtes, annotation par Sara et Ilyas ; règle d'alerte v1 figée) |
| F4 | NLI | Inférence en langage naturel (implication / contradiction / neutre), évaluée sur ContractNLI. | En cours (Transformer sur paires hypothèse-phrase, dev ; D-014 proposée) |
| F5 | Recherche hybride et RAG avec abstention | Recherche par mots-clés + recherche vectorielle, puis réponse citant le texte exact, ou abstention. | En cours (vrai BM25 + embeddings ; seuil d'abstention réglé sur le train ; corpus explicatif de 18 sources indexé à part ; fidélité mesurée automatiquement, annotation humaine à faire) |
| F6 | Interface analyste | Interface web (React) pour importer un contrat, consulter les clauses et poser des questions. | En cours (API FastAPI + interface React minimale, essai de bout en bout réussi ; voir le diagnostic pour la démonstration) |
| F7 | Traçabilité | Chaque sortie renvoie au segment source (page, positions) ; chaque expérience est suivie dans MLflow. | En cours (test de traçabilité des segments) |

## Architecture (prévue)

```
               ┌──────────────────────────┐
               │  Interface React (F6)    │
               └────────────┬─────────────┘
                            │ HTTP (JSON)
               ┌────────────▼─────────────┐
               │       API FastAPI        │
               └────────────┬─────────────┘
                            │
   ┌────────────┬───────────┼────────────┬──────────────────┐
   ▼            ▼           ▼            ▼                  ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────────────────┐
│Ingest. │ │Extraction│ │Comparais.│ │  NLI   │ │ Recherche + RAG    │
│PDF (F1)│ │clauses   │ │clauses   │ │  (F4)  │ │ avec abstention    │
│PyMuPDF │ │  (F2)    │ │  (F3)    │ │        │ │       (F5)         │
└───┬────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ └─────────┬──────────┘
    │           │            │           │                │
    └───────────┴────────────┴─────┬─────┴────────────────┘
                                   ▼
               ┌──────────────────────────────────────┐
               │ PostgreSQL + pgvector (Docker)       │
               │ contrats, segments + provenance (F7),│
               │ résultats, vecteurs                  │
               └──────────────────────────────────────┘

  Hors application : entraînement et évaluation des modèles
  (scikit-learn, PyTorch/Transformers), suivis dans MLflow.
```

## Données : deux mondes séparés

| | Données d'entraînement et d'évaluation | Base de l'application |
|---|---|---|
| **Contenu** | CUAD, ContractNLI, annotations humaines sur contrats réels | Contrats importés par l'utilisateur, segments, résultats d'analyse, vecteurs |
| **Stockage** | Fichiers dans `data/`, non versionnés, sauf `data/annotations/` (références sans texte, D-003) | PostgreSQL + pgvector, dans Docker |
| **Usage** | Entraîner et évaluer les modèles (découpage entraînement / validation / test) | Faire fonctionner l'outil |
| **Règle** | Le jeu de test ne sert **jamais** à régler un modèle. Aucune donnée synthétique. | Chaque résultat garde sa provenance (page, positions). |

## Structure du dépôt (prévue, susceptible d'évoluer)

```
ContractGuardian/
├── CLAUDE.md             # Règles de travail lues par Claude Code
├── README.md             # Ce fichier
├── .gitignore
├── docs/                 # Documentation du projet
│   ├── CONVENTIONS.md
│   ├── PROGRESS.md
│   └── decisions.md
├── src/cg/               # Code Python (un README.md par sous-dossier)
│   ├── ingestion/        # F1
│   ├── extraction/       # F2
│   ├── comparison/       # F3
│   ├── nli/              # F4
│   ├── retrieval/        # F5
│   └── api/              # API FastAPI
├── frontend/             # Interface React (F6)
├── training/             # Scripts d'entraînement des modèles
├── evaluation/           # Scripts d'évaluation (métriques, rapports)
├── tests/                # Tests automatisés (pytest)
├── notebooks/            # Explorations
├── data/
│   ├── raw/              # Données brutes : CUAD, ContractNLI, PDF (non versionnées)
│   ├── processed/        # Données préparées (non versionnées)
│   └── annotations/      # Nos annotations : références seulement, sans texte (versionnées, D-003)
├── models/               # Modèles entraînés (non versionnés)
└── docker-compose.yml    # PostgreSQL + pgvector
```

## Installation (macOS)

Prérequis : Homebrew, Python 3.11, Git, Docker Desktop, Node.js, Ollama.

```bash
python3.11 -m venv .venv && source .venv/bin/activate     # Python 3.11 (jamais le python3 du système)
python -m pip install -r requirements.txt
cp .env.example .env                                     # puis choisir un mot de passe
open -a Docker && docker compose up -d                   # PostgreSQL 17 + pgvector
python -m pytest                                         # tests (certains sont ignorés sans données)
```

**Données** (non versionnées, voir `docs/data_provenance.md`) : CUAD v1 dans `data/raw/cuad/`,
`data.zip` officiel dans `data/raw/cuad_official/`, ContractNLI dans `data/raw/contractnli/`.
**Préparation et modèles** (dans l'ordre, avec `PYTHONPATH=src`) :
`cg.datasets.creer_splits`, `cg.datasets.preparer_segments`, `cg.datasets.preparer_segments_pdf`,
`cg.datasets.preparer_segments_contractnli`, `training/transformer_extraction.py` (avec et sans
`--poids-racine`), `training/sauvegarder_tfidf_resiliation.py`, `training/nli_contractnli.py`,
`cg.recherche.indexer`. Les modèles sont écrits dans `models/` (non versionné).

**Application** :

```bash
open -a Ollama                                            # LLM local (CG_LLM_MODELE, défaut qwen3-vl:8b)
PYTHONPATH=src python -m uvicorn cg.api.app:app --port 8000
cd frontend && npm install && npm run dev                 # http://localhost:5173
```

## Résultats

| Fonctionnalité | Jeu d'évaluation | Métrique | Baseline | Modèle final | Date |
|---|---|---|---|---|---|
| F2 Extraction | **Validation** CUAD (61 contrats, 8 253 segments) | Macro-F1 (3 familles) | Mots-clés : 0,247 · TF-IDF + rég. log. : **0,669** | — | 2026-11-22 |
| F2 · durée | Validation | F1 (P / R) | Mots-clés 0,180 (0,10 / 0,80) · TF-IDF **0,727** (0,79 / 0,67) | — | 2026-11-22 |
| F2 · résiliation | Validation | F1 (P / R) | Mots-clés 0,304 (0,21 / 0,53) · TF-IDF **0,521** (0,51 / 0,54) | — | 2026-11-22 |
| F2 Extraction (segments PDF, blocs) | **Validation** (61 contrats, 11 465 segments PDF) | Macro-F1 · macro rappel par annotation | TF-IDF entraîné sur CUAD : 0,643 · 0,719 — entraîné sur PDF : **0,656 · 0,724** | — | 2026-11-23 |
| F2 · confidentialité | **Dev** ContractNLI (61 NDA, 2 872 segments) | F1 (P / R) | Mots-clés : 0,580 (0,43 / 0,88) · TF-IDF : 0,830 | Transformer (legal-bert-small) : **0,862** (0,85 / 0,87) | 2026-11-23 |
| F2 Extraction (segments PDF, 3 familles) | **Validation** | Macro-F1 · macro rappel par annotation | TF-IDF : 0,656 · 0,724 | Transformer (legal-bert-small, poids atténué) : 0,625 · **0,773** | 2026-11-23 |
| F4 NLI (ContractNLI) | **Dev** (61 NDA, 1 037 couples) | Exactitude · macro-F1 · évidences F1 | Classe majoritaire : 0,681 · 0,633 · — | Transformer (paires) : **0,778 · 0,717 · 0,630** | 2026-11-23 |
| F5 Recherche (questions CUAD) | **Validation** (61 contrats, 809 questions avec réponse) | rappel@1 · @3 · @5 · @10 · MRR | Texte intégral PostgreSQL : 0,208 · 0,417 · 0,518 · 0,638 · 0,334 ; BM25 : 0,347 · 0,519 · 0,585 · 0,672 · 0,447 ; embeddings : 0,313 · 0,468 · 0,543 · 0,642 · 0,411 ; hybride PostgreSQL : 0,323 · 0,503 · 0,586 · 0,682 · 0,433 | **Hybride BM25 + embeddings : 0,368 · 0,532 · 0,602 · 0,696 · 0,469** | 2026-11-26 |
| F5 Réponse avec abstention | **Validation** (2 492 questions) | Exactitude équilibrée | Toujours s'abstenir : 0,500 | Extractif : 0,521 | 2026-11-23 |
| F5 RAG + LLM local (**référence, séance 2**) | **Validation**, 200 questions (70 avec réponse) | Exactitude équilibrée · réponses fausses / données | Extractif (BM25) : 0,480 · 32 sur 41 | RAG hybride BM25 + NLI 0,85 (réglé sur le train) : **0,560 · 23 sur 40** (4,2 s par question) ; avec corpus explicatif : 0,548 · 25 sur 42 (9,8 s) | 2026-11-26 |
| F5 RAG + LLM local (séance 1) | **Validation**, 200 questions (70 avec réponse) | Exactitude équilibrée · réponses fausses / données | Extractif : 0,477 · 24 sur 30 | RAG qwen3-vl:8b-instruct : 0,529 · 71 sur 102 ; **+ vérification NLI : 0,561 · 35 sur 57** (8,1 s par question) | 2026-11-26 |
| F5 RAG + LLM local (indicatif, remplacé) | Validation, 20 questions | Exactitude équilibrée · réponses fausses | Extractif : 0,423 · 2 sur 2 | RAG qwen3-vl:8b : 0,643 · 0 sur 2 | 2026-11-24 |
| F2 · responsabilité | Validation | F1 (P / R) | Mots-clés 0,257 (0,16 / 0,71) · TF-IDF **0,758** (0,89 / 0,66) | — | 2026-11-22 |

*Chiffres de **validation**, optimistes car les seuils y sont réglés (D-006). Le jeu de test n'a
pas été ouvert. Tâche différente de l'article CUAD : chiffres non comparables (D-004).*

## Documentation

- [CLAUDE.md](CLAUDE.md) : règles de travail du projet.
- [docs/CONVENTIONS.md](docs/CONVENTIONS.md) : conventions de code et de Git, définition de « terminé ».
- [docs/PROGRESS.md](docs/PROGRESS.md) : journal des séances et bilans hebdomadaires.
- [docs/decisions.md](docs/decisions.md) : registre des décisions techniques.

## Équipe

- **Sara-hjd**
- **ILyas394**
- **Encadrant** : *à compléter*
