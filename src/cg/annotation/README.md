# `src/cg/annotation/` — annotations humaines (D-003)

Rôle : préparer et contrôler les annotations **faites par Sara et Ilyas** (jamais par Claude) :
paires de clauses de F3, questions de F5, accord entre annotateurs. Les fichiers de
`data/annotations/` ne contiennent **que des références** (contrat, page, positions, étiquettes),
jamais de texte de contrat (vérifié par `tests/test_annotations.py`).

| Fichier | Contenu |
|---|---|
| `creer_paires_f3.py` | Script : 47 paires candidates (4 types, contrats de validation) → références commitées + fichier de lecture local (non commité). |
| `accord.py` | Kappa de Cohen (écrit à la main, vérifié contre scikit-learn) ; script de comparaison de deux annotateurs. |
| `positions.py` | Outil : page et positions d'un extrait copié d'un contrat (pour les questions de F5). |

Guides : `docs/annotation/GUIDE_F3_PAIRES.md`, `docs/annotation/GUIDE_F5_QUESTIONS.md`.
