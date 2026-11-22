# `src/cg/extraction/` — extraction de clauses (F2)

Rôle : dire, pour chaque segment (D-001), s'il relève de chacune de nos familles de clauses
(durée, résiliation, responsabilité). Tâche **multi-étiquette** : un segment peut relever de
plusieurs familles, ou d'aucune (environ 97 % des segments).

## Fichiers

| Fichier | Contenu |
|---|---|
| `mots_cles.py` | Baseline 1 : `MOTS_CLES` (motifs écrits à la main et justifiés), `predire_mots_cles`. |
| `tfidf.py` | Baseline 2 : vectoriseur TF-IDF, régression logistique pondérée (`class_weight="balanced"`), mots les plus lourds. |
| `metriques.py` | Précision, rappel, F1 par famille, macro-F1 ; choix du seuil (sur la validation seulement). |

L'entraînement se lance avec `training/baselines_extraction.py` (voir ce fichier).

## Règles

- **Pas d'exactitude globale** : un modèle qui ne trouve rien aurait 97 % d'exactitude.
- **Réglages sur la validation seulement** (hyperparamètres, seuils) ; le test reste fermé
  (`cg.datasets.segments.charger_segments` refuse de le charger sans `ouvrir_test=True`).
- **Mots-clés figés** : la liste de `mots_cles.py` a été écrite avant toute évaluation et
  n'est pas modifiée en fonction des résultats.
- Chaque prédiction porte sur un segment qui garde sa provenance (titre, début, fin).

## Exemple

```python
from cg.extraction.mots_cles import predire_mots_cles

predire_mots_cles(["In no event shall either party be liable for consequential damages."])
# {'durée': array([False]), 'résiliation': array([False]), 'responsabilité': array([ True])}
```
