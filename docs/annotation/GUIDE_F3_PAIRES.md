# Guide d'annotation F3 — paires de clauses

*Pour : Sara (Sara-hjd) et Ilyas (ILyas394). Version 1, 2026-11-24. À lire en entier avant de commencer.*

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

## Les quatre étiquettes

| Étiquette | Quand l'utiliser | Exemple **inventé** |
|---|---|---|
| `COMPATIBLES` | Les deux clauses s'appliquent ensemble sans tension : l'une précise l'autre, ou elles visent des situations clairement distinctes. | A : « Le contrat dure 2 ans. » B : « Il se renouvelle ensuite par périodes d'un an, sauf préavis de 60 jours. » |
| `A_VERIFIER` | Une **tension possible** qu'un lecteur devrait regarder : exception qui limite fortement l'autre clause, chiffres ou délais différents pour un même sujet, articulation pas claire. | A : « La responsabilité est plafonnée aux sommes payées. » B : « Aucune limite ne s'applique en cas de violation de la confidentialité. » |
| `CONTRADICTION_APPARENTE` | Les deux textes semblent dire des choses **incompatibles sur le même point**, sans règle d'articulation visible (« nonobstant », « sauf », « sous réserve de »…). | A : « Le contrat ne peut pas être résilié avant 3 ans. » B : « Chaque partie peut résilier à tout moment avec un préavis de 30 jours. » |
| `NON_COMPARABLE` | Impossible de juger : un des segments est coupé ou illisible, ou les deux passages ne portent pas sur le même sujet. | Une clause B réduite à un titre de section. |

**Règles de décision**
1. Lire **les deux clauses en entier**, puis se demander : « un lecteur pressé pourrait-il être induit
   en erreur s'il ne lisait qu'une des deux ? ». Si oui → au moins `A_VERIFIER`.
2. Une exception **explicitement annoncée** (« sauf », « nonobstant l'article X ») n'est **pas** une
   contradiction : c'est en général `COMPATIBLES` (exception claire) ou `A_VERIFIER` (exception large).
3. En cas d'hésitation entre `A_VERIFIER` et `CONTRADICTION_APPARENTE` → `A_VERIFIER` (prudence).
4. Ne pas chercher d'informations ailleurs dans le contrat : juger **ces deux passages**.
5. **Ne pas se concerter** avant d'avoir fini tous les deux (sinon le kappa ne mesure plus rien).

## Format du fichier (une ligne par paire)

| Colonne | Contenu |
|---|---|
| `id_paire` | `P01` … `P47` |
| `annotateur` | votre identifiant GitHub |
| `etiquette` | une des quatre étiquettes, **exactement** comme écrites ci-dessus |
| `date` | AAAA-MM-JJ |

**Interdit (règle 5, D-003)** : copier du texte de contrat dans le fichier, ou ajouter une colonne de
commentaire. Vos remarques éventuelles vont dans un document personnel, hors du dépôt.

## Après l'annotation

```bash
PYTHONPATH=src .venv/bin/python -m cg.annotation.accord data/annotations/f3_paires/annotations_Sara-hjd.csv data/annotations/f3_paires/annotations_ILyas394.csv
.venv/bin/python -m pytest tests/test_annotations.py     # vérifie qu'aucun texte n'a été copié
```

Le script donne le kappa (4 étiquettes, et « alerte oui / non » = `A_VERIFIER` ou
`CONTRADICTION_APPARENTE`), la matrice et la liste des désaccords. Ensuite : discuter les désaccords,
fixer une **étiquette de référence** par paire (fichier `reference.csv`, même format, annotateur =
`consensus`), et seulement alors évaluer les alertes.
