# Guide d'annotation F3 — paires de clauses

*Pour : Sara (Sara-hjd) et Ilyas (ILyas394). **Version 2, 2026-11-25** : grille alignée sur les
**trois étiquettes du cahier des charges** (section 6, F3 ; décision D-020). La version 1 (quatre
étiquettes) n'a servi à aucune annotation. À lire en entier avant de commencer.*

## But

ContractGuardian doit signaler **avec prudence** des points à vérifier entre deux clauses d'un même
contrat (F3). Pour mesurer si ses alertes sont utiles, il faut une **référence humaine** : vous
deux, **indépendamment**, donnez une étiquette à chacune des **47 paires**. Votre accord est mesuré
par le **kappa de Cohen** ; les alertes du système seront ensuite évaluées sur vos étiquettes.

**Ce n'est pas un avis juridique** : vous jugez, en lecteurs attentifs, si les deux textes **peuvent
se lire ensemble sans tension**, pas ce que dirait un juge.

## Matériel

- `data/annotations/f3_paires/paires_v1.csv` : les références des paires (commité).
- `data/processed/f3_paires_a_lire.md` : le **texte** des deux clauses de chaque paire (local,
  **jamais commité** ; le régénérer avec `PYTHONPATH=src .venv/bin/python -m cg.annotation.creer_paires_f3`).
- Votre fichier : copier `data/annotations/f3_paires/MODELE_annotations.csv` en
  `annotations_<votre-identifiant-GitHub>.csv` (par exemple `annotations_Sara-hjd.csv`).

## Les trois étiquettes (cahier des charges, F3)

| Étiquette | Quand l'utiliser | Exemple **inventé** |
|---|---|---|
| `POTENTIELLEMENT_INCOMPATIBLE` | Les deux clauses peuvent **se contredire ou se limiter fortement** sur un même point : délais ou montants différents pour le même sujet, exception qui vide l'autre clause de son sens, articulation absente ou peu claire. **C'est l'alerte.** | A : « Le contrat ne peut pas être résilié avant 3 ans. » B : « Chaque partie peut résilier à tout moment avec 30 jours de préavis. » |
| `COMPATIBLE` | Les deux clauses s'appliquent ensemble **sans tension** : l'une précise l'autre, ou elles visent des situations clairement distinctes, ou une exception est explicitement et clairement délimitée. | A : « Le contrat dure 2 ans. » B : « Il se renouvelle ensuite par périodes d'un an, sauf préavis de 60 jours. » |
| `INFORMATION_INSUFFISANTE` | **Impossible de juger** avec ces deux passages : un segment est coupé, illisible ou réduit à un titre ; ou les deux passages ne portent pas sur le même sujet ; ou il faudrait lire une autre partie du contrat pour trancher. | Une clause B réduite à un titre de section. |

**Règles de décision**
1. Lire **les deux clauses en entier**, puis se demander : « un lecteur pressé pourrait-il être induit
   en erreur s'il ne lisait qu'une des deux ? ». Si oui → `POTENTIELLEMENT_INCOMPATIBLE`.
2. Une exception **explicitement annoncée et précise** (« sauf », « nonobstant l'article X ») est en
   général `COMPATIBLE` ; si l'exception est **large** au point de limiter fortement l'autre clause,
   → `POTENTIELLEMENT_INCOMPATIBLE`.
3. En cas d'hésitation entre `COMPATIBLE` et `POTENTIELLEMENT_INCOMPATIBLE` →
   `POTENTIELLEMENT_INCOMPATIBLE` (prudence : c'est un point **à vérifier**, pas un verdict).
4. `INFORMATION_INSUFFISANTE` seulement si l'on ne **peut pas** juger avec ces deux passages ; ne pas
   l'utiliser pour éviter une décision difficile.
5. Ne pas chercher d'informations ailleurs dans le contrat : juger **ces deux passages**.
6. **Ne pas se concerter** avant d'avoir fini tous les deux (sinon le kappa ne mesure plus rien).

## Format du fichier (une ligne par paire)

| Colonne | Contenu |
|---|---|
| `id_paire` | `P01` … `P47` |
| `annotateur` | votre identifiant GitHub |
| `etiquette` | une des trois étiquettes, **exactement** comme écrites ci-dessus |
| `date` | AAAA-MM-JJ |

**Interdit (règle 5, D-003)** : copier du texte de contrat dans le fichier, ou ajouter une colonne de
commentaire. Vos remarques éventuelles vont dans un document personnel, hors du dépôt.

## Après l'annotation

```bash
PYTHONPATH=src .venv/bin/python -m cg.annotation.accord data/annotations/f3_paires/annotations_Sara-hjd.csv data/annotations/f3_paires/annotations_ILyas394.csv
.venv/bin/python -m pytest tests/test_annotations.py     # vérifie la grille et l'absence de texte copié
```

Le script donne le kappa (3 étiquettes, et « alerte oui / non » = `POTENTIELLEMENT_INCOMPATIBLE`),
la matrice et la liste des désaccords. Ensuite : discuter les désaccords, fixer une **étiquette de
référence** par paire (fichier `reference.csv`, même format, annotateur = `consensus`), et seulement
alors évaluer les alertes.
