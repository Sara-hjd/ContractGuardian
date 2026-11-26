# Journal d'avancement

Une entrée par séance de travail, la plus récente en haut.
Un bilan hebdomadaire est rédigé pour l'encadrant.

> Claude met à jour ce journal à chaque fin de séance, y compris l'avancement et la rubrique
> **« Ce que j'ai compris »**. Sara relit cette rubrique et la corrige si besoin.

---

## Modèles

### Modèle de séance

```markdown
## AAAA-MM-JJ — Titre court

- **Qui** :
- **Durée** :
- **Branche** :
- **Objectif** :

### Fait
-

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | À faire / En cours / Terminé | |
| F2 Extraction de clauses | | |
| F3 Comparaison de paires de clauses | | |
| F4 NLI (ContractNLI) | | |
| F5 Recherche hybride et RAG avec abstention | | |
| F6 Interface analyste | | |
| F7 Traçabilité | | |

- **Étape du planning** :

### Ce que j'ai compris
<!-- Notions vues, pourquoi on les utilise, comment elles s'enchaînent dans le projet.
     Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- *Relu par Sara : à faire*

### Problèmes et solutions
-

### Décisions
- (renvoyer vers docs/decisions.md : D-XXX)

### Preuves
- (commandes et résultats, commits, captures, liens MLflow)

### Prochaine étape
-
```

### Modèle de bilan hebdomadaire (pour l'encadrant)

```markdown
## Bilan semaine du AAAA-MM-JJ au AAAA-MM-JJ

- **Objectifs de la semaine** :
- **Réalisé** (avec liens vers commits / PR) :
- **Résultats chiffrés** (métrique, jeu d'évaluation) :
- **Difficultés rencontrées** :
- **Décisions prises ou à valider** (D-XXX) :
- **Questions pour l'encadrant** :
- **Objectifs de la semaine prochaine** :
```

---

## Séances

## 2026-11-25 → 26 — Séance 1 (mode sans limite) : audit, grille F3, RAG de référence

- **Qui** : Claude (mode « Claude exécute tout »), décisions de Sara
- **Branches** : `docs/mode-sans-limite` (PR #14), `docs/audit-grille-f3` (PR #15), `exp/rag-200-instruct`
- **Objectif** : audit de conformité au cahier des charges ; grille F3 conforme ; mesure de référence du RAG.

### Fait
- **Audit de conformité** (`docs/AUDIT_CONFORMITE_2026-11-25.md`) : exigence → état → preuve → action ;
  actions 🔒 à faire avant le gel des modèles.
- **Grille F3 alignée** sur les 3 étiquettes du cahier des charges (D-020) : guide v2, script du kappa,
  tests. **Prête pour l'annotation** par Sara et Ilyas.
- **D-021** : cahier de référence en attente de l'encadrant ; comparaison V1/V2 prévue en séance 4.
- **`qwen3-vl:8b-instruct`** téléchargé (5 relances automatiques, réseau lent) ; aucune réflexion.
- **RAG de référence, 200 questions de validation** : extractif 0,477 ; RAG 0,529 ; RAG + vérification
  NLI **0,561** (exactitude équilibrée) ; **8,1 s par question** (82 s avant). **D-022 acceptée** :
  instruct par défaut, vérification NLI dans le graphe RAG, extractif par défaut dans l'application
  (LLM sur demande, « à vérifier ») ; test ajouté (51 tests) ; essai réel par l'API.

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | En cours | Manquent section, statut d'extraction, rectangle du bloc (séance 3) |
| F2 Extraction de clauses | En cours | Validation faite ; baseline BM25 et calibration (séance 3) ; test fermé |
| F3 Comparaison de paires de clauses | En cours | Grille conforme ; annotation humaine à faire |
| F4 NLI (ContractNLI) | En cours | Dev fait ; test fermé |
| F5 Recherche hybride et RAG avec abstention | En cours | Mesure de référence faite ; abstention à améliorer (séance 2) |
| F6 Interface analyste | En cours | Surlignage, bouton « à vérifier », export (séance 4) |
| F7 Traçabilité | En cours | Traçabilité des réponses et alertes (séance 4) |

- **Étape du planning** : séance 1 terminée ; prochaine : séance 2 🔒 (corpus explicatif, vrai BM25,
  seuil d'abstention, fidélité).

### Ce que j'ai compris
- **Un audit de conformité** compare, exigence par exigence, ce que demande le cahier des charges et ce
  qui existe, **avec une preuve** (fichier, décision, mesure). Il sert à ne rien oublier avant la fin.
- **Pourquoi aligner la grille AVANT d'annoter** : si on change les étiquettes après, il faut tout
  refaire, et le kappa mesuré ne correspondrait plus au cahier des charges.
- **Modèle « thinking » contre « instruct »** : le premier écrit d'abord un long raisonnement caché
  (lent, parfois sans fin) ; le second répond directement. Pour un outil qui doit répondre vite et en
  JSON, l'instruct est plus adapté : 8 s au lieu de 82 s, et 3 fois moins de sorties illisibles.
- **Un petit échantillon trompe** : sur 20 questions on mesurait 0,643 ; sur 200, 0,529. Avec peu de
  questions, quelques cas chanceux changent tout ; c'est pour ça qu'on disait « indicatif ».
- **Trouver plus de réponses ≠ être meilleur** : le LLM trouve 31 réponses sur 70 (extractif : 6), mais
  il répond aussi à 50 questions qui n'ont pas de réponse annotée. Un outil prudent doit savoir
  **se taire** ; c'est ce que mesurent les « bonnes abstentions ».
- **La vérification NLI** est un second contrôle : le modèle de F4 vérifie que le passage cité
  « implique » bien la réponse. Elle supprime surtout des réponses fausses (on passe de 70 % à 61 % de
  réponses fausses parmi les réponses données) : c'est un compromis entre couverture et prudence.
- **Validation, pas test** : tous ces choix se font sur la validation ; le test reste fermé.

---

## 2026-11-24 — Séance 5/5 (second mode) : F6, LLM indicatif — fin du mode

- **Qui** : Sara-hjd (avec Claude Code, second mode temporaire, séance **5/5**, la dernière)
- **Branche** : `feat/api-interface-f6`

### Fait
- D-018 acceptée (risque n°1 du cahier des charges → plan de repli) ; **D-019 acceptée** (seuil 0,95
  pour la confidentialité, exception au critère ; architecture de F6).
- **F6** : `src/cg/extraction/pipeline.py` (modèles et seuils de D-012/D-013/D-019), modèle TF-IDF de la
  résiliation sauvegardé, **API FastAPI** (`src/cg/api/`), **interface React** (`frontend/`), tests de
  l'API ; **essai de bout en bout réussi** (import 11 s, 23 clauses, 0 segment non traçable ; question,
  alertes, NLI). Défaut corrigé : titres en double à l'import.
- **LLM** : `qwen3-vl:8b` réfléchit toujours et boucle à température 0 → réglages recommandés par Qwen
  (correction de D-016 acceptée) ; **évaluation indicative sur 20 questions** ; téléchargement de
  `qwen3-vl:8b-instruct` lancé (≈ 4 h) pour la mesure de référence.
- Piste « vérification par le NLI » mesurée (aucun effet sur ces 20 questions).
- README : section **Installation** rédigée. **50 tests passent.** **Fin du mode** ; diagnostic complet.

### Résultats (validation ; tests fermés)
- RAG + LLM (20 questions, indicatif) : exactitude équilibrée **0,643** (extractif 0,423) ; 0 réponse
  fausse ; 13/13 abstentions correctes ; 2/7 réponses trouvées ; 82 s par question.
- Confidentialité au critère de D-012 : seuil 0,07 (P 0,510, rappel par évidence 0,988) ; **0,95 retenu** (D-019).

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Une API** expose des fonctions par des adresses web (`POST /contrats`, `GET /contrats/1/clauses`) ;
  l'interface React les appelle ; FastAPI génère la documentation (`/docs`).
- **Tester l'application de bout en bout** révèle des défauts que les tests unitaires ne voient pas
  (un même fichier importé deux fois).
- **Un modèle « thinking »** écrit une réflexion avant de répondre ; à température 0, il peut tourner
  en boucle ; une graine fixe garde la reproductibilité avec une température non nulle.
- **Une exception à une règle commune** est acceptable si elle est **écrite et justifiée** (D-019 :
  le seuil est réglé sur des NDA, l'application lit des contrats commerciaux).
- **Indicatif ou référence** : 20 questions donnent une tendance, pas un résultat ; on le dit.
- *Relu par Sara : à faire*

### Décisions
- D-016 (correction et plan), D-018, D-019 acceptées.

### Prochaine étape (règle habituelle : Sara exécute)
- Fin du téléchargement de `qwen3-vl:8b-instruct`, puis évaluation de référence sur 200 questions.
- Annotations F3 (Sara et Ilyas) et kappa ; 25 questions de F5.
- Décision écrite pour ouvrir le test de F2 (une seule fois), puis de F4 et F5.
- Ilyas : relecture des PR #2 à #13.

---

## 2026-11-24 — Séance 4/5 (second mode) : F3, préparation de l'annotation humaine

- **Qui** : Sara-hjd (avec Claude Code, second mode temporaire, séance **4/5**)
- **Branche** : `feat/f3-annotation`

### Fait
- **D-017 acceptée** (Sara) avec ses deux précisions ; **Recall@5** ajouté partout (0,586 en hybride) ;
  piste pour la séance 5 : vérifier les réponses de F5 avec le NLI de F4.
- **47 paires** de clauses (validation, 4 types, 24 contrats) : références commitées
  (`data/annotations/f3_paires/paires_v1.csv`), texte dans un fichier de lecture local non commité.
- **Grille et guide** (`docs/annotation/GUIDE_F3_PAIRES.md`), modèle de fichier, **script du kappa de
  Cohen** (vérifié contre scikit-learn).
- **Format et guide des 25 questions de F5** (`docs/annotation/GUIDE_F5_QUESTIONS.md`), outil de positions.
- **Test** : aucun fichier de `data/annotations/` ne contient de texte de contrat.
- **Alertes v1 figées avant les annotations** : 41 alertes sur 47 (R3 « exception » quasi partout ;
  R1 NLI jamais). Troncature NLI passée à `longest_first` (sans effet sur F4).
- **45 tests passent.** D-018 proposée.

### À faire par Sara et Ilyas
- Annoter les 47 paires **chacun de son côté** (`annotations_<identifiant>.csv`), puis lancer le kappa.
- Rédiger les **25 questions** (au moins 8 sans réponse).

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Une référence humaine** est nécessaire pour évaluer des alertes : il n'existe pas de jeu tout fait.
- **Le kappa de Cohen** corrige l'accord brut de ce que le hasard donnerait : deux annotateurs qui
  disent presque toujours « à vérifier » sont souvent d'accord… par hasard.
- **Annoter sans se concerter**, sinon on mesure l'influence de l'un sur l'autre, pas la clarté de la grille.
- **Figer la règle avant de voir les étiquettes** : la date du commit le prouve ; une règle ajustée
  sur les étiquettes qui servent à l'évaluer serait trop optimiste.
- **Une règle trop large** (presque tout déclenche une alerte) aura un bon rappel mais une mauvaise
  précision ; c'est ce que l'évaluation montrera.
- *Relu par Sara : à faire*

### Décisions
- D-017 acceptée ; D-018 proposée.

---

## 2026-11-23 — Séance 3/5 (second mode) : F5, recherche hybride et réponse avec abstention

- **Qui** : Sara-hjd (avec Claude Code, second mode temporaire, séance **3/5**)
- **Branche** : `feat/rag-f5`

### Fait
- D-012 (option 2 : meilleur modèle par famille, avec mises en garde) et D-014 acceptées.
- **D-015** (bge-small-en-v1.5 ; recherche hybride dans PostgreSQL) et **D-016** (`qwen3-vl:8b` via
  Ollama, paramétrable par `CG_LLM_MODELE` ; `qwen3:8b` cible ; lien OCR) acceptées ; licence Apache
  2.0 vérifiée et notée (`data_provenance.md`, section « Modèles »).
- Base : `db/init/002_recherche.sql` (texte intégral + vecteurs) ; 96 244 vecteurs calculés.
- `src/cg/recherche/` : embeddings, recherche hybride (RRF), extractif, client Ollama, **graphe
  LangGraph** (chercher → générer → vérifier mot pour mot → répondre ou s'abstenir), questions CUAD.
- **Bug corrigé** : les tests de la base laissaient des contrats (connexion désormais en autocommit) ;
  13 contrats de test supprimés.
- Tests : **40 passent**. D-017 proposée.

### Résultats (validation ; réglage sur 60 contrats du train ; test fermé)
- Recherche hybride : **Recall@5 0,586** (mots 0,518, sens 0,543) ; Recall@10 0,682 (mots 0,638, sens 0,642).
- Extractif avec abstention : exactitude équilibrée **0,521** (toujours s'abstenir : 0,500).
- RAG + LLM : en place et essayé ; **évaluation complète reportée à la séance 5/5** (Mac en veille).

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F5 | En cours | Recherche et extractif mesurés ; RAG + LLM à évaluer (Mac ouvert, sur secteur). |
| F3 | À faire | Séance 4/5 : paires candidates, grille, kappa (annotation par Sara et Ilyas). |
| F6 | À faire | Séance 5/5. |

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Un embedding** transforme un texte en une liste de nombres ; deux textes de sens proche ont des
  listes proches. **pgvector** range ces listes dans PostgreSQL et retrouve vite les plus proches.
- **Recherche hybride** : les mots exacts (« termination ») et le sens (« end the contract ») se
  complètent ; la **fusion RRF** additionne les rangs des deux classements.
- **Un RAG** : on **cherche** les passages, on les donne au LLM, il **répond à partir d'eux seulement**,
  et on **vérifie** chaque citation mot pour mot ; sinon, on s'abstient. **LangGraph** décrit ces
  étapes comme un graphe.
- **Choisir le bon critère** : quand 2 questions sur 3 n'ont pas de réponse, « toujours s'abstenir »
  a 67 % d'exactitude ; on mesure donc l'**exactitude équilibrée**.
- **Un calcul long a besoin d'un Mac éveillé** : la veille suspend les programmes ; on rend les
  évaluations **reprenables** pour ne rien perdre.
- *Relu par Sara : à faire*

### Décisions
- D-012 (option 2), D-014, D-015, D-016 acceptées ; D-017 proposée, puis **acceptée par Sara le 2026-11-24**.
- **Piste pour la séance 5/5** : vérifier la réponse avec le modèle NLI de F4, et comparer avec la vérification mot pour mot.

---

## 2026-11-23 — Séance 2/5 (second mode) : critère de F2, puis NLI (F4)

- **Qui** : Sara-hjd (avec Claude Code, second mode temporaire, séance **2/5**)
- **Branche** : `exp/nli-f4`

### Fait
- D-012 acceptée (Sara) avec un **critère de sélection fixé avant le test** : rappel par annotation
  sous précision ≥ 0,50 par famille, appliqué **sur la validation** (règle 2) ; calcul refait à la
  lettre, famille par famille ; **choix final pour CUAD en attente** (la condition de Sara n'est
  pas remplie : TF-IDF meilleur en résiliation et en moyenne, Transformer en durée).
- D-013 acceptée (deux modèles).
- **F4** : `src/cg/nli/` (paires, modèle, décision du document, métriques), script, 4 tests
  (**36 passent**) ; modèle `models/f4-nli-legal-bert-small` ; D-014 proposée.

### Résultats (dev ContractNLI ; test fermé)
- Classe majoritaire : exactitude 0,681, macro-F1 0,633.
- Transformer (paires) : **exactitude 0,778, macro-F1 0,717** ; évidences P 0,678, R 0,588, F1 0,630.

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F2 | En cours | Critère fixé ; choix du modèle CUAD en attente de Sara ; test à ouvrir ensuite (décision écrite). |
| F4 NLI | En cours | Transformer sur le dev ; D-014 à décider. |
| F3, F5, F6 | À faire | F5 à la séance 3/5. |

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Choisir un modèle, c'est le régler** : le critère s'applique sur la validation ; le test ne sert
  qu'à rapporter le chiffre du modèle déjà choisi.
- **Comparer à précision égale** : un modèle qui « trouve plus » en faisant plus de fausses alertes
  n'est pas meilleur ; on fixe la précision minimale, puis on compare ce que chacun trouve.
- **La NLI** : on présente au modèle une hypothèse et une phrase du contrat ; il dit « implique »,
  « contredit » ou « rien à voir ». Pour tout le contrat, on garde la phrase la plus probante et on
  la cite ; si aucune n'est assez probante, on s'abstient (*NotMentioned*).
- **Une baseline forte** : répondre toujours la réponse la plus fréquente donne déjà 68 % de bonnes
  réponses ; le modèle doit faire nettement mieux pour être utile (78 %).
- **La contradiction** est le cas le plus rare et le plus dur : souvent une exception rédigée en « sauf si ».
- *Relu par Sara : à faire*

### Décisions
- D-012 (critère) et D-013 acceptées ; choix du modèle CUAD en attente ; D-014 proposée.

---

## 2026-11-23 — Séance 1/5 (second mode) : Transformer pour F2

- **Qui** : Sara-hjd (avec Claude Code, second mode temporaire, séance **1/5**)
- **Branche** : `exp/transformer-f2`
- **Plan des 5 séances validé par Sara** : F2 → F4 → F5 → F3 → F6, avec : F5 = réponse extractive
  + petit LLM local orchestré par LangGraph (citations vérifiées mot pour mot, abstention) ;
  F3 = 30 à 50 paires annotées par Sara et Ilyas (kappa de Cohen), Claude prépare seulement.

### Fait
- PyTorch 2.15 + Transformers 4.57 installés ; puce graphique du Mac (MPS) utilisée.
- `src/cg/extraction/transformer.py` (boucle d'entraînement écrite à la main, perte pondérée),
  `src/cg/extraction/evaluation.py` (rappel par annotation, partagé), 2 scripts, 3 tests (**32 passent**).
- Deux modèles (D-013 proposée) entraînés, 2 expériences sur CUAD ; modèles dans `models/` (non commité).
- D-012 (modèle, réglages) et D-013 proposées ; analyse `docs/analyses/transformer_f2_val.md`.

### Résultats (validation ; tests fermés)
- Confidentialité : **F1 0,862** (TF-IDF 0,830, mots-clés 0,580).
- 3 familles CUAD : macro-F1 0,625 (TF-IDF 0,656), rappel par annotation **0,773** (TF-IDF 0,724).

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 | En cours | Inchangé. |
| F2 Extraction de clauses | En cours | Transformer entraîné pour les 4 familles ; D-012, D-013 à décider ; test à ouvrir plus tard (décision écrite). |
| F3 à F6 | À faire | F4 à la séance 2/5. |
| F7 | En cours | Expériences dans MLflow (`F2-transformer`). |

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Affiner un modèle préentraîné** : Legal-BERT connaît déjà la langue juridique ; on lui ajoute une
  petite « tête » de classification qu'on entraîne sur nos segments étiquetés.
- **Une époque** = un passage complet sur le train ; après chacune, on mesure sur la validation et
  on garde la meilleure.
- **Le poids des positifs** compense le déséquilibre, mais **trop fort, il fait dire « oui » trop
  souvent** : 156 fausses alertes en résiliation avec un poids ≈ 100, 74 avec ≈ 10.
- **Un seuil au bord de la grille** est un signal d'alerte ; ici, élargir la grille n'a pas suffi :
  la cause était ailleurs (le poids). On cherche la cause avant de corriger.
- **Deux mesures, deux lectures** : TF-IDF est un peu plus précis par segment, le Transformer
  retrouve plus de clauses. Le choix dépend de ce qui compte pour l'utilisateur (ne rien rater ou
  ne pas déranger), et c'est une décision.
- *Relu par Sara : à faire*

### Décisions
- D-012 et D-013 proposées.

### Prochaine étape
- Sara : décider D-012 et D-013.
- Séance 2/5 : F4, NLI sur ContractNLI.

---

## 2026-11-23 — Séance 3/3 (mode « Claude exécute tout ») : ContractNLI, confidentialité, diagnostic — fin du mode

- **Qui** : Sara-hjd (avec Claude Code, mode temporaire, séance **3/3**, la dernière)
- **Branche** : `exp/contractnli`

### Fait
- D-010 et D-011 acceptées (Sara) ; PR #6 fusionnée.
- **ContractNLI** téléchargé (65,4 Mo, SHA-256 noté), provenance, licence et conditions documentées.
- `src/cg/datasets/contractnli.py` (test fermé dans le code), segments « confidentialité » pour
  train (18 355) et dev (2 872), traçabilité 100 %.
- **Liste de mots-clés figée et commitée avant toute évaluation** (`e44cdf8`).
- Segmentation : option « coupe aux lignes » (le texte de ContractNLI n'a aucune ligne vide).
- Mesures pour **D-009 (proposée)** ; 3 runs MLflow (`F2-confidentialite`).
- **29 tests passent**. **Diagnostic total** : `docs/DIAGNOSTIC_2026-11-16_au_2026-11-23.md`.
- **Fin du mode temporaire** : la règle « Sara exécute les commandes » reprend.

### Résultats (dev ContractNLI, test fermé)
- Mots-clés, négatifs pris dans les NDA : précision 0,433, rappel 0,877, F1 0,580.
- Négatifs pris dans CUAD : F1 0,462 ou 0,355, mais **faussé** : 51 contrats CUAD de validation sur
  61 contiennent des clauses de confidentialité non annotées.

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | En cours | PDF par blocs, pages, alignement, base de données. |
| F2 Extraction de clauses | En cours | 3 familles : TF-IDF (validation) ; confidentialité : mots-clés (dev). Transformer à faire. |
| F3, F4, F6 | À faire | ContractNLI prêt pour F4. |
| F5 | À faire | pgvector prêt. |
| F7 Traçabilité | En cours | Tests + vérification SQL ; MLflow. |

- **Étape du planning** : étapes 1, 2 et 3 (baseline) en place ; confidentialité commencée.

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Un deuxième jeu de données réel** (ContractNLI) comble le trou de CUAD (pas de confidentialité),
  sans données synthétiques (règle 3). Ses « évidences » sont les phrases qui justifient une
  hypothèse : elles deviennent nos annotations.
- **Chaque source a ses pièges** : ici, un texte sans lignes vides. Une même règle de segmentation
  ne convient pas à tous les textes : on mesure avant de choisir.
- **Figer avant de mesurer** : la liste de mots-clés est commitée avant le premier calcul ; la date
  du commit le prouve.
- **Des négatifs « propres »** : prendre des négatifs dans des contrats qui contiennent en réalité
  la clause cherchée fausse l'évaluation et l'apprentissage.
- **Un bug qui donne 0 %** est un signal à prendre au sérieux : on vérifie avant de conclure.
- *Relu par Sara : à faire*

### Décisions
- D-010, D-011 acceptées. D-009 proposée, puis **acceptée par Sara le 2026-11-23** (option D prévue plus tard).

### Prochaine étape
- Sara : décider D-009 ; lire le diagnostic ; refaire les exercices de sa section 9.
- Ilyas : relecture a posteriori des PR #2 à #7.
- Encadrant : valider les décisions ; planning (D-006).

---

## 2026-11-23 — Séance 2/3 (mode « Claude exécute tout ») : base de données, segments PDF, réentraînement

- **Qui** : Sara-hjd (avec Claude Code, mode temporaire, séance **2/3**)
- **Branche** : `infra/postgres-pgvector`

### Fait
- **D-008 acceptée** (Sara) : segmentation des PDF par blocs ; fusion testée en expérience.
- **PostgreSQL 17.12 + pgvector 0.8.7** dans Docker (`docker-compose.yml`, image figée, port
  local seulement, volume nommé) ; `.env` local avec mot de passe aléatoire (jamais commité) et
  `.env.example` ; schéma `contrats`, `pages`, `segments`, `resultats` (`db/init/001_schema.sql`).
- `src/cg/stockage/` (connexion, dépôt, script d'import) ; psycopg 3.3.9 ; 3 tests d'intégration.
- **408 contrats (train + val) importés** dans la base : 96 244 segments, **0 non traçable (SQL)**.
- `fusionner_fragments` (option 3 de D-008) ; segments PDF étiquetés pour 4 seuils de fusion.
- Réentraînement de la baseline sur segments PDF : 5 configurations, comparées sur la validation
  avec le **rappel par annotation** (mesure indépendante de la segmentation).
- **D-010** (base de données) et **D-011** (données d'entraînement : segments PDF sans fusion)
  **proposées** ; Sara décidera.

### Résultats (validation, test fermé)
- Entraîné sur CUAD et appliqué aux PDF : macro-F1 0,643, macro rappel par annotation 0,719.
- Entraîné sur segments PDF (sans fusion) : **0,656 et 0,724**.
- Avec fusion (20, 40, 80) : rappel par annotation 0,720 à 0,723 — rien de significatif
  (1 annotation = 0,5 à 1,1 point de rappel selon la famille).
- Suite de tests : **25 passent**.

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | En cours | Extraction par blocs, pages, alignement, **stockage en base** avec traçabilité vérifiée en SQL. |
| F2 Extraction de clauses | En cours | Baseline réentraînée sur segments PDF (validation) ; D-011 à décider ; confidentialité (ContractNLI) à venir. |
| F3, F4, F6 | À faire | |
| F5 Recherche hybride et RAG | À faire | pgvector prêt ; colonne de vecteurs à ajouter avec le choix du modèle d'embeddings. |
| F7 Traçabilité | En cours | Vérifiée en Python et **dans la base** ; expériences dans MLflow. |

- **Étape du planning** : étape 2 (ingestion PDF + base de données) **en place** ; reste à écrire
  les résultats d'analyse dans la table `resultats` (avec l'API, F6).

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Docker** fait tourner un logiciel (ici PostgreSQL) dans un « conteneur » isolé, à partir d'une
  **image** figée : tout le monde obtient exactement la même base, sans l'installer sur sa machine.
  `docker-compose.yml` décrit le conteneur ; `docker compose up -d` le démarre.
- **Un volume** garde les données hors du conteneur : on peut arrêter et relancer la base sans rien
  perdre (`docker compose down -v` effacerait tout : à éviter).
- **Les secrets restent hors du dépôt** : le mot de passe est dans `.env` (ignoré par Git) ; le dépôt
  ne contient que `.env.example`, un modèle sans vraie valeur.
- **Le schéma** décrit les tables et leurs liens : un contrat a des pages, une page des segments, un
  segment des résultats. Les contraintes (`fin > debut`, page existante) empêchent d'enregistrer
  une provenance incohérente.
- **Vérifier la traçabilité dans la base** : `substring(texte from debut + 1 for fin - debut)` en SQL
  est l'équivalent de `texte[debut:fin]` en Python (SQL compte à partir de 1).
- **Une transaction** : soit tout le contrat est enregistré (contrat, pages, segments), soit rien.
- **Comparer des segmentations différentes** : le F1 par segment change quand la segmentation change ;
  le **rappel par annotation** (la clause a-t-elle été trouvée ?) permet de comparer équitablement.
- **Un écart n'est pas forcément un progrès** : quand une annotation vaut un point de rappel, un
  écart d'un point ne prouve rien ; à résultat égal, on choisit le plus simple.
- *Relu par Sara : à faire*

### Décisions
- D-008 acceptée (Sara). D-010 et D-011 proposées, puis **acceptées par Sara le 2026-11-23**.

### Prochaine étape
- Sara : décider D-010 et D-011 ; puis fusion de la PR de cette séance.
- Séance 3/3 : ContractNLI (D-002, D-009) et baseline par mots-clés pour la confidentialité.

---

## 2026-11-22 → 2026-11-23 — Séance 1/3 (mode « Claude exécute tout ») : extraction PDF

- **Qui** : Sara-hjd (avec Claude Code, mode temporaire, séance **1/3**)
- **Branche** : `feat/ingestion-pdf` (PR #5)
- **Objectif** : vérifier qu'on peut lire les PDF de CUAD avec PyMuPDF, garder la page de chaque
  segment, et retrouver les annotations CUAD dans ce texte.

### Fait
- PyMuPDF **1.28.2** installé (série 1.x : la 2.1 tirait `onnxruntime`, beaucoup trop long à
  télécharger ; arrêt et relance décidés par Sara).
- `src/cg/ingestion/pdf.py` (texte page par page, modes « texte » et « blocs », segments avec
  page), `src/cg/ingestion/alignement.py` (normalisation avec lien vers les positions d'origine),
  deux scripts dans `evaluation/`, 8 tests (suite : **21 passent**).
- Mesures sur le **train** puis **train + validation** (test fermé) ; rapport
  `docs/analyses/verification_pdf_pymupdf.md`.
- **D-007 acceptée** (Sara) : alignement exact après normalisation étendue, 98,3 % des annotations
  de nos 9 catégories retrouvées sur le train ; les autres sont comptées et exclues.
- **D-008 proposée** : segmentation des PDF par **blocs** PyMuPDF (2 % de segments au plafond
  contre 18,8 % en texte brut ; 92,0 % d'annotations entières dans un segment). Sara décidera.
- Numérotation : exemples négatifs de ContractNLI → **D-009**.

### Résultats clés
- 510 PDF retrouvés ; 46 pages sans texte dans le train (39 blanches, 7 images), aucun contrat
  entièrement scanné.
- Normalisation « espaces » : 70,7 % ; « étendue » : **98,3 %** (les guillemets typographiques du
  PDF expliquent l'écart).
- **Correction** : l'échantillon de 10 contrats avait exagéré la longueur des segments PDF
  (médiane 1 422) ; sur 408 contrats, la médiane est 148, proche de CUAD (153).

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | En cours | Extraction PyMuPDF avec pages ; alignement D-007 ; segmentation PDF à décider (D-008). |
| F2 Extraction de clauses | En cours | Baselines sur segments CUAD ; à réentraîner sur segments PDF après D-008. |
| F3 à F6 | À faire | |
| F7 Traçabilité | En cours | Traçabilité page + positions vérifiée sur 141 240 segments PDF (train + val). |

- **Étape du planning** : étape 2, partie « vérification PDF » faite. Reste : D-008, Docker,
  PostgreSQL, pgvector (séance 2/3) ; ContractNLI (séance 3/3).

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Extraire un PDF n'est pas « lire un fichier texte »** : PyMuPDF donne le texte page par page,
  avec sa propre façon de couper les lignes, ses guillemets typographiques, parfois des pages
  vides. Le texte obtenu n'est jamais exactement celui de CUAD.
- **Garder la page** : on met les pages bout à bout en notant où chacune commence et finit ;
  une ligne vide entre deux pages garantit qu'un segment ne chevauche jamais deux pages.
- **Normaliser sans perdre la trace** : pour comparer deux textes, on les « simplifie » (espaces,
  minuscules, guillemets), mais on garde pour chaque caractère sa position d'origine. On cherche
  dans la version simplifiée, on cite dans la version d'origine.
- **Exact plutôt qu'approximatif** : une recherche approximative retrouverait quelques passages
  de plus, mais pourrait citer le mauvais endroit. Pour la traçabilité, une annotation manquante
  vaut mieux qu'une annotation mal placée (D-007).
- **Un petit échantillon peut tromper** : 10 contrats suggéraient des segments PDF dix fois trop
  longs ; 408 contrats ont montré que ce n'était vrai que pour quelques documents. On mesure sur
  tout le train + validation avant de décider, et on corrige par écrit quand on s'est trompé.
- **Mesurer avant de choisir** : pour D-008, on compare les deux segmentations avec les mêmes
  critères (longueur, traçabilité, annotations entières), et c'est Sara qui décide.
- *Relu par Sara : à faire*

### Problèmes et solutions
- Installation de PyMuPDF 2.1 trop lente (dépendances lourdes) → version 1.x.
- Conclusion trop rapide sur 10 contrats → mesure sur 408 contrats et correction écrite.

### Décisions
- D-007 acceptée (Sara). D-008 proposée. D-009 réservée (exemples négatifs ContractNLI).

### Prochaine étape
- Sara : décider D-008 ; relire « Ce que j'ai compris ».
- Séance 2/3 : Docker, PostgreSQL et pgvector ; si D-008 est décidée, préparer les segments PDF
  étiquetés et réentraîner la baseline sur la validation.
- Séance 3/3 : ContractNLI (D-002, D-009).

---

## 2026-11-22 (suite 4) — PR #2 et #3 fusionnées ; début du mode « Claude exécute tout » (séance 1/3)

- **Qui** : Sara-hjd (avec Claude Code)
- **Branche** : `main`, puis `docs/mode-temporaire`

> ⚠️ **Mode temporaire** décidé par Sara : pendant 3 séances, Claude exécute toutes les commandes
> (voir la section en tête de `CLAUDE.md` : interdits, obligations, compteur). Cette suite de
> séance est la **séance 1/3**. Actions tracées dans [JOURNAL_ACTIONS.md](JOURNAL_ACTIONS.md) (F1…).

### Fait
- PR #2 et #3 **fusionnées dans `main`** par décision de Sara, **sans attendre la relecture
  d'Ilyas** (relecture a posteriori demandée en commentaire sur chaque PR, comme pour la PR #1).
- **Incident** : la PR #3 (empilée) a été **fermée** par GitHub à la suppression de sa branche de
  base, au lieu de basculer vers `main`. Réparée : branche de base recréée, PR rouverte, base
  changée vers `main`, puis fusion. Leçon notée (F3).
- `main` : 13 tests passent ; seule branche restante : `main`.
- `CLAUDE.md` : section « Mode temporaire » (3 séances).

### Ce que j'ai compris
<!-- Rédigé par Claude, relu et corrigé par Sara. -->
- **Fusionner sans relecture** est possible techniquement, mais la relecture sert justement à
  ce que les deux membres du binôme valident les règles communes (ici : la règle 5). D'où le
  commentaire laissé à Ilyas pour qu'il puisse encore réagir.
- **PR empilées** : supprimer la branche de base au moment de la fusion peut **fermer** la PR
  suivante. Ordre sûr : fusionner la première sans supprimer sa branche, changer la base de la
  seconde vers `main`, puis supprimer la branche.
- *Relu par Sara : à faire*

---

## 2026-11-22 (suite 3) — Décisions de Sara et pull requests

- **Qui** : Sara-hjd (avec Claude Code)
- **Branche** : `exp/baseline-extraction`

> ⚠️ **Exception ponctuelle**, limitée par Sara à une liste précise : mettre à jour les décisions,
> PROGRESS et la fiche ; commiter et pousser `exp/baseline-extraction` ; créer les PR A et B ;
> ajouter ILyas394 comme relecteur (PR A, PR B, PR #1). **Aucune fusion.** Actions tracées dans
> [JOURNAL_ACTIONS.md](JOURNAL_ACTIONS.md) (E1 et suivantes). Règle habituelle ensuite.

### Décisions prises par Sara, à présenter à l'encadrant pour validation
- **D-001** (segment comme unité de base) : acceptée.
- **D-002** (confidentialité) : acceptée. **ContractNLI** comme source de données réelles pour la
  famille confidentialité, **et** une baseline par mots-clés (comparaison et solution de secours).
  À faire : télécharger et documenter ContractNLI, vérifier l'adaptation de ses passages d'évidence
  en segments étiquetés (risque : les exemples négatifs), figer la liste de mots-clés avant toute
  évaluation.
- **D-004** (splits CUAD) : passe de « acceptée provisoirement » à **acceptée**.
- **D-006** (baseline avant l'étape 2) : **confirmée**.

### Fait
- `docs/decisions.md`, `docs/FICHE_ENCADRANT.md`, ce journal mis à jour.
- Commit et push de `exp/baseline-extraction`.
- PR A (`exp/exploration-cuad` → `main`) et PR B (`exp/baseline-extraction` → `exp/exploration-cuad`)
  créées, ILyas394 relecteur ; ILyas394 relecteur de la PR #1. Liens : voir JOURNAL_ACTIONS.md.

### Avancement
- Inchangé (voir l'entrée « suite 2 »). Ajout au planning : **ContractNLI** pour la famille
  confidentialité (F2) et pour F4.

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Décider puis faire valider** : les décisions sont prises par le binôme (Sara), puis présentées
  à l'encadrant ; le statut le dit (« acceptée, à présenter »), pour garder la trace de qui a décidé.
- **PR empilées** : la PR B a pour base la branche de la PR A ; GitHub n'y montre que le travail
  nouveau. Quand la PR A sera fusionnée et sa branche supprimée, la PR B basculera vers `main`.
  On fusionne avec « merge commit » (pas « squash ») pour que les commits de A restent les mêmes.
- **Relecture** : Ilyas relit et approuve avant toute fusion ; les points sensibles (règle 5 et
  D-005, D-006) sont signalés dans la description des PR.
- *Relu par Sara : à faire*

### Prochaine étape
- Ilyas : relire et approuver PR A, puis PR B ; relire la PR #1 a posteriori.
- Sara : fusionner elle-même PR A puis PR B après approbation (`--merge`).
- Encadrant : valider D-001, D-002, D-004, D-006.
- Ensuite : étape 2 (ingestion PDF, base de données) et téléchargement de ContractNLI.

---

## 2026-11-22 (suite 2) — Baselines d'extraction (F2) sur la validation

- **Qui** : Sara-hjd (avec Claude Code)
- **Branche** : `exp/baseline-extraction` (créée depuis `exp/exploration-cuad`)
- **Objectif** : deux baselines d'extraction, réglées et évaluées sur la validation.

> ⚠️ **Même exception** (Claude Code exécute, tout est tracé dans
> [JOURNAL_ACTIONS.md](JOURNAL_ACTIONS.md), actions D1 et suivantes). Installation de scikit-learn
> et MLflow autorisée d'avance par Sara. **Règle habituelle dès la prochaine séance.**

> 📅 **Changement d'ordre du planning, à présenter à l'encadrant** (D-006) : la **baseline
> d'extraction (étape 3)** est faite **avant** l'ingestion PDF et la base de données (étape 2).
> Raisons : les données de l'étape 1 sont prêtes ; un premier résultat chiffré valide toute la
> chaîne (segments, étiquettes, métriques) ; la baseline ne dépend pas des PDF. Précaution :
> l'étape 2 commencera par comparer, sur quelques PDF du **train**, les segments PyMuPDF aux
> segments CUAD. Si D-004 change, la baseline se relance en quelques minutes.

### Fait
- Installation de scikit-learn 1.9.1 et MLflow 3.18.0 (3 tentatives : réseau très lent).
- Code : `src/cg/extraction/` (mots-clés, TF-IDF, métriques, README), `src/cg/datasets/segments.py`
  (le test ne se charge pas sans `ouvrir_test=True`), `training/baselines_extraction.py`.
- Tests : `tests/test_extraction.py` (7 tests) ; suite complète : **13 tests passent**.
- Deux runs MLflow (expérience `F2-extraction-baselines`).
- Analyse de 24 erreurs de validation : `docs/analyses/erreurs_baseline_tfidf_val.md`.
- D-006 (protocole et ordre du planning) ; tableau des résultats du README rempli (validation).

### Résultats (validation, test fermé)

| Famille | Mots-clés F1 (P / R) | TF-IDF + rég. log. F1 (P / R) |
|---|---|---|
| durée | 0,180 (0,10 / 0,80) | **0,727** (0,79 / 0,67) |
| résiliation | 0,304 (0,21 / 0,53) | **0,521** (0,51 / 0,54) |
| responsabilité | 0,257 (0,16 / 0,71) | **0,758** (0,89 / 0,66) |
| **macro** | **0,247** | **0,669** |

- Réglages retenus (sur val) : bigrammes, C = 10 (bord de la grille), seuils 0,80 / 0,55 / 0,80.
- Seuil 0,5 au lieu du seuil réglé : macro-F1 0,635 au lieu de 0,669.
- Erreurs lues (24) : 9 étiquettes discutables, 7 liées à la segmentation, 2 reformulations,
  2 seuils, 2 vocabulaires trompeurs, 1 exception, 1 contexte.

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | En cours | Segmentation v1 ; PDF à l'étape 2. |
| F2 Extraction de clauses | En cours | 2 baselines évaluées sur la validation ; Transformer à venir. |
| F3 à F6 | À faire | |
| F7 Traçabilité | En cours | Tests de traçabilité ; expériences suivies dans MLflow. |

- **Étape du planning** : étape 3 (baseline) faite avant l'étape 2, voir l'encadré.

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **TF-IDF** transforme un texte en nombres : un poids par mot, fort si le mot est fréquent dans le
  segment et rare ailleurs. **La régression logistique** apprend un poids par mot et en déduit une
  probabilité ; on décide « oui » au-dessus d'un **seuil**.
- **Multi-étiquette** : un classifieur oui / non par famille, parce qu'un segment peut relever de
  plusieurs familles.
- **Précision** = « quand le modèle signale, a-t-il raison ? » ; **rappel** = « trouve-t-il tout ? » ;
  **F1** = compromis des deux ; **macro-F1** = moyenne des familles, la plus rare comptant autant.
- **Pourquoi pas l'exactitude** : un modèle qui ne trouve rien aurait 97 % d'exactitude (un test le
  montre : `test_modele_qui_ne_trouve_rien`).
- **Pondération des classes** : sans elle, le modèle apprend à toujours dire « non ».
- **Régler sur la validation, pas sur le test** : on a choisi n-grammes, C et seuils sur la
  validation ; ses chiffres sont donc un peu optimistes. Le test reste fermé jusqu'à la fin.
- **Lire les erreurs** apprend plus que les chiffres : une partie des « erreurs » sont des
  étiquettes discutables de CUAD, et la segmentation en cause une autre partie.
- **MLflow** garde, pour chaque entraînement, ses paramètres et ses métriques : on peut comparer
  les runs et retrouver comment un résultat a été obtenu.
- *Relu par Sara : à faire*

### Problèmes et solutions
- Installation interrompue deux fois (`incomplete-download`) : relance avec `--retries`, puis
  `--resume-retries` pour reprendre le téléchargement de `pyarrow`.
- pandas 3 retire les colonnes de regroupement dans `groupby().apply()` : tirage de l'échantillon
  d'erreurs refait avec une boucle sur les groupes.

### Décisions
- D-006 acceptée (protocole des baselines, ordre du planning), à présenter à l'encadrant.

### Prochaine étape
- Sara : relire les résultats, l'analyse d'erreurs et « Ce que j'ai compris » ; ouvrir MLflow.
- Avec l'encadrant : ordre du planning (D-006), D-004, D-001, D-002 ; étiquettes discutables de CUAD.
- Ensuite : étape 2 (ingestion PDF, base de données), en commençant par la comparaison des segments.

---

## 2026-11-22 (suite) — Fin de l'étape 1 : splits, segmentation v1, traçabilité

- **Qui** : Sara-hjd (avec Claude Code)
- **Branche** : `exp/exploration-cuad`
- **Objectif** : avoir des données prêtes pour la baseline de F2.

> ⚠️ **Même exception que plus haut**, reconduite par Sara pour la suite de la séance : Claude Code
> exécute et note chaque action dans [JOURNAL_ACTIONS.md](JOURNAL_ACTIONS.md) (actions B1 et
> suivantes). Accord de Sara requis pour push, fusion, suppression, installation.
> **Règle habituelle dès la prochaine séance.**

### Fait
- **D-004 acceptée provisoirement** (à confirmer par l'encadrant) : test officiel CUAD + validation
  de 15 % du train officiel, par contrat, graine 42 ; limite de comparabilité avec l'article notée.
- **Découpage officiel récupéré** : `data.zip` du dépôt GitHub de CUAD (commit `7aad649`), empreinte
  vérifiée ; train 408 / test 102, sans recouvrement, union = les 510 contrats.
  `docs/data_provenance.md` complété (nouvelle section, limites 3, 8, 9, 10).
- **Fichier des splits** `data/splits/cuad_v1_splits.json` (titres seulement) : train 347, val 61,
  test 102 ; nos 9 catégories présentes dans chaque jeu. **D-005** proposée (le commiter ?).
- **Code** : `src/cg/ingestion/segmentation.py` (segmentation v1), `src/cg/datasets/`
  (chargement CUAD, splits, projection des annotations, 2 scripts), README de chaque sous-dossier.
- **Données prêtes** : `data/processed/cuad_segments_v1.jsonl` (non commité), 79 510 segments
  étiquetés par famille.
- **Tests** : `tests/test_tracabilite.py` (4 tests), lancés à la main : **tous passent**, dont
  la traçabilité des 79 510 segments. Puis, avec l'accord de Sara : pytest installé, `tests/test_splits.py`
  ajouté (D-005), `python -m pytest` → **6 tests passent sur 6**.

### Résultats clés

| Jeu | Contrats | Segments | % durée | % résiliation | % responsabilité | % aucune |
|---|---|---|---|---|---|---|
| train | 347 | 58 000 | 1,35 | 0,88 | 0,81 | 97,08 |
| val | 61 | 8 253 | 1,73 | 1,13 | 1,07 | 96,23 |
| test | 102 | 13 257 | 1,61 | 0,83 | 0,83 | 96,82 |

- Longueur des segments : médiane 154 caractères, 90 % sous 1 037 ; **15 % font moins de
  20 caractères** (titres, numéros, lignes isolées) ; 6,9 % sont au plafond ou presque.
- Sur 3 257 annotations de nos 9 catégories, **une seule** n'étiquette aucun segment.

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | En cours | Segmentation v1 du texte CUAD avec positions ; lecture PDF (PyMuPDF) à faire. |
| F2 Extraction de clauses | En cours | Données prêtes (splits + segments étiquetés) ; baseline à faire. |
| F3 Comparaison de paires de clauses | À faire | |
| F4 NLI (ContractNLI) | À faire | |
| F5 Recherche hybride et RAG avec abstention | À faire | |
| F6 Interface analyste | À faire | |
| F7 Traçabilité | En cours | Test automatique : 79 510 segments traçables. |

- **Étape du planning** : étape 1 (données CUAD) **terminée**, sous réserve de D-004 (encadrant)
  (encadrant). D-005 acceptée. Prochaine étape : à choisir (voir le récapitulatif de fin de séance).

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Train, validation, test** : le train sert à apprendre, la validation à régler (choisir un
  modèle, un seuil), le test à mesurer **une seule fois** à la fin. Si on règle sur le test, le
  score final devient optimiste : on a « appris » le test sans le vouloir.
- **Découper par contrat** : les segments d'un même contrat se ressemblent ; s'ils étaient
  répartis entre train et test, le modèle serait testé sur du « presque déjà vu ».
- **Graine aléatoire** : un tirage « au hasard » avec une graine fixée (42) donne toujours le même
  résultat ; on la fixe **avant** de tirer, pour ne pas être tenté de relancer jusqu'à un tirage
  qui nous arrange.
- **Empreinte d'un fichier** (MD5, SHA-1) : une « signature » calculée sur son contenu. Deux
  fichiers de même empreinte sont identiques : c'est ainsi qu'on a prouvé que le `CUADv1.json` du
  dépôt GitHub est le même que celui de Zenodo.
- **Segment et positions** : un segment, c'est un morceau de texte et ses positions `[debut, fin)`
  dans le texte source. Python découpe avec `texte[debut:fin]`, fin exclue. Retirer les espaces
  aux bords en **décalant les positions** garde la garantie `texte[debut:fin] == segment`.
- **Projection des annotations** : CUAD annote des passages, nous classons des segments. On
  transfère une étiquette quand le segment et le passage se chevauchent assez ; la règle
  (`min(20, longueur)`) est fixée **avant** de voir les résultats, pour ne pas l'ajuster sur eux.
- **Déséquilibre** : 97 % des segments n'ont aucune de nos familles. Un modèle qui dit toujours
  « aucune » aurait 97 % d'exactitude et ne servirait à rien : il faudra mesurer la précision et
  le rappel de chaque famille, pas l'exactitude globale.
- **Test automatique** : une fonction avec des `assert`, que pytest lance et vérifie. Notre test
  de traçabilité contrôle les 79 510 segments en une seconde : la règle absolue 1 devient
  vérifiable à chaque modification du code.
- *Relu par Sara : à faire*

### Problèmes et solutions
- Téléchargement de `data.zip` lent (~7 minutes) : le code a été écrit pendant ce temps.
- Annotation de longueur 0 : elle aurait étiqueté tous les segments (seuil de 0) ; exclue dans le code.
- pytest absent : tests appelés directement avec Python en attendant l'accord d'installation.

### Décisions
- D-004 : acceptée provisoirement (option 1), à confirmer par l'encadrant.
- D-005 : **acceptée** par Sara : `data/splits/` commité, exception de la règle 5 étendue dans `CLAUDE.md`.

### Prochaine étape
- Sara : relire « Ce que j'ai compris » ; prendre l'habitude de lancer `python -m pytest` avant chaque commit.
- Encadrant : confirmer D-004, valider D-001 et D-002.
- Segmentation v2 éventuelle (fusionner les segments de moins de 20 caractères), à décider en
  regardant **le train seulement**.
- Baseline F2 (scikit-learn : TF-IDF + régression logistique, une par famille), réglée sur la validation.

---

## 2026-11-22 — Exploration de CUAD (notebook exécuté) et préparation de D-004

- **Qui** : Sara-hjd (avec Claude Code)
- **Durée** : *à compléter*
- **Branche** : `exp/exploration-cuad`
- **Objectif** : exécuter et interpréter `notebooks/01_exploration_cuad.ipynb`, préparer D-004,
  préparer l'entretien avec l'encadrant.

> ⚠️ **Exception ponctuelle à la règle « Sara exécute les commandes »** (CLAUDE.md), décidée par
> Sara **pour cette séance uniquement**, afin de montrer un avancement à l'encadrant. Claude Code
> a exécuté lui-même le notebook, les `git add` et les `git commit` sur `exp/exploration-cuad`.
> Push, fusion, suppression, installation et toute action sur `main` ou GitHub restaient soumis à
> l'accord de Sara. Chaque action est tracée dans [JOURNAL_ACTIONS.md](JOURNAL_ACTIONS.md).
> **La règle habituelle s'applique de nouveau dès la prochaine séance.**

### Fait
- Notebook exécuté en entier avec le noyau `.venv` (Python 3.11.18, pandas 3.1.1) : **aucune
  erreur**, aucune cellule à corriger.
- 4 cellules ajoutées après une première lecture des résultats : **f.3** (les passages *Uncapped*
  sont-ils aussi *Cap* ?) et **g.3** (les `<omitted>` expliquent-ils l'écart 13 823 / 13 101 ?).
- Cellule « Conclusions » rédigée (sans recopier d'extrait de contrat).
- Vérification en lecture seule du dépôt GitHub de CUAD : le découpage officiel est dans `data.zip`
  (`train_separate_questions.json`, `test.json`, cités par `run.sh`) ; pas de jeu de validation.
- **D-004** (découpage train / validation / test) rédigée avec 4 options, statut « Proposée ».
- `docs/JOURNAL_ACTIONS.md` créé ; `docs/FICHE_ENCADRANT.md` créée (fiche de révision).
- Notebook commité **sans sorties** (aucun extrait de contrat dans le dépôt public).

### Résultats clés
- 510 contrats, 41 catégories, 13 823 passages ; positions `answer_start` exactes 13 823/13 823.
- Longueur des contrats : médiane 33 143 caractères (de 645 à 338 211).
- Nos 9 catégories : de 470 contrats (*Agreement Date*) à 111 (*Uncapped Liability*,
  *Notice Period To Terminate Renewal*).
- **Les 111 contrats *Uncapped* ont tous aussi *Cap*, et 125 des 167 passages *Uncapped* sont
  exactement des passages *Cap*** : CUAD annote souvent une même clause dans les deux catégories.
- **13 101 = nombre d'éléments de `master_clauses.csv`** ; l'écart de 722 avec le JSON vient du
  découpage des annotations non contiguës (`<omitted>`), à 11 passages près.
- **`context` = fichier TXT pour 510 contrats sur 510.**

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | À faire | L'exploration confirme le besoin d'aligner les positions CUAD sur notre texte PyMuPDF. |
| F2 Extraction de clauses | À faire | Données comprises ; découpage D-004 à trancher avant tout entraînement. |
| F3 Comparaison de paires de clauses | À faire | Constat : *Cap* + *Uncapped* dans un contrat n'est pas un signal d'incohérence. |
| F4 NLI (ContractNLI) | À faire | |
| F5 Recherche hybride et RAG avec abstention | À faire | |
| F6 Interface analyste | À faire | |
| F7 Traçabilité | À faire | Positions CUAD vérifiées exactes sur le texte CUAD. |

- **Étape du planning** : étape 1 (données CUAD), exploration terminée ; reste D-004.

### Ce que j'ai compris
<!-- Rédigé par Claude en fin de séance, relu et corrigé par Sara. -->
- **Notebook et noyau** : un notebook mélange texte et code ; le **noyau** est le Python qui
  exécute les cellules et garde les variables en mémoire. D'où l'importance de l'ordre
  d'exécution, et du choix du noyau `.venv` (c'est lui qui a pandas 3).
- **Aplatir des données imbriquées** : le JSON de CUAD est une structure « listes dans des listes ».
  On le parcourt une fois pour fabriquer trois tableaux simples (contrats, questions, passages) :
  ensuite, chaque question se règle avec un `groupby` ou un filtre.
- **Vérifier avant de faire confiance** : on a contrôlé que chaque position `answer_start` retombe
  exactement sur le texte annoté (13 823/13 823). C'est la base de la traçabilité (F7) : une
  position qu'on n'a pas vérifiée ne peut pas servir de preuve.
- **Médiane plutôt que moyenne** : avec quelques contrats énormes, la moyenne serait trompeuse ;
  la médiane donne le contrat « typique ».
- **Déséquilibre des classes** : la plupart des catégories sont absentes de la plupart des contrats.
  Un modèle qui répondrait toujours « absent » aurait l'air bon sur beaucoup de questions : il
  faudra des métriques qui ne se laissent pas tromper.
- **Une annotation n'est pas une clause distincte** : la même phrase peut être annotée *Cap* et
  *Uncapped* (une limite avec exception). Pour F3, il faudra comparer des clauses différentes,
  pas des étiquettes.
- **Réconcilier des chiffres** : on a formulé des hypothèses (doublons, découpage, unité de
  comptage), puis on les a testées une à une. Résultat : l'article compte les éléments du CSV,
  le JSON les morceaux. Expliquer un écart est plus convaincant que de le cacher.
- **Pourquoi D-004 avant tout entraînement** : si on choisit les contrats de test après avoir vu
  des résultats, on triche sans le vouloir. Le découpage doit se faire par contrat, être fixé et
  enregistré avant le premier entraînement.
- **Sorties de notebook et dépôt public** : les sorties contiennent du texte de contrat ; on commite
  le notebook sans sorties, chacun peut le réexécuter avec les données locales.
- *Relu par Sara : à faire*

### Problèmes et solutions
- `jupyter nbconvert --execute --inplace` (réécriture du notebook) a été bloqué par le contrôle de
  sécurité de Claude Code. Solution : exécuter vers une copie dans un dossier temporaire ; le
  notebook du dépôt n'a donc jamais contenu de sorties.
- Un extrait de date d'un contrat s'était glissé dans les Conclusions : retiré avant le commit.

### Décisions
- D-004 proposée (voir [decisions.md](decisions.md)), **à trancher ensemble**.
- D-001 et D-002 toujours à valider avec l'encadrant.

### Preuves
- Exécution complète : `jupyter nbconvert --to notebook --execute` (voir JOURNAL_ACTIONS.md, A3 à A6).
- Commits : voir JOURNAL_ACTIONS.md.

### Prochaine étape
- Sara relit les Conclusions du notebook, D-004 et la rubrique « Ce que j'ai compris ».
- Trancher D-004 ensemble (et télécharger `data.zip` si l'option 1 est retenue).
- Reporter les constats dans `docs/data_provenance.md` (limites 3, 8, 9).
- Push de `exp/exploration-cuad` : **seulement avec l'accord de Sara**.

---

## 2026-11-16 — Fusion de la PR #1, puis début de l'étape 1 (données CUAD)

- **Qui** : Sara-hjd (avec Claude Code)
- **Durée** : *à compléter*
- **Branche** : `exp/exploration-cuad` (créée depuis `main` à jour, `2a558c8`)
- **Objectif** : clore l'étape 0 (fusion de la PR #1), puis préparer les données de l'étape 1 :
  comprendre CUAD, le télécharger et documenter sa provenance.

### Fait
- Vérifications de début de séance :
  - `git status` : propre ;
  - `git log --graph --all` : historique linéaire, `main` n'a pas bougé ;
  - `gh pr view 1` : PR ouverte, sans relecture ;
  - collaborateurs du dépôt : ILyas394 n'a pas encore accepté l'invitation.
- Barre d'état VS Code **confirmée** : `Python 3.11.18 ('.venv': venv)`.
- **Décision : fusionner la PR #1 avant la relecture d'Ilyas**, car l'étape 1 a besoin de la
  structure de dossiers. Ilyas relira la PR **a posteriori** quand il aura accès : une PR
  fusionnée reste consultable et commentable. L'invitation est toujours en attente
  (envoyée le 2026-11-15, elle expire au bout de 7 jours, vers le 2026-11-22).
- PR #1 fusionnée avec `gh pr merge 1 --merge` : commit de fusion **`2a558c8`**, qui conserve `63c067f`.
  Lien : https://github.com/Sara-hjd/ContractGuardian/pull/1
- Premier `git pull` sur `main` : *fast-forward* de `5cf0cb5` à `2a558c8`.
- Branche `chore/structure-projet` supprimée en local (`git branch -d`) et sur GitHub
  (`git push origin --delete`). `git branch -a` confirme : seule `main` reste.
- **Étape 0 terminée.**
- Création de la branche `exp/exploration-cuad` pour l'étape 1.
- Recherche des sources officielles de CUAD (Zenodo, site de l'Atticus Project, article
  NeurIPS 2021).
- Règle précisée dans `CLAUDE.md` : Claude peut lancer seul les commandes **en lecture seule**
  (status, log, diff, ls, md5, gh api GET, pages web…). Tout ce qui modifie quelque chose
  reste à Sara.
- **CUAD v1 téléchargé** depuis Zenodo dans `data/raw/cuad/CUAD_v1.zip` (105,9 Mo).
  **Empreinte MD5 vérifiée** et conforme à Zenodo. Décompressé dans `data/raw/cuad/CUAD_v1/` :
  1 051 fichiers (1 JSON, 1 CSV, 1 README, 510 PDF, 510 TXT, 28 XLSX), 173,7 Mo.
- `git check-ignore` confirme que les fichiers CUAD sont ignorés par la règle `data/raw/*`.
- Création de `docs/data_provenance.md` : identification, téléchargement, licence CC BY 4.0
  et citation, contenu, usage dans le projet, et 9 limites connues (dont l'absence de
  catégorie confidentialité, « annotation ≠ risque », et `answer_start` calculé sur le texte
  de CUAD et non sur notre extraction PDF).

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | À faire | |
| F2 Extraction de clauses | À faire | CUAD en préparation (étape 1). |
| F3 Comparaison de paires de clauses | À faire | |
| F4 NLI (ContractNLI) | À faire | |
| F5 Recherche hybride et RAG avec abstention | À faire | |
| F6 Interface analyste | À faire | |
| F7 Traçabilité | À faire | |

- **Étape du planning** : étape 0 **terminée** ; étape 1 (données) **en cours**.
  Le planning détaillé reste à établir avec l'encadrant.

### Ce que j'ai compris
*Relu par Sara : à faire*

**1. Lire le graphe Git** (`git log --oneline --graph --all --decorate`)
- Chaque ligne est un commit, le plus récent en haut. On le lit de bas en haut pour suivre l'histoire.
- Une **branche est une étiquette** collée sur un commit. `HEAD -> main` veut dire
  « tu es sur `main` ». `origin/…` est la dernière image de GitHub connue du Mac.
  `origin/HEAD` indique la branche par défaut de GitHub (`main`).
- Une branche **contient** un commit si on l'atteint en suivant les lignes vers le bas.
  Ici, `63c067f` est atteignable depuis `main` (`2a558c8`), donc il est dans `main`.

**2. Fusionner et pull request**
- **Fusionner**, c'est faire entrer le travail d'une branche dans une autre. Ça permet de
  travailler séparément, puis de rassembler le travail dans `main`. Si deux personnes ont
  modifié les mêmes lignes, Git signale un **conflit** à résoudre à la main.
- La **pull request** est la demande de fusion sur GitHub. Elle permet de relire les changements
  ligne par ligne, de commenter et d'approuver **avant** que ça entre dans `main`, et elle en
  garde la trace. Ici, la relecture est une règle du binôme, que GitHub n'impose pas.
- Trois méthodes de fusion sur GitHub :
  - `--merge` crée un **commit de fusion** à deux parents et garde les commits d'origine ;
  - `--squash` regroupe tout en **un nouveau commit**, avec un nouvel identifiant ;
  - `--rebase` **recopie** les commits au bout de `main`, avec de nouveaux identifiants.

  On a choisi `--merge` pour garder `63c067f` et la trace « PR #1 ».
- Une fusion faite **par GitHub** via une PR crée toujours un nouveau commit (ici `2a558c8`).
  Le **fast-forward** (simple avance de l'étiquette) a eu lieu **sur le Mac**, au moment du `git pull`.

**3. Le premier `git pull`**
- `origin/main` n'est pas GitHub en direct : c'est une **image** qui n'est rafraîchie que
  quand on communique avec GitHub. D'où le message trompeur « up to date » juste après le
  `git switch main`.
- `git pull` = **`fetch`** (télécharger les nouveaux commits et rafraîchir `origin/main`)
  + **`merge`** (faire avancer la `main` locale). Ici, la `main` locale était un ancêtre
  direct, donc un simple *fast-forward*, sans conflit possible.
- Bonne habitude : `git pull` sur `main` **avant** de créer une nouvelle branche.

**4. Supprimer une branche fusionnée**
- Supprimer une branche enlève seulement **l'étiquette** : les commits restent dans `main`.
- `git branch -d` est **prudent** : il refuse si la branche contient du travail non fusionné.
  `git branch -D` force la suppression, à éviter.
- `git push origin --delete <branche>` supprime la branche sur GitHub. La PR reste consultable.
- `git branch -a` liste les branches locales et l'image de celles de GitHub ;
  `git ls-remote --heads origin` interroge GitHub en direct.

**Comment tout s'enchaîne** : vérifier l'état (status, graphe, PR, collaborateurs) →
fusionner la PR sur GitHub → rapatrier la fusion avec `git pull` → supprimer la branche
terminée → repartir de `main` à jour sur une nouvelle branche pour l'étape suivante.

### Problèmes et solutions
- Claude avait annoncé un *fast-forward* pour la fusion de la PR. Inexact : via GitHub,
  `--merge` crée toujours un commit de fusion. Le *fast-forward* a eu lieu lors du `git pull` local.
- Après `git switch main`, certains fichiers et dossiers ont semblé « disparaître » ou revenir
  en arrière (par exemple `.venv*/` redevenu `.venv/`). C'est normal : les fichiers reflètent
  le commit de la branche courante (`5cf0cb5`). Le `git pull` a tout ramené.
- Claude a tenté une commande `gh api` de lecture alors que la règle ne l'autorisait pas encore
  (bloquée, sans effet). Résolu par la précision « lecture seule » ajoutée dans `CLAUDE.md`.
- Pour vérifier les comptages, Claude a lancé un court `python3 -c` en lecture seule sur
  `CUAD_v1.json`. C'est un écart à deux règles (ne jamais utiliser `python3`, et le lancement
  de scripts est réservé à Sara). Il ne se reproduira pas : les comptages se feront dans le
  notebook d'exploration, lancé par Sara avec le `.venv`.

### Décisions
- Fusion de la PR #1 avant relecture, avec relecture d'Ilyas a posteriori (voir « Fait »).

### Preuves
- `gh pr merge 1 --merge` : `✓ Merged pull request Sara-hjd/ContractGuardian#1`.
- `git pull` : `5cf0cb5..2a558c8  main -> origin/main`, `Fast-forward`,
  `15 files changed, 314 insertions(+), 9 deletions(-)`.
- `git branch -d` : `Deleted branch chore/structure-projet (was 63c067f).`
- `git push origin --delete` : `- [deleted]  chore/structure-projet`.
- `git branch -a` : `* main`, `remotes/origin/HEAD -> origin/main`, `remotes/origin/main`.
- `curl` : 100 % de 100 Mio en 3 min 46. `ls -l` : 105 883 672 octets.
- `md5` : `c38f490a984420b8a62600db401fafd5` (identique à Zenodo).
- `find … -type f | wc -l` : 1 051 fichiers extraits (510 PDF, 510 TXT, 28 XLSX).
- `git check-ignore -v` : `.gitignore:15:data/raw/*` pour le zip et le JSON.

### Prochaine étape
- Commiter `CLAUDE.md`, `docs/PROGRESS.md` et `docs/data_provenance.md` sur
  `exp/exploration-cuad`, sans push.
- Exploration de CUAD dans un notebook : répartition des catégories, longueur des contrats,
  comparaison `context` / `full_contract_txt`, réconciliation des comptages.
- Décision à préparer (D-004) : quel découpage entraînement/test utiliser (celui de l'article ?).
- Suivre l'invitation d'Ilyas (expiration vers le 2026-11-22), puis lui demander de relire
  la PR #1 a posteriori.

---

## 2026-11-15 — Structure du projet et environnement Python

- **Qui** : Sara-hjd (avec Claude Code)
- **Durée** : *à compléter*
- **Branche** : `chore/structure-projet` (commit, push et pull request vers `main` en fin de
  séance ; pas de fusion avant relecture par Ilyas)
- **Objectif** : créer l'arborescence du projet et un environnement Python 3.11 isolé,
  prêt pour l'exploration des données.

### Fait
- Création de la branche `chore/structure-projet` (`git switch -c`).
- Décision **D-003 acceptée** : `data/annotations/` est versionné, mais les annotations
  ne contiennent que des références (identifiant du contrat, positions, étiquette,
  annotateur, date), jamais le texte. Exception ajoutée à la règle 5 de `CLAUDE.md`,
  ainsi que dans `README.md` et `docs/CONVENTIONS.md`.
- Environnement virtuel créé (`python3.11 -m venv .venv`), activé, et vérifié : Python 3.11.18.
- Arborescence créée : `data/raw/`, `data/processed/`, `data/annotations/`, `src/cg/`,
  `training/`, `evaluation/`, `notebooks/`, `tests/`, avec des `.gitkeep` et `src/cg/README.md`.
- `.gitignore` corrigé : `data/raw/*` et `data/processed/*` (le contenu) au lieu des dossiers,
  pour pouvoir garder leurs `.gitkeep`.
- `requirements.txt` créé (pandas, jupyter, matplotlib), puis installé avec
  `python -m pip install -r requirements.txt`.
- Configuration de VS Code : `./.venv/bin/python` sélectionné comme interpréteur
  (après suppression d'un `.venv-1/` créé par erreur, voir « Problèmes et solutions »).
  Barre d'état **non confirmée** : sa valeur n'a pas été transmise.
- README : structure du dépôt mise à jour (`training/`, `evaluation/`, sous-dossiers de `data/`).

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | À faire | |
| F2 Extraction de clauses | À faire | Les annotations par références (D-003) serviront à l'évaluation. |
| F3 Comparaison de paires de clauses | À faire | |
| F4 NLI (ContractNLI) | À faire | |
| F5 Recherche hybride et RAG avec abstention | À faire | |
| F6 Interface analyste | À faire | |
| F7 Traçabilité | À faire | D-003 applique la provenance aux annotations. |

- **Étape du planning** : étape 0, mise en place, **terminée** (environnement Python prêt).
  Prochaine étape : étape 1, exploration des données. Le planning détaillé reste à
  établir avec l'encadrant.

### Ce que j'ai compris
*Relu par Sara : à faire*

**1. Les branches Git**
- Une **branche** est une ligne de travail parallèle. Elle part de `main` et enregistre
  ses commits à part, sans toucher à `main`.
- On n'écrit plus directement sur `main`, pour trois raisons :
  - `main` reste la version propre de référence ;
  - une tâche ratée s'abandonne sans dégât ;
  - on peut relire avant de fusionner (`merge`).

  En binôme, chacun avance sur sa branche sans écraser l'autre.
- `git switch -c nom` **crée** la branche et bascule dessus ; `git switch nom` bascule sur
  une branche **existante**. Relancer `-c` sur une branche qui existe donne une erreur sans gravité.
- Les fichiers modifiés et non commités **suivent** quand on change de branche : la
  modification de `PROGRESS.md` faite sur `main` part dans le commit de cette branche.

**2. L'environnement virtuel**
- Un `.venv` est un dossier qui contient un Python et **ses propres bibliothèques**,
  séparées de celles du système et des autres projets.
- `source .venv/bin/activate` place `.venv/bin` en tête du `PATH`. `python` et `pip` désignent
  alors ceux du projet, et le préfixe `(.venv)` le signale. L'activation ne vaut que pour
  le terminal en cours.
- On écrit `python -m pip` plutôt que `pip` : on est sûr d'installer dans le Python qu'on utilise.
- **`.venv/` n'est pas commité, `requirements.txt` l'est** : on versionne la recette
  (quelques lignes, portable), pas le résultat (des centaines de Mo, propre à la machine).
  Ilyas recrée le même environnement avec `pip install -r requirements.txt`.
- **Dépendances transitives** : on a demandé 3 bibliothèques, pip en a installé une centaine,
  car jupyter et matplotlib dépendent elles-mêmes d'autres paquets (numpy, tornado…).
- `>=` fixe une version minimale, `==` une version exacte. On figera les versions quand
  l'environnement sera stable, pour que le binôme ait exactement les mêmes.

**3. Git et les dossiers**
- Git suit des **fichiers**, pas des dossiers : un dossier vide n'existe pas pour lui.
  Le fichier vide `.gitkeep` (une convention, pas une fonction de Git) le rend visible.
- Dans `.gitignore`, `data/raw/` ignore le **dossier** : Git ne regarde plus à l'intérieur,
  et aucune exception `!` n'est possible. `data/raw/*` ignore seulement le **contenu**,
  ce qui permet d'écrire `!data/raw/.gitkeep`.
- Le motif `.venv*/` utilise un **joker** : `*` remplace « n'importe quelle suite de
  caractères ». Il couvre `.venv/`, `.venv-1/`, etc. Le `/` final limite la règle aux dossiers.
- Avant un `rm -rf` (suppression définitive, sans corbeille), on **regarde d'abord** ce
  qu'on va supprimer (`ls -a`).

**4. Les annotations par références (D-003)**
- Une annotation désigne un passage par son **adresse** (contrat, début, fin) au lieu de
  le recopier. Le dépôt public ne publie donc aucun texte de contrat, et le binôme partage
  et historise ses annotations pour mesurer son accord.
- C'est la même logique que la règle de traçabilité : toujours pointer vers la source.

**5. Les outils d'exploration**
- **pandas** manipule des tableaux (*DataFrame*) ; **jupyter** permet d'explorer pas à pas
  dans des notebooks ; **matplotlib** trace les graphiques.
- **VS Code** doit savoir quel Python utiliser (« Python: Select Interpreter ») : sinon,
  il signale des bibliothèques introuvables alors qu'elles sont installées dans `.venv`.

**6. La pull request**
- Une **pull request** (PR) est une demande, sur GitHub, de fusionner une branche dans `main`.
  Elle montre toutes les différences, et permet de commenter ligne par ligne et d'approuver.
- On ne fusionne pas tout de suite : **Ilyas relit d'abord**. Un second regard attrape
  les erreurs, et chacun du binôme connaît tout le code. La fusion se fait après approbation.
- `git push -u origin <branche>` publie la branche sur GitHub (ce qu'il faut avant d'ouvrir
  la PR). `-u` relie la branche locale à sa copie distante.

**Comment tout s'enchaîne** : branche dédiée → environnement isolé en 3.11 → arborescence
prête et `.gitignore` adapté → bibliothèques d'exploration installées → commit sur la branche
→ push → pull request → relecture par Ilyas → fusion dans `main`.
L'étape suivante peut commencer : télécharger CUAD dans `data/raw/` (non versionné)
et l'explorer dans un notebook.

### Problèmes et solutions
- `git switch -c` lancé deux fois : la seconde fois, « a branch named … already exists ».
  Sans conséquence, on était déjà sur la branche.
- La ligne `M docs/PROGRESS.md` annoncée par Claude après `git switch -c` ne s'est pas affichée :
  la prévision était inexacte. À vérifier avec `git status` (le fichier apparaît bien comme modifié).
- `data/raw/` et `data/processed/` étaient ignorés en tant que dossiers, ce qui aurait masqué
  leurs `.gitkeep`. Corrigé avec le motif `dossier/*` suivi d'une exception `!dossier/.gitkeep`.
- **Incident VS Code** : en configurant l'interpréteur, VS Code a créé un second environnement
  `.venv-1/`, et une commande lancée par VS Code a échoué avec « No module named python ».
  Solution appliquée par Sara :
  1. vérifier le contenu du dossier avec `ls -a` avant toute suppression ;
  2. supprimer `.venv-1/` avec `rm -rf .venv-1` ;
  3. sélectionner explicitement `./.venv/bin/python` comme interpréteur.

  Prévention : dans `.gitignore`, `.venv/` remplacé par `.venv*/`, pour qu'aucun dossier
  d'environnement, quel que soit son suffixe, ne puisse être commité.

### Décisions
- D-003 (acceptée) : versionner les annotations, sans le texte des contrats.

### Preuves
- `python --version` (avec `.venv` actif) : `Python 3.11.18`.
- `pip install -r requirements.txt` : `Successfully installed …` avec notamment
  pandas-3.1.1, matplotlib-3.11.2, jupyter-1.1.1, numpy-2.4.6.
- Notice pip : version 26.2.2 installée, 26.3 disponible (mise à jour non urgente).

### Prochaine étape
- **Fin de séance** :
  1. commit `chore: créer la structure du projet et l'environnement Python` ;
  2. push de la branche (`git push -u origin chore/structure-projet`) ;
  3. pull request de `chore/structure-projet` vers `main` (`gh pr create`).
- Fusionner la pull request **seulement après relecture et approbation par Ilyas**
  (il doit d'abord accepter l'invitation au dépôt).
- Confirmer la barre d'état de VS Code : `3.11.18 ('.venv': venv)` attendu.
- Figer les versions dans `requirements.txt` une fois l'environnement stabilisé.
- Étape 1 : télécharger CUAD dans `data/raw/`, premier notebook d'exploration.
  Attention : pandas 3 a changé certains comportements par rapport à pandas 2,
  donc préférer la documentation de pandas 3 aux tutoriels anciens.
- Toujours en attente : acceptation de l'invitation par ILyas394, validation de D-001 et
  D-002 par l'encadrant.

---

## 2026-11-15 — Mise en place du projet

- **Qui** : Sara-hjd (avec Claude Code)
- **Durée** : *à compléter*
- **Branche** : `main` (premier commit, qui crée la branche)
- **Objectif** : préparer l'environnement, le dépôt Git et la documentation de base.

### Fait
- Vérification des outils installés : Homebrew 7.0.13, Python 3.11.18, Git 2.50.1,
  GitHub CLI 2.103.3, Docker 29.8.2, Node.js 24.19.0 (npm 11.17.0).
- Constats : `python3` pointe vers Python 3.9.6 (macOS), donc on utilisera toujours
  `python3.11` et un `.venv`. Docker est installé mais Docker Desktop doit être lancé.
- `git init -b main` dans le dossier du projet, et le dépôt GitHub
  `Sara-hjd/ContractGuardian` (public, vide) relié comme `origin`.
- Accès vérifié avec `git ls-remote origin` : succès, aucune branche (dépôt vide).
- Invitation de ILyas394 comme collaborateur avec droits d'écriture (en attente d'acceptation).
- Création de `CLAUDE.md` : projet, stack, façon de travailler, règle « Sara exécute
  les commandes », règles absolues, conventions Git.
- Création de la documentation de base : `.gitignore`, `README.md`, `docs/CONVENTIONS.md`,
  `docs/PROGRESS.md`, `docs/decisions.md`.
- Changement de règle : Claude remplit désormais `docs/PROGRESS.md` en fin de séance,
  y compris « Ce que j'ai compris » (relu par Sara) ; `CLAUDE.md` mis à jour.
- Configuration de l'identité Git (`user.name`, `user.email` avec l'adresse
  noreply de GitHub pour ne pas exposer d'e-mail personnel dans un dépôt public).
- Premier commit `5cf0cb5` « docs: initialiser la documentation du projet »
  (6 fichiers), exécuté par Sara étape par étape : `git status` → `git add` → `git status`
  → `git commit` → `git push -u origin main`. Push réussi.

### Avancement

| Fonctionnalité | Statut | Commentaire |
|---|---|---|
| F1 Ingestion PDF et provenance | À faire | Unité « segment » proposée (D-001). |
| F2 Extraction de clauses | À faire | Données de confidentialité à trouver (D-002). |
| F3 Comparaison de paires de clauses | À faire | |
| F4 NLI (ContractNLI) | À faire | |
| F5 Recherche hybride et RAG avec abstention | À faire | |
| F6 Interface analyste | À faire | |
| F7 Traçabilité | À faire | Règle de provenance inscrite dans CLAUDE.md. |

- **Étape du planning** : étape 0, mise en place (environnement, dépôt, documentation),
  **terminée**, hors création du `.venv`. Le planning détaillé reste à établir avec l'encadrant.

### Ce que j'ai compris
*Relu par Sara : à faire*

**1. L'environnement de développement**
- **Homebrew** est un gestionnaire de paquets : il installe et met à jour des outils
  (Python, gh…) avec une seule commande, au lieu de télécharger chaque installateur.
- **Plusieurs Python coexistent** sur le Mac : `python3` lance celui de macOS (3.9),
  `python3.11` celui de Homebrew. Le terminal choisit selon le `PATH`, la liste des dossiers
  où il cherche les commandes.
- Un **environnement virtuel (`.venv`)** est un dossier qui contient un Python et ses
  bibliothèques, propres à ce projet. Pourquoi : chaque projet a ses versions de bibliothèques
  sans gêner les autres, et le binôme obtient le même environnement en réinstallant la même liste.
- **Docker** fait tourner des logiciels (ici PostgreSQL + pgvector) dans des conteneurs
  isolés. Le client `docker` ne sert à rien si le moteur (Docker Desktop) n'est pas lancé.

**2. Git et GitHub**
- **Git** garde l'historique du projet **sur l'ordinateur**. **GitHub** héberge une copie
  **en ligne** pour la partager. Ce sont deux choses différentes, reliées par un *remote*.
- `origin` est un **surnom** pour l'URL du dépôt GitHub : on écrit `git push origin`
  au lieu de l'URL complète.
- `git ls-remote` interroge GitHub **sans rien télécharger**. Pas d'erreur = l'accès fonctionne ;
  sortie vide = le dépôt n'a encore aucune branche.
- Un fichier passe par plusieurs **états** :
  non suivi (`??`) → indexé (`git add`) → commité en local (`git commit`) → envoyé sur GitHub (`git push`).
  `git status` indique à tout moment où en est chaque fichier.
- Le **`.gitignore`** liste ce que Git doit ignorer. C'est essentiel ici car le dépôt est
  **public** : les données, les modèles et les secrets ne doivent jamais partir.
- **`gh`** pilote GitHub depuis le terminal. On l'a utilisé pour inviter ILyas394 :
  l'invitation doit être acceptée avant de donner accès.
- **L'index** (*staging area*) est la salle d'attente du commit : `git add` y place
  des fichiers, `git status` montre ce qu'il contient, et seul son contenu part dans le commit.
  On le vérifie toujours avant de commiter, car c'est le dernier moment pour attraper
  un fichier interdit.
- **Un commit** est un instantané du projet, avec un auteur, un message et un identifiant
  unique (le *hash*, ici `5cf0cb5`). Le tout premier s'appelle *root-commit*, car il n'a pas de parent.
- **L'identité Git** (`user.name`, `user.email`) est obligatoire : chaque commit dit qui l'a fait.
  Avec `--global`, elle vaut pour tous les dépôts du Mac. L'adresse
  `…@users.noreply.github.com` relie les commits au compte GitHub sans rendre public
  l'e-mail personnel.
- **`git push -u origin main`** envoie les commits sur GitHub. `-u` relie la branche locale
  à `origin/main` : ensuite, `git push` et `git pull` suffisent.
- **Commit ≠ push** : le commit reste sur l'ordinateur, et seul le push le rend visible
  sur GitHub (et au binôme).

**3. La documentation comme outil de travail**
- **`CLAUDE.md`** : la « mémoire » du projet pour Claude (règles, stack, façon de travailler).
- **`README.md`** : la vitrine, ce que voit un visiteur ou l'encadrant en premier.
- **`docs/CONVENTIONS.md`** : comment écrire le code et les commits, et quand une tâche est « terminée ».
- **`docs/decisions.md`** : le *pourquoi* des choix, pour pouvoir les justifier à la soutenance.
- **`docs/PROGRESS.md`** : ce journal, qui alimente les bilans pour l'encadrant.

**4. Les notions propres au projet**
- Le **segment** (D-001) est un morceau de contrat avec sa **provenance** (page, positions).
  C'est ce qui permet de citer exactement la source de chaque résultat et d'éviter
  qu'un résultat « sorte de nulle part ».
- Les données sont séparées en **entraînement / validation / test**. On règle le modèle
  sur la validation, et le test sert **une seule fois** à mesurer honnêtement la performance.
  S'en servir pour régler le modèle reviendrait à connaître les questions de l'examen à l'avance.
- **CUAD** (clauses annotées dans des contrats) et **ContractNLI** (accords de confidentialité,
  NLI) sont les jeux de données de référence. CUAD n'a pas de catégorie confidentialité,
  d'où la décision D-002.

**Comment tout s'enchaîne** : environnement prêt → dépôt Git relié à GitHub → règles écrites
(CLAUDE.md, CONVENTIONS) → documentation de base → premier commit → on pourra coder F1
(ingestion PDF et segments), sur lequel reposent toutes les autres fonctionnalités.

### Problèmes et solutions
- `python3` n'est pas en 3.11 : utiliser `python3.11 -m venv .venv`.
- Rien à commiter tant que les fichiers de documentation n'existaient pas : le commit
  a été reporté après leur création.
- `git commit` a échoué avec « Author identity unknown » : identité Git jamais configurée
  sur ce Mac. Solution : `git config --global user.name` et `user.email`, puis relancer le commit.

### Décisions
- D-001 (proposée) : le segment comme unité de base.
- D-002 (proposée) : la famille confidentialité est absente de CUAD, à valider avec l'encadrant.

### Preuves
- `git ls-remote origin` : code de sortie 0, sortie vide (dépôt vide accessible).
- Invitation GitHub créée le 2026-11-15 pour ILyas394, permission `write`.
- Commit `5cf0cb5` sur `main` : 6 fichiers, 752 lignes ajoutées.
- `git push -u origin main` : réussi (d'après Sara ; sortie non recopiée).

### Prochaine étape
- Commiter cette mise à jour de `docs/PROGRESS.md` (sur une branche, selon les conventions).
- Vérifier que ILyas394 a accepté l'invitation.
- Créer le `.venv` en Python 3.11.
- Préparer avec l'encadrant : planning détaillé, validation de D-001 et D-002, nom de l'encadrant dans le README.
