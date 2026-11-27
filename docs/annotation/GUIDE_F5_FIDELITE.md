# Guide d'annotation F5 — fidélité des réponses du RAG

*Pour : Sara (Sara-hjd) et Ilyas (ILyas394). Version 1, 2026-11-26 (décision D-026). À lire en entier
avant de commencer. Durée estimée : environ 1 heure pour 50 réponses.*

## But

Le RAG répond à une question sur un contrat en **citant** des passages. On veut savoir si ses réponses
sont **fidèles** : est-ce que **tout** ce que dit la réponse se trouve dans les passages qu'elle cite ?
Vous deux, **indépendamment**, jugez **50 réponses** tirées au hasard (graine 0) parmi les réponses
vérifiées sur la validation. Votre accord est mesuré par le **kappa de Cohen**.

**Ce n'est pas la même question que « la réponse est-elle juste ? »** :
- une réponse peut être **fidèle** mais ne pas répondre à la question (elle cite un passage hors sujet,
  et le dit correctement) ;
- une réponse peut sembler juste mais être **infidèle** (elle ajoute un délai, un montant ou une
  condition qui ne sont **pas** dans le passage cité).

Ici, **on ne juge que la fidélité** : réponse contre passages cités. Ce n'est pas un avis juridique.

## Matériel

- `data/processed/f5_fidelite_a_lire.md` : pour chaque réponse (R01 à R50), la réponse du système et
  le texte des passages cités (local, **jamais commité** ; le régénérer avec
  `PYTHONPATH=src .venv/bin/python -u evaluation/mesurer_fidelite_f5.py --configuration "…"`).
- `data/annotations/f5_fidelite/reponses_v1.csv` : les références des 50 réponses (commité, sans texte).
- Votre fichier : copier `data/annotations/f5_fidelite/MODELE_annotations.csv` en
  `annotations_<votre-identifiant-GitHub>.csv` (par exemple `annotations_Sara-hjd.csv`).

## Les trois étiquettes

| Étiquette | Quand l'utiliser | Exemple **inventé** (passage : « Either party may terminate this Agreement upon thirty (30) days prior written notice. ») |
|---|---|---|
| `FIDELE` | **Tout** ce que dit la réponse est dans les passages cités (une reformulation fidèle est permise). | « Each party can end the agreement with 30 days' written notice. » |
| `PARTIELLEMENT_FIDELE` | L'essentiel est dans les passages, mais **un élément** n'y est pas, ou la réponse **généralise** (« always », « any time ») ou **omet une condition importante** (« written »). | « Each party can end the agreement with 30 days' notice, without paying any fee. » (la question des frais n'est pas dans le passage) |
| `NON_FIDELE` | La réponse **contredit** les passages ou **invente** l'élément principal (délai, montant, partie, condition). | « Only the Supplier may terminate, with 60 days' notice. » |

**Règles de décision**
1. Lire la réponse, puis **chercher chaque affirmation** dans les passages cités. Ne pas utiliser ce que
   vous savez par ailleurs sur le contrat ou sur le droit.
2. Une **reformulation** est fidèle si elle garde le sens exact (« terminate » ≈ « end »). Un changement
   de **chiffre, de partie, de négation** (« may » / « may not ») ou de **condition** ne l'est pas.
3. Hésitation entre `FIDELE` et `PARTIELLEMENT_FIDELE` → `PARTIELLEMENT_FIDELE` (prudence).
4. Hésitation entre `PARTIELLEMENT_FIDELE` et `NON_FIDELE` : `NON_FIDELE` si l'élément faux ou inventé
   est **celui qui répond à la question** (le délai pour une question sur le préavis, par exemple).
5. Une réponse **vide ou incompréhensible** → `NON_FIDELE`.
6. **Ne pas se concerter** avant d'avoir fini tous les deux (sinon le kappa ne mesure plus rien).

## Format du fichier (une ligne par réponse)

| Colonne | Contenu |
|---|---|
| `id_reponse` | `R01` … `R50` |
| `annotateur` | votre identifiant GitHub |
| `etiquette` | une des trois étiquettes, **exactement** comme écrites ci-dessus |
| `date` | AAAA-MM-JJ |

**Interdit (règle 5, D-003)** : copier du texte de contrat ou de réponse dans le fichier, ou ajouter une
colonne de commentaire. Vos remarques éventuelles vont dans un document personnel, hors du dépôt.

## Après l'annotation

```bash
PYTHONPATH=src .venv/bin/python -m cg.annotation.accord data/annotations/f5_fidelite/annotations_Sara-hjd.csv data/annotations/f5_fidelite/annotations_ILyas394.csv --grille f5
.venv/bin/python -m pytest tests/test_annotations.py     # vérifie la grille et l'absence de texte copié
```

Le script donne le kappa (3 étiquettes, et « fidèle oui / non »), la matrice et les désaccords. Ensuite :
discuter les désaccords, fixer une **étiquette de référence** par réponse (`reference.csv`, même format,
annotateur = `consensus`). Le taux de fidélité sera rapporté avec son intervalle de confiance (environ
± 14 points pour 50 réponses).
