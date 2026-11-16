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

La traçabilité (F7) n'a pas de dossier à elle : c'est une règle que **tous** les modules
respectent, puisque chaque sortie référence un segment avec sa provenance.

**État actuel** : aucun sous-dossier n'existe encore. Chacun sera créé avec sa tâche.

## Règles pour ce dossier

- Chaque sous-dossier a son propre `README.md` : rôle, fichiers, utilisation.
- Chaque module commence par une docstring, et chaque fonction a une docstring au style
  Google ainsi que des annotations de type (voir [docs/CONVENTIONS.md](../../docs/CONVENTIONS.md)).
- Toute sortie référence un segment avec sa provenance (page, positions).
