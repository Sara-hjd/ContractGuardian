# Vérification de l'extraction PDF avec PyMuPDF (étape 2, début)

*2026-11-23. PyMuPDF 1.28.2. Contrats du **train** uniquement (le test n'est pas touché).
Aucun extrait de contrat ici : chiffres et descriptions seulement.*

## Question

Les annotations de CUAD ont des positions dans **le texte de CUAD** (`context`). L'application,
elle, lira les PDF avec PyMuPDF. Peut-on retrouver les passages annotés dans le texte PyMuPDF,
avec leur page, pour garder la traçabilité (règle 1) ? Et les segments PDF ressemblent-ils aux
segments CUAD sur lesquels la baseline a été entraînée ?

## Méthode

- `src/cg/ingestion/pdf.py` : texte page par page, pages séparées par une ligne vide (un segment
  ne chevauche jamais deux pages).
- `src/cg/ingestion/alignement.py` : recherche du passage dans le texte PyMuPDF **normalisé**, en
  gardant le lien avec les positions d'origine. Deux niveaux :
  - **espaces** : suites d'espaces et de sauts de ligne → un espace ;
  - **étendue** : en plus, minuscules, guillemets et tirets typographiques unifiés, ligatures
    décomposées, tirets de césure invisibles supprimés.
- Correspondance exacte seulement (pas de recherche approximative) : un passage est retrouvé
  tel quel après normalisation, ou il ne l'est pas. Jamais de position « devinée ».
- 10 contrats tirés au hasard (graine 0) pour le détail, puis **les 347 contrats du train** pour
  les taux (`evaluation/verifier_extraction_pdf.py` et un comptage complémentaire, voir le journal G5 à G7).

## Résultats

| Mesure | Résultat |
|---|---|
| PDF retrouvés à partir des titres | 510 / 510 (505 noms identiques, 5 légères différences gérées) |
| Traçabilité des segments PDF (texte exact, segment dans sa page) | 10 / 10 contrats vérifiés |
| Longueur du texte PyMuPDF / texte CUAD | très proche (écart < 1 %) |
| Alignement, niveau **espaces**, nos 9 catégories (train) | 1 603 / 2 269 = **70,7 %** |
| Alignement, niveau **étendu**, nos 9 catégories (train) | 2 230 / 2 269 = **98,3 %** |
| Alignement, niveau étendu, 41 catégories (train) | 9 473 / 9 539 = **99,3 %** |
| Échecs (nos 9, étendu) | 39 annotations, dans 23 contrats |
| Pages sans texte | 46 (39 blanches, 7 avec une image : scans probables), dans 21 contrats ; aucun contrat entièrement scanné |
| Temps d'extraction | ~0,1 s par contrat (0,3 s pour 75 pages) |

### Pourquoi le niveau « espaces » ne suffit pas

Le texte PyMuPDF garde les **guillemets typographiques** du PDF (“Party”), alors que le texte de
CUAD a des guillemets droits ("Party"). La normalisation étendue les unifie : c'est la principale
raison du passage de 71 % à 98 %.

### L'échec observé dans l'échantillon

Un défaut **du texte CUAD lui-même** : une date dont la conversion de CUAD a coupé un mot en deux
(« 19t h » au lieu de « 19th »). Le PDF est correct ; le texte CUAD ne l'est pas. Aucune
normalisation exacte ne peut le retrouver.

## Segments PDF : constat de l'échantillon, puis correction sur train + validation

Sur l'échantillon de **10 contrats**, les segments PDF (texte brut) semblaient environ 10 fois plus
longs que les segments CUAD (médiane 1 422 contre 136 caractères, 54 % au plafond). PyMuPDF y
laissait très peu de **lignes vides** (22 dans un contrat où il détecte 199 **blocs**).

**Correction (mesure sur les 408 contrats de train + validation, D-008)** : cet échantillon était
dominé par quelques gros contrats sans lignes vides. Sur l'ensemble, la médiane PDF (148) est
proche de CUAD (153) ; le vrai écart est une **queue de segments coupés au plafond** (18,8 % des
segments PDF ≥ 1 400 caractères, contre 6,6 % pour CUAD). Leçon : **un échantillon de 10 ne
suffit pas** pour une distribution de longueurs ; on mesure sur tout le train + validation.

La comparaison complète (texte brut contre blocs PyMuPDF) est dans **D-008** (`docs/decisions.md`).

## Ce qu'on en retient

1. L'alignement **exact après normalisation étendue** retrouve 98 % des annotations sans jamais
   inventer de position : c'est l'option retenue par Sara pour **D-007** (acceptée le 2026-11-23).
2. Les annotations non retrouvées (≈ 2 %) doivent être **comptées et exclues**, jamais placées au hasard.
3. La **segmentation des PDF** est à décider (D-008) avant d'utiliser la baseline sur des PDF.
4. L'application devra détecter les **pages sans texte** et prévenir l'utilisateur (OCR hors périmètre
   pour l'instant).
