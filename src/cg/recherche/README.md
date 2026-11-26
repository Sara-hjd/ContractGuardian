# `src/cg/recherche/` — recherche hybride et réponse avec citation ou abstention (F5)

Rôle : répondre à une question sur **un** contrat en **citant exactement** le texte du contrat
(page, positions), ou en **s'abstenant** s'il n'y a pas de réponse fiable. Jamais d'avis juridique.

## Fichiers

| Fichier | Contenu |
|---|---|
| `embeddings.py` | `Encodeur` (bge-small-en-v1.5, D-015) : texte → vecteur normalisé de 384 nombres ; préfixe pour les questions. |
| `indexer.py` | Script : calculer les vecteurs des segments de la base (seulement ceux qui n'en ont pas). |
| `hybride.py` | `rechercher` dans un contrat : par les mots (texte intégral PostgreSQL), par le sens (pgvector), fusion RRF ; chaque résultat garde sa provenance. |
| `extractive.py` | `repondre` : citer le meilleur segment tel quel, ou s'abstenir sous un seuil de similarité. |
| `llm.py` | Client du LLM local Ollama (D-016) : température 0, sans « réflexion », réponse JSON ; modèle = `CG_LLM_MODELE`. |
| `graphe.py` | RAG LangGraph : chercher → générer → **vérifier chaque citation mot pour mot** → répondre ou s'abstenir ; positions exactes des extraits. |
| `verification_nli.py` | Second contrôle (D-022) : le modèle NLI de F4 vérifie qu'un passage cité **implique** la réponse (seuil 0,5), sinon abstention. |
| `questions_cuad.py` | Jeu d'évaluation : questions CUAD posées aux contrats de la base, avec leurs segments de réponse. |

Base : `db/init/002_recherche.sql` (colonnes `tsv` et `embedding`, index GIN et HNSW).

## Utilisation

```bash
docker compose up -d                                   # base
PYTHONPATH=src .venv/bin/python -u -m cg.recherche.indexer          # vecteurs des segments
PYTHONPATH=src .venv/bin/python -u evaluation/evaluer_qr_f5.py      # recherche + extractif
PYTHONPATH=src .venv/bin/python -u evaluation/evaluer_rag_llm_f5.py --seuil-extractif S   # + LLM
CG_LLM_MODELE=qwen3:8b PYTHONPATH=src .venv/bin/python -u evaluation/evaluer_rag_llm_f5.py --seuil-extractif S
```

## Règles

- La recherche se fait **dans un seul contrat** ; chaque passage garde sa page et ses positions.
- Le LLM ne voit que les passages retrouvés ; une citation qui n'existe pas mot pour mot provoque
  une **abstention** (on ne montre jamais une citation non vérifiée).
- Le seuil d'abstention extractif est réglé sur des contrats du **train** ; les mesures sont faites
  sur la **validation** ; le test reste fermé.
