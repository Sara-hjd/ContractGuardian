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
| F1 | Ingestion PDF et provenance | Lire un contrat PDF et le découper en segments, chacun avec sa page et ses positions. | En cours (segmentation v1, extraction PDF PyMuPDF avec pages, alignement des annotations D-007) |
| F2 | Extraction de clauses | Repérer les clauses (durée, résiliation, responsabilité, confidentialité) : d'abord une baseline classique, puis un modèle Transformer. | En cours (données prêtes, baseline à faire) |
| F3 | Comparaison de paires de clauses | Comparer deux clauses pour signaler, avec prudence, une incohérence possible. | À faire |
| F4 | NLI | Inférence en langage naturel (implication / contradiction / neutre), évaluée sur ContractNLI. | À faire |
| F5 | Recherche hybride et RAG avec abstention | Recherche par mots-clés + recherche vectorielle, puis réponse citant le texte exact, ou abstention. | À faire |
| F6 | Interface analyste | Interface web (React) pour importer un contrat, consulter les clauses et poser des questions. | À faire |
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

*À compléter.*

Prérequis déjà identifiés : Homebrew, Python 3.11, Git, Docker Desktop, Node.js.

## Résultats

| Fonctionnalité | Jeu d'évaluation | Métrique | Baseline | Modèle final | Date |
|---|---|---|---|---|---|
| F2 Extraction | **Validation** CUAD (61 contrats, 8 253 segments) | Macro-F1 (3 familles) | Mots-clés : 0,247 · TF-IDF + rég. log. : **0,669** | — | 2026-11-22 |
| F2 · durée | Validation | F1 (P / R) | Mots-clés 0,180 (0,10 / 0,80) · TF-IDF **0,727** (0,79 / 0,67) | — | 2026-11-22 |
| F2 · résiliation | Validation | F1 (P / R) | Mots-clés 0,304 (0,21 / 0,53) · TF-IDF **0,521** (0,51 / 0,54) | — | 2026-11-22 |
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
