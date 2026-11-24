# `src/cg/` — le code de ContractGuardian

`cg` (pour **C**ontract**G**uardian) est le **paquet Python principal** du projet.
Tout le code de l'application y vit : lecture des PDF, extraction de clauses, comparaison,
NLI, recherche, API.

Ce qui n'est **pas** ici :
- les scripts d'entraînement → `training/`
- les scripts d'évaluation → `evaluation/`
- les explorations → `notebooks/`
- les tests → `tests/`
- l'interface React → `frontend/`

## Sous-dossiers prévus

| Dossier | Fonctionnalité | Rôle |
|---|---|---|
| `ingestion/` | F1 | Lire un PDF et le découper en segments avec leur provenance (page, positions). |
| `extraction/` | F2 | Repérer les clauses : durée, résiliation, responsabilité, confidentialité. |
| `comparison/` | F3 | Comparer deux clauses pour signaler une incohérence possible. |
| `nli/` | F4 | Inférence en langage naturel (implication / contradiction / neutre). |
| `retrieval/` | F5 | Recherche hybride et réponses avec citation exacte ou abstention. |
| `api/` | F6 | API FastAPI utilisée par l'interface. |
| `datasets/` | F2 (données) | Lire CUAD, fixer les splits (D-004), étiqueter les segments par famille. |
| `stockage/` | F1, F7 | Base PostgreSQL + pgvector : contrats, pages, segments, résultats. |
| `recherche/` | F5 | Recherche hybride, réponse extractive, RAG LangGraph avec LLM local. |
| `annotation/` | F3, F5 | Préparer et contrôler les annotations humaines (paires, questions), kappa de Cohen. |

La traçabilité (F7) n'a pas de dossier à elle : c'est une règle que **tous** les modules
respectent, puisque chaque sortie référence un segment avec sa provenance.

**État actuel** (2026-11-22) : `ingestion/` (segmentation v1 du texte CUAD, pas encore de PDF),
`datasets/` et `extraction/` (baselines) existent. Les autres seront créés avec leur tâche.

**Lancer un module** depuis la racine, avec le `.venv` : `PYTHONPATH=src .venv/bin/python -m cg.<module>`
(`PYTHONPATH=src` indique à Python où trouver le paquet `cg`).

## Règles pour ce dossier

- Chaque sous-dossier a son propre `README.md` : rôle, fichiers, utilisation.
- Chaque module commence par une docstring, et chaque fonction a une docstring au style
  Google ainsi que des annotations de type (voir [docs/CONVENTIONS.md](../../docs/CONVENTIONS.md)).
- Toute sortie référence un segment avec sa provenance (page, positions).
