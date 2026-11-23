# Baseline TF-IDF sur les segments PDF (blocs) — validation

*2026-11-23. Jeu : validation (61 contrats). Test fermé. Expérience MLflow :
`F2-extraction-segments-pdf`. Script : `training/baselines_extraction_pdf.py`.*

## Question

La baseline TF-IDF + régression logistique (D-006) a été entraînée sur des segments du **texte
CUAD**. L'application lira des **PDF**, segmentés par blocs PyMuPDF (D-008). Faut-il la
réentraîner sur des segments PDF ? Et la fusion des fragments très courts (option 3 de D-008)
aide-t-elle ?

## Configurations (toutes réglées sur la validation : n-grammes, C, seuil par famille)

| Configuration | Entraînement | Évaluation (validation) |
|---|---|---|
| `cuad->pdf` | segments du texte CUAD | segments PDF blocs, sans fusion |
| `pdf-fusion0` | segments PDF blocs, sans fusion | idem |
| `pdf-fusion20/40/80` | segments PDF blocs, fusion des segments de moins de 20 / 40 / 80 caractères | idem (même fusion) |

Seuils de fusion {0, 20, 40, 80} fixés **avant** tout entraînement.

## Résultats

| Configuration | Segments val | F1 durée | F1 résil. | F1 resp. | **macro-F1 (segments)** | R. annot. durée | R. annot. résil. | R. annot. resp. | **macro rappel annot.** |
|---|---|---|---|---|---|---|---|---|---|
| `cuad->pdf` | 11 465 | 0,711 | 0,518 | 0,700 | 0,643 | 0,779 | 0,584 | 0,793 | 0,719 |
| `pdf-fusion0` | 11 465 | 0,723 | 0,554 | 0,689 | 0,656 | 0,788 | 0,607 | 0,776 | **0,724** |
| `pdf-fusion20` | 9 548 | 0,727 | 0,548 | 0,697 | 0,657 | 0,779 | 0,607 | 0,776 | 0,720 |
| `pdf-fusion40` | 8 610 | 0,747 | 0,552 | 0,697 | 0,665 | 0,788 | 0,596 | 0,776 | 0,720 |
| `pdf-fusion80` | 7 687 | 0,741 | 0,568 | 0,697 | **0,669** | 0,788 | 0,596 | 0,784 | 0,723 |

Réglages retenus : bigrammes et C = 10 partout (bord de la grille, comme pour D-006) ; seuils de 0,65 à 0,85.

## Comment lire ces chiffres

- **F1 par segment** : ne se compare qu'à **segmentation égale**. `cuad->pdf` et `pdf-fusion0`
  sont évalués sur exactement les mêmes 11 465 segments : comparables. Avec fusion, il y a moins
  de segments, et plus gros : le F1 par segment change aussi parce que la « question » change.
- **Rappel par annotation** : part des clauses annotées de la validation (alignées selon D-007)
  dont au moins un segment est détecté dans la bonne famille. Il ne dépend pas de la
  segmentation : c'est la mesure qui permet de comparer **toutes** les configurations.
- **Taille de l'effet** : la validation contient 208 annotations alignées de durée, 89 de
  résiliation et 116 de responsabilité. Une annotation vaut donc 0,5 point de rappel (durée),
  1,1 point (résiliation), 0,9 point (responsabilité). Tous les écarts de rappel par annotation
  entre configurations tiennent à **1 à 2 annotations par famille** : **aucun n'est significatif**.

## Ce qu'on en retient

1. **La baseline entraînée sur le texte CUAD se transfère bien aux segments PDF** : macro rappel
   par annotation 0,719, contre 0,724 après réentraînement. Le réentraînement sur segments PDF
   améliore un peu le F1 par segment (0,643 → 0,656, mêmes segments), surtout en résiliation
   (0,518 → 0,554).
2. **La fusion des fragments n'améliore pas le rappel par annotation** (0,720 à 0,723). Elle
   augmente le F1 par segment, mais c'est surtout un effet du changement de segmentation (moins de
   petits segments faciles à classer « aucune »).
3. Avec 61 contrats de validation, des écarts de moins de 2 points ne permettent pas de trancher ;
   on choisit donc la configuration **la plus simple et la plus cohérente avec l'application**.
4. Comme pour D-006 : chiffres **optimistes** (seuils réglés sur la validation), et C = 10 au bord
   de la grille.
