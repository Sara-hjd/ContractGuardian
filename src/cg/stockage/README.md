# `src/cg/stockage/` — base de données de l'application (PostgreSQL + pgvector)

Rôle : garder, pour chaque contrat importé, son **texte complet**, ses **pages** et ses
**segments** avec leur provenance (règle 1, D-001), puis les **résultats** d'analyse rattachés aux
segments. C'est le « monde de l'application » du README (contrats de l'utilisateur), distinct
des données d'entraînement (`data/`).

## Fichiers

| Fichier | Contenu |
|---|---|
| `connexion.py` | `lire_configuration` (variables d'environnement, sinon `.env`), `connecter`. |
| `depot.py` | `enregistrer_document` (une transaction), `lire_segments`, `compter_segments_non_tracables` (vérification **en SQL**), `supprimer_contrat`. |
| `ingerer_pdf.py` | Script : importer un PDF (extraction par blocs, D-008) et vérifier la traçabilité. |

Schéma : `db/init/001_schema.sql` (tables `contrats`, `pages`, `segments`, `resultats` ;
extension `vector` activée, colonne de vecteurs ajoutée avec F5). Décision : D-010.

## Utilisation

```bash
open -a Docker                      # Docker Desktop doit tourner
cp .env.example .env                # une seule fois, puis remplacer le mot de passe
docker compose up -d                # démarre la base (127.0.0.1:5432)
PYTHONPATH=src .venv/bin/python -m cg.stockage.ingerer_pdf chemin/contrat.pdf
docker compose down                 # arrête la base ; les données restent dans le volume
```

## Règles

- Le fichier `.env` (mot de passe) n'est **jamais** commité ; seul `.env.example` l'est.
- La base contient du texte de contrats : elle vit dans un volume Docker local, jamais dans le dépôt.
- Positions en caractères, comme en Python : `substring(texte from debut + 1 for fin - debut)`
  en SQL correspond à `texte[debut:fin]` en Python.
