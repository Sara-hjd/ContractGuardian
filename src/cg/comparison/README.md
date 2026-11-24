# `src/cg/comparison/` — alertes prudentes entre clauses (F3)

Rôle : pour deux clauses d'un même contrat, signaler un **point à vérifier** (jamais « contradiction »,
jamais d'avis juridique), avec ses raisons et la provenance des deux clauses.

| Fichier | Contenu |
|---|---|
| `alertes.py` | Règle v1 (D-018) : R1 NLI (modèle de F4, « contredit » ≥ 0,5), R2 délais différents, R3 formule d'exception. |
| `predire_alertes.py` | Script : décisions sur les paires de `data/annotations/f3_paires/paires_v1.csv` → `docs/analyses/f3_alertes_v1_predictions.csv` (sans texte). |

La règle v1 a été **figée le 2026-11-24, avant les annotations humaines** ; elle est évaluée sur les
étiquettes de consensus de Sara et Ilyas (`docs/annotation/GUIDE_F3_PAIRES.md`).
