# Audit de conformité au cahier des charges — 2026-11-25

*Référence : « Cahier des charges : ContractGuardian » (11 pages, sections 1 à 18). Complément :
« ContractGuardian 360 — cahier des charges technique » (EMSI, 10 pages, version de travail du
03/11/2026), cité « CDC 360 ». Les deux documents sont hors du dépôt (`~/Downloads`).
État : **fait** / **partiel** / **manquant**. Les actions marquées 🔒 modifient un modèle, les
données d'apprentissage ou le RAG : elles doivent être faites **avant le gel des modèles**.*

## 3.2 Objectifs spécifiques

| # | Exigence | État | Preuve | Action proposée |
|---|---|---|---|---|
| 1 | Ingestion PDF avec provenance : page, **section**, position | **partiel** | `src/cg/ingestion/pdf.py` (page, positions), PR #5 | Ajouter la **section** (titre de section détecté) au segment 🔒 |
| 2 | ≥ 3 familles ; baseline lexicale vs modèle neuronal | **partiel** | D-006, D-012 ; validation seulement | Test final (décision écrite) ; ajouter la baseline **BM25** demandée par F2 🔒 |
| 3 | NLI évalué ; alertes validées indépendamment | **partiel** | D-014 (dev) ; F3 : 47 paires prêtes (PR #12) | Annotation par Sara et Ilyas ; test ContractNLI |
| 4 | RAG à citations vérifiables, abstention mesurée | **partiel** | D-017, `docs/analyses/qr_f5_val.md` (20 questions indicatives) | 200 questions avec le modèle « instruct » ; corpus explicatif 🔒 ; 25 questions |
| 5 | Application web démontrable, reproductible, gratuite | **partiel** | PR #13 (API + React) ; tout local | Dépendances **figées** ; procédure de démo dans le README |

## 4 Périmètre

| Exigence | État | Preuve | Action proposée |
|---|---|---|---|
| PDF texte (DOCX en option) | **fait** (DOCX : non) | `extraire_pdf` | DOCX : extension facultative, non prévue |
| Anglais ; 4 familles | **fait** | D-002, D-009, D-013 | — |
| Alertes limitées à des paires du même thème | **fait** | D-018, `paires_v1.csv` | — |
| Q/R sur le contrat **et sur un petit corpus documentaire explicatif** | **partiel** | F5 sur le contrat seulement | **Constituer et indexer le corpus explicatif** 🔒 |
| Hors périmètre respecté (pas d'avis juridique, pas de note de risque) | **fait** | avertissement dans chaque réponse de l'API | — |

## 5 Données et ressources

| Ressource | État | Preuve | Action proposée |
|---|---|---|---|
| CUAD (découpage par contrat) | **fait** | `data_provenance.md`, D-004, D-005 | — |
| ContractNLI (partitions officielles) | **fait** | `data_provenance.md`, D-009 | — |
| **Corpus personnel de 8 à 15 contrats publics** (démo, contrats inédits) | **manquant** | — | Collecter 8 à 15 contrats publics **hors CUAD**, références datées, provenance ; **jamais** utilisés pour régler |
| **Corpus documentaire explicatif** (base du RAG, sources ouvertes datées) | **manquant** | — | 10 à 25 sources ouvertes (glossaires, guides), licences vérifiées, index séparé 🔒 |
| Mini-jeu de 30 à 50 paires annotées par les deux | **partiel** | 47 paires, guide, kappa (PR #12) | Annotation par Sara et Ilyas ; **aligner la grille sur les 3 étiquettes de F3** (voir F3) |

## 6 Exigences fonctionnelles

| Exigence | État | Preuve | Action proposée |
|---|---|---|---|
| **F1** segment : identifiant, page, positions, fichier d'origine | **fait** | tables `contrats`, `pages`, `segments` (D-010) | — |
| **F1** **section** et **statut d'extraction** | **manquant** | pages sans texte seulement signalées | Colonnes `section` et `statut_extraction` ; coordonnées (rectangle) du bloc pour le surlignage 🔒 |
| **F2** baseline **mots-clés et BM25** vs Transformer, **même jeu de test** | **partiel** | mots-clés, TF-IDF, Transformer (validation) | Baseline BM25 🔒 ; évaluation sur le test |
| **F3** extraire les conditions (durée, préavis, plafond, **délai de secret**) et comparer des paires du même thème | **partiel** | règle v1 (délais), D-018 | Extraction des valeurs (durées, montants) ; type de paire « durée de confidentialité ↔ durée du contrat » manquant |
| **F3** **trois étiquettes** : potentiellement incompatible / compatible / information insuffisante | **non conforme** | grille à 4 étiquettes (`GUIDE_F3_PAIRES.md`) | **Aligner la grille AVANT l'annotation** (décision) |
| **F4** NLI, macro-F1 sur 3 étiquettes ; non transféré directement aux alertes | **fait** (dev) | D-014 ; D-018 | Test ContractNLI |
| **F5** clauses et **documents explicatifs indexés séparément** | **manquant** | — | Index du corpus explicatif 🔒 |
| **F5** recherche **BM25** + embeddings | **partiel** | texte intégral PostgreSQL (`ts_rank_cd`, **pas BM25**) + pgvector | Implémenter un vrai BM25 et comparer 🔒 |
| **F5** citation contrat + page + extrait ; abstention | **fait** | graphe vérifié mot pour mot (D-017) | — |
| **F6** importation | **fait** | `POST /contrats` | — |
| **F6** **navigation par page** et **clauses surlignées par famille** | **manquant** | liste de citations seulement | Afficher le PDF page par page avec surlignage par famille |
| **F6** onglet alertes avec justification | **fait** | `GET /contrats/{id}/alertes` | — |
| **F6** **bouton « à vérifier »** | **manquant** | — | Bouton + statut enregistré |
| **F6** chat documentaire | **fait** | onglet « Questions » | — |
| **F6** **export d'un rapport PDF ou JSON** | **manquant** | — | Export JSON et PDF (clauses, alertes, preuves, avertissement) |
| **F7** pour chaque réponse ou alerte : **version du modèle, paramètres, passages récupérés, statut de revue humaine** | **partiel** | nom du modèle pour F2 seulement (table `resultats`) | Table des exécutions (questions, alertes) et des revues ; exposer ces champs dans l'API |
| **F7** accès limité, pas de données privées | **partiel** | base locale (127.0.0.1), `.env` | Documenter ; pas de comptes (application locale mono-utilisateur) |

## 7 Exigences non fonctionnelles

| Exigence | État | Preuve | Action proposée |
|---|---|---|---|
| Reproductibilité : **dépendances figées** ; commandes documentées | **partiel** | `requirements.txt` en `>=` ; README « Installation » | Fichier de versions exactes (`pip freeze`) ; `package-lock.json` (présent) |
| Autonomie (sans service payant) | **fait** | tout local (Ollama, PostgreSQL) | — |
| Prudence : **périmètre juridique et linguistique affiché** dans l'interface | **partiel** | avertissement « pas d'avis juridique » | Afficher aussi « contrats en anglais, droit commercial général » |
| Performance : objectif fixé après mesure | **partiel** | import 11 s (9 pages), extractif < 1 s, LLM 73-82 s | Fixer l'objectif par écrit (décision) |
| Maintenabilité : modules ; tests ingestion, recherche, API | **fait** | 50 tests (`tests/`) | — |

## 9 Protocole d'évaluation

| Exigence | État | Preuve | Action proposée |
|---|---|---|---|
| Partition par contrat ; test jamais utilisé pour régler ; partitions officielles ContractNLI | **fait** | D-004, D-005, D-009 ; garde-fous dans le code | — |
| Extraction : P, R, F1 par classe ; tolérance de recouvrement définie à l'avance | **fait** (validation) | règle min(20, longueur), D-006 | Test final |
| NLI : macro-F1 (partitions officielles) | **fait** (dev) | D-014 | Test final |
| Alertes : précision, rappel, accord | **partiel** | protocole et kappa prêts | Après annotation |
| RAG : Recall@5, exactitude des citations, **fidélité**, abstention correcte ; **25 questions** | **partiel** | Recall@5 0,586 ; citations vérifiées ; fidélité non mesurée | Mesurer la **fidélité** ; 25 questions (Sara, Ilyas) |
| Robustesse : ≥ 10 erreurs documentées | **fait** | `docs/analyses/erreurs_baseline_tfidf_val.md` (24) | Refaire pour le modèle final |
| Ablations : BM25 seul / embeddings seuls / hybride ; avec et sans abstention ; mots-clés vs Transformer | **partiel** | faits, mais « BM25 » = texte intégral PostgreSQL | Refaire avec un vrai BM25 🔒 |

## 10 Critères de recette

| # | Critère | État | Action proposée |
|---|---|---|---|
| 1 | ≥ 3 catégories **retrouvées et surlignées** dans un **contrat inédit** | **partiel** | Corpus personnel hors CUAD + surlignage dans le PDF |
| 2 | Baseline et modèle comparés sur le **même échantillon test** | **partiel** | Ouverture du test (décision écrite) |
| 3 | Alerte : deux passages + motif ; **marquer « à vérifier »** | **partiel** | Bouton et statut de revue |
| 4 | RAG cite document et page ou extrait ; ne conclut pas sans preuve | **fait** | Mesure de référence sur 200 questions |
| 5 | Aucune qualification de légalité | **fait** | — |

## 14 Livrables

| Livrable | État | Action proposée |
|---|---|---|
| Dépôt organisé, **dépendances figées**, README complet | **partiel** | Versions exactes ; procédure de démo dans le README |
| Provenance, licences, limites, **dictionnaire des variables**, partitions, protocole | **partiel** | Écrire le dictionnaire des variables (tables, fichiers, colonnes) |
| Baseline et variante, **métriques exportées**, analyses d'erreurs, **jeux de questions annotés** | **partiel** | Export des métriques (MLflow + tableaux) ; 25 questions |
| Application ou API, tests, preuves de citations, politique d'abstention | **fait** | — |
| Rapport, supports de soutenance, **vidéo**, **répartition des contributions** | **manquant** | Séances finales (format EMSI à recevoir) |

## 15-16 Éthique et améliorations

| Point | État | Action proposée |
|---|---|---|
| Chaque alerte soumise à revue humaine | **manquant** | Statut de revue (lié au bouton « à vérifier ») |
| Limites linguistiques et juridiques affichées | **partiel** | Voir section 7 |
| Amélioration 1 : **calibration** (scores NLI des alertes → certitude affichée) | **manquant** | Calibrer sur la validation 🔒 |
| Amélioration 2 : **seuil d'abstention par courbe couverture / erreur** | **manquant** | Courbe sur les questions de réglage (train) 🔒 |
| Amélioration 3 : reranker | **manquant** | Facultatif 🔒 |
| Amélioration 4 : fenêtres selon la structure | **manquant** | Facultatif (changerait la segmentation et donc les modèles) 🔒 |
| Amélioration 5 : double annotation et kappa | **partiel** | Prêt ; annotation à faire |
| Amélioration 7 : **MLflow complet** | **partiel** | F2, F4, F5 enregistrés ; ajouter les évaluations manquantes (critère F2, seuil de confidentialité, prédictions F3) |

## Ce qu'ajoute le CDC 360 (à arbitrer)

| Exigence du CDC 360 | Dans le cahier de référence | État | Proposition |
|---|---|---|---|
| **Comparaison V1/V2** de deux versions d'un contrat (MVP, critère de recette, scénario de soutenance) | **Extension** (section 17) | **manquant** | **À trancher par Sara et l'encadrant** : quel document fait foi ? |
| OCR des pages sans texte (MVP F02) | Facultatif | **manquant** | Extension (Qwen-VL, D-016) |
| Réponses d'inférence avec identifiant d'expérience, version du modèle, score, seuil | F7 | **partiel** | Inclus dans l'action F7 |
| RAG : ≥ 20 questions dont 5 sans réponse ; Recall@3 et MRR | 25 dont 8 | **partiel** | Ajouter Recall@3 et MRR aux mesures (sans effort) |
| ACORD (benchmark de recherche de clauses) | Non mentionné | **manquant** | Facultatif |
