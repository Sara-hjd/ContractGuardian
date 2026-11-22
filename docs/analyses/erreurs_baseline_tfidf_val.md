# Analyse d'erreurs — baseline 2 (TF-IDF + régression logistique), validation

*2026-11-22. Jeu : validation (61 contrats, 8 253 segments). Test non ouvert.*
*Aucun extrait de contrat ici (dépôt public) : chaque erreur est désignée par sa provenance
(titre CUAD tronqué, positions dans le texte `context`) et décrite en français.*

## Méthode

- Erreurs de la baseline 2 avec les seuils retenus : **201** (durée : 25 faux positifs, 47 faux
  négatifs ; résiliation : 49 FP, 43 FN ; responsabilité : 7 FP, 30 FN).
- Échantillon **tiré au hasard** (graine 0) : 4 faux positifs et 4 faux négatifs par famille,
  soit **24 erreurs**, lues une à une.
- Causes : celles proposées par Sara (exception, clause longue, reformulation, segment trop court,
  étiquette discutable), plus trois apparues à la lecture : **seuil** (probabilité juste sous le
  seuil), **vocabulaire trompeur** (mots de la famille employés dans un autre sens), **contexte**.
- « Étiquette discutable » est un **jugement de lecture**, pas un avis juridique : à confirmer
  par Sara et l'encadrant.

## Résultat

| Cause | Nombre | Erreurs |
|---|---|---|
| Étiquette discutable | **9** | #5, #6, #10, #13, #14, #15, #19, #20, #22 |
| Segment trop court ou coupé | 4 | #2, #7, #17, #18 |
| Clause longue (segment au plafond, sujet noyé) | 3 | #9, #23, #24 |
| Reformulation | 2 | #1, #3 |
| Seuil (probabilité juste sous le seuil) | 2 | #4, #12 |
| Vocabulaire trompeur | 2 | #16, #21 |
| Exception | 1 | #11 |
| Contexte (renvoie à un autre document) | 1 | #8 |
| **Total** | **24** | |

## Détail

| # | Famille | Type | Proba | Contrat [positions] | Cause | Description |
|---|---|---|---|---|---|---|
| 1 | durée | FN | 0,05 | PareteumCorp_20081001… [54353:54494] | Reformulation | Renouvellement exprimé comme « dérogation à une extension automatique », durées caviardées. |
| 2 | durée | FN | 0,03 | RUBIOSRESTAURANTSINC_03_31_2008… [3705:3762] | Segment court | Date de signature au bas d'un bloc de signature (57 caractères). |
| 3 | durée | FN | 0,25 | QIWI_06_16_2017… [15700:15952] | Reformulation | Entrée en vigueur décrite par « come into force », sans le terme « effective date ». |
| 4 | durée | FN | 0,78 | AMERICANPHYSICIANSCAPITALINC_03_31_2003… [9511:9866] | Seuil | Clause de renouvellement et préavis ; probabilité 0,78 pour un seuil de 0,80. |
| 5 | durée | FP | 0,91 | CardlyticsInc_20180112… [472:977] | Étiquette discutable | En-tête qui mentionne la date d'effet ; CUAD a annoté la date ailleurs dans le contrat. |
| 6 | durée | FP | 0,93 | ARMSTRONGFLOORING,INC_01_07_2019… [62249:62870] | Étiquette discutable | Document annexe avec sa propre date et date d'effet, non annotées. |
| 7 | durée | FP | 0,94 | SMITHELECTRICVEHICLESCORP_04_04_2012… [85951:85963] | Segment court | Date isolée (12 caractères) dans un formulaire, non annotée. |
| 8 | durée | FP | 0,88 | RaeSystemsInc_20001114… [28497:28715] | Contexte | Date d'un **autre** accord, cité en référence : ne pas l'annoter est correct. |
| 9 | resp. | FN | 0,30 | BNLFINANCIALCORP_03_30_2007… [35090:36585] | Clause longue | Segment de 1 495 caractères commençant en milieu de phrase ; la limite n'en occupe qu'une partie. |
| 10 | resp. | FN | 0,01 | WARNERCHILCOTTPLC_12_31_2003… [25100:25428] | Étiquette discutable | Force majeure annotée comme plafond de responsabilité. |
| 11 | resp. | FN | 0,47 | ImpresseCorp_20000322… [23904:24039] | Exception | Titre « limitation dans le temps » suivi d'une exception ; le mot « liability » est absent. |
| 12 | resp. | FN | 0,80 | INTERSECTENT,INC_05_11_2020… [22689:23444] | Seuil | Plafond annuel explicite ; probabilité 0,797 pour un seuil de 0,80. |
| 13 | resp. | FP | 0,96 | TodosMedicalLtd_20190328… [26937:27404] | Étiquette discutable | « Remèdes exclusifs » en matière d'indemnisation, annotés comme plafond dans d'autres contrats. |
| 14 | resp. | FP | 1,00 | CHANGEPOINTCORP_03_08_2000… [135842:136472] | Étiquette discutable | Limitation générale de responsabilité, non annotée. |
| 15 | resp. | FP | 1,00 | CHANGEPOINTCORP_03_08_2000… [135488:135840] | Étiquette discutable | Exclusion des dommages indirects, type de clause annoté ailleurs, non annotée ici. |
| 16 | resp. | FP | 0,94 | EUROPEANMICROHOLDINGSINC_03_06_1998… [18067:18983] | Vocabulaire trompeur | Renonciation à des indemnités de fin de contrat : « damages » sans plafond. |
| 17 | résil. | FN | 0,03 | RevolutionMedicinesInc_20200117… [200324:201067] | Segment coupé | Commence en milieu de clause, avec un passage caviardé. |
| 18 | résil. | FN | 0,17 | SPORTHALEYINC_09_29_1997… [7835:7985] | Segment coupé | Fin d'une phrase dont le début (« après la résiliation ») est dans le segment précédent. |
| 19 | résil. | FN | 0,29 | QIWI_06_16_2017… [11397:12244] | Étiquette discutable | Obligation qui suit l'entrée en vigueur, annotée comme post-résiliation. |
| 20 | résil. | FN | 0,09 | CardlyticsInc_20180112… [30229:30670] | Étiquette discutable | Résiliation **pour faute** annotée comme résiliation sans motif. |
| 21 | résil. | FP | 0,68 | INTERSECTENT,INC_05_11_2020… [24980:26478] | Vocabulaire trompeur | Résiliation pour manquement (pour faute), pas sans motif. |
| 22 | résil. | FP | 0,59 | AMERICANPHYSICIANSCAPITALINC_03_31_2003… [9511:9866] | Étiquette discutable | Résiliation par simple préavis (sans motif ?) non annotée comme telle. Même segment que #4. |
| 23 | résil. | FP | 0,66 | EtonPharmaceuticalsInc_20191114… [36329:37826] | Clause longue | Section « durée et résiliation » au plafond de 1 500 caractères, qui mélange les deux. |
| 24 | résil. | FP | 0,84 | IOVANCEBIOTHERAPEUTICS,INC_08_03_2017… [50021:51516] | Clause longue | Segment au plafond qui mêle licences et fin de contrat. |

## Ce qu'on en retient

1. **Plus d'un tiers des erreurs lues (9/24) viennent d'étiquettes discutables.** CUAD répond à
   la question « où est cette clause dans le contrat ? » ; il n'annote pas forcément **chaque**
   occurrence. Projeté sur nos segments, cela donne de faux « négatifs » dans les données. Nos
   chiffres sont donc probablement **pessimistes**, surtout pour la précision.
2. **La segmentation compte** (7/24 : segments courts, coupés ou trop longs). Pistes pour une v2,
   à évaluer sur la validation : fusionner les segments très courts, ne pas couper au milieu
   d'une phrase, découper les sections au plafond par numéro de clause.
3. **Résiliation est la famille la plus difficile** : la résiliation *sans motif* et la résiliation
   *pour faute* emploient les mêmes mots ; TF-IDF ne voit pas la différence de sens.
4. **Deux erreurs sont juste sous le seuil** : le seuil élevé (0,80) choisi sur la validation
   favorise la précision au détriment du rappel.
