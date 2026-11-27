# `cg.explicatif` — corpus documentaire explicatif (F5, D-023)

Petit corpus de **documents publics sous licence ouverte** (glossaires, guides) qui expliquent les
notions de durée, résiliation, responsabilité et confidentialité. Il sert de **contexte** au RAG, dans
un index **séparé** des contrats ; il n'est **pas** une donnée d'entraînement (règle 3) et ne dit pas le
droit applicable à un contrat.

| Fichier | Rôle |
|---|---|
| `sources.py` | La liste des 18 sources validées par Sara (titre, URL, éditeur, licence, attribution). Aucun texte. |
| `collecte.py` | Télécharge chaque source dans `data/raw/explicatif/` (jamais commité) et écrit `manifeste.json` : date de consultation, empreinte SHA-256, révision Wikipédia. |
| `texte.py` | Convertit chaque source en texte (API Wikipédia, HTML GOV.UK et FAR, PDF par blocs) et la découpe en segments avec **positions, page (PDF) et section**. |
| `indexer.py` | Remplit `sources_explicatives` et `segments_explicatifs` (`db/init/003_explicatif.sql`) avec les vecteurs. |
| `recherche.py` | Recherche hybride **BM25 + embeddings** (fusion RRF) dans tout le corpus ; chaque résultat porte son attribution. |

## Reconstruire le corpus

```bash
docker exec -i cg-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < db/init/003_explicatif.sql   # une fois
PYTHONPATH=src .venv/bin/python -m cg.explicatif.collecte    # ≈ 2 min (pause de 3 s entre deux requêtes)
PYTHONPATH=src .venv/bin/python -m cg.explicatif.indexer     # ≈ 2 min, 6 349 segments
```

## Règles

- Dans le RAG (`cg.recherche.graphe`), les passages explicatifs sont montrés au LLM dans un **bloc
  séparé** (E1, E2, E3) ; une réponse doit toujours citer **le contrat** ; un extrait explicatif cité
  est vérifié mot pour mot et affiché avec son **attribution** (source, licence, page ou section).
- Les sources CC BY-SA (Wikipédia) imposent de citer les auteurs et la licence : c'est le champ
  `attribution`, affiché par l'interface sous chaque extrait.
