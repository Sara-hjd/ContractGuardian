# `src/cg/datasets/` — jeux de données d'entraînement et d'évaluation

Rôle : préparer les données de CUAD pour la baseline de F2 : lire les annotations, fixer les
jeux train / val / test (D-004), puis étiqueter les segments (D-001) par famille de clauses.

## Fichiers

| Fichier | Contenu |
|---|---|
| `cuad.py` | `FAMILLES` (nos 9 catégories CUAD), `charger_cuad` (textes + annotations, positions vérifiées), `projeter_annotations` (règle de chevauchement). |
| `splits.py` | Construire, vérifier, écrire et lire le fichier des splits. |
| `creer_splits.py` | Script : crée `data/splits/cuad_v1_splits.json`. |
| `preparer_segments.py` | Script : crée `data/processed/cuad_segments_v1.jsonl` et affiche les statistiques. |

## Utilisation (depuis la racine, avec le `.venv`)

```bash
PYTHONPATH=src .venv/bin/python -m cg.datasets.creer_splits
PYTHONPATH=src .venv/bin/python -m cg.datasets.preparer_segments
```

Prérequis : `data/raw/cuad/CUAD_v1/` (Zenodo) et `data/raw/cuad_official/data.zip` (GitHub),
voir `docs/data_provenance.md`.

## Règles fixées à l'avance

- **Splits (D-004)** : test = `test.json` officiel ; validation = 15 % du train officiel, tirés
  par contrat avec la graine 42. Ne pas changer la graine pour améliorer un résultat.
- **Étiquetage** : un segment reçoit la catégorie C si son chevauchement avec une annotation de C
  atteint `min(20, longueur de l'annotation)` caractères. Un segment peut avoir plusieurs familles.

## Ce qui est versionné ou non

- `data/splits/cuad_v1_splits.json` : titres seulement (voir D-005).
- `data/processed/cuad_segments_v1.jsonl` : contient le texte des contrats → **jamais commité**.
