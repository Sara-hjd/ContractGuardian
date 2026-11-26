# Registre des décisions

Chaque choix technique important est noté ici, pour garder une trace de **pourquoi**
le projet est fait ainsi.

**Statuts possibles** : `Proposée` → `Acceptée` ou `Rejetée` ; plus tard éventuellement
`Remplacée par D-XXX`.

---

## Modèle

```markdown
## D-XXX — Titre

- **Date** : AAAA-MM-JJ
- **Statut** : Proposée | Acceptée | Rejetée | Remplacée par D-XXX

### Contexte
Quel problème se pose, quelles contraintes.

### Options envisagées
1. Option A : avantages / inconvénients
2. Option B : avantages / inconvénients

### Décision
L'option retenue.

### Raisons
Pourquoi cette option plutôt que les autres.

### Conséquences
Ce que ça implique pour la suite (code, données, évaluation).
```

---

## D-001 — Le segment comme unité de base

- **Date** : 2026-11-15
- **Statut** : **Acceptée (Sara, 2026-11-22), à présenter à l'encadrant**. Déjà mise en œuvre :
  segmentation v1 (`src/cg/ingestion/segmentation.py`), traçabilité testée sur 79 510 segments.

### Contexte
Toutes les fonctionnalités (extraction, comparaison, NLI, RAG) travaillent sur des morceaux
de contrat. Une règle absolue impose que **toute sortie référence sa provenance**
(page, positions). Il faut donc une unité commune.

### Options envisagées
1. **Le document entier** : simple, mais impossible de citer un passage précis, et trop
   long pour les modèles Transformer (limite de tokens).
2. **La page** : provenance facile, mais une clause peut être coupée entre deux pages,
   et une page contient souvent plusieurs clauses.
3. **Le segment** (paragraphe ou clause, avec page et positions de début et de fin) :
   assez précis pour citer, assez court pour les modèles.

### Décision
Option 3 : **le segment** est l'unité de base de tout le projet.

### Raisons
- Il permet la citation exacte exigée par la règle de traçabilité.
- Sa taille est adaptée aux modèles et à la recherche vectorielle.
- Toutes les fonctionnalités partagent la même structure : moins de conversions, moins d'erreurs.

### Conséquences
- F1 doit produire des segments fiables, avec page et positions.
- La base PostgreSQL stocke les segments ; les résultats (clauses, incohérences, réponses)
  pointent vers un ou plusieurs segments.
- La règle de découpage v1 (lignes vides, plafond de 1 500 caractères) est documentée dans
  `src/cg/ingestion/README.md` ; une v2 éventuelle sera décidée sur la validation.

---

## D-002 — La famille « confidentialité » est absente de CUAD

- **Date** : 2026-11-15
- **Statut** : **Acceptée (Sara, 2026-11-22), à présenter à l'encadrant**

### Contexte
Le projet doit extraire quatre familles de clauses : durée, résiliation, responsabilité,
confidentialité. CUAD couvre les trois premières (par exemple *Expiration Date*,
*Renewal Term*, *Termination For Convenience*, *Cap On Liability*, *Uncapped Liability*),
mais **n'a pas de catégorie dédiée à la confidentialité**. Les données synthétiques
sont interdites pour l'entraînement.

### Options envisagées
1. **S'appuyer sur ContractNLI** : ce jeu porte sur des accords de confidentialité (NDA)
   et annote des passages comme preuves. Il faut vérifier si ces annotations peuvent servir
   à l'extraction.
2. **Annoter à la main** des clauses de confidentialité sur des contrats réels
   (par exemple ceux de CUAD), avec un guide d'annotation, et si possible les deux membres
   du binôme pour mesurer l'accord entre annotateurs.
3. **Retirer la confidentialité** du périmètre de F2 (extraction), et ne la traiter
   que via F4/F5.

### Décision
**Option 1, complétée par une baseline par mots-clés** :
- **ContractNLI** est la source de **données réelles** pour la famille confidentialité (règle 3 :
  pas de données synthétiques). On réutilise ses **passages d'évidence** comme passages annotés.
- Une **baseline par mots-clés** pour la confidentialité, construite comme celle des trois autres
  familles (D-006). Elle sert de **point de comparaison** et de **solution de secours** si les
  annotations de ContractNLI ne peuvent pas être adaptées à l'extraction.

### Raisons
- ContractNLI annote des accords de confidentialité (NDA) réels, avec des passages d'évidence :
  c'est la seule source réelle et autorisée (règle 3) déjà annotée pour ce sujet.
- Il sert aussi à F4 (NLI) : un seul jeu à télécharger, documenter et comprendre pour deux
  fonctionnalités.
- La baseline par mots-clés est peu coûteuse, et elle garantit un résultat pour la quatrième
  famille même si l'adaptation de ContractNLI échoue.

### Conséquences
1. **Téléchargement de ContractNLI**, depuis sa source officielle, dans `data/raw/contractnli/`
   (non versionné) : version, licence (à vérifier au téléchargement), empreinte et limites
   documentées dans `docs/data_provenance.md`, comme pour CUAD.
2. **Vérifier l'adaptation des passages d'évidence en segments étiquetés**, avant tout entraînement :
   - comprendre le format : passages d'évidence rattachés à des hypothèses ; positions dans le texte ;
   - segmenter les documents avec la règle v1 (D-001) et projeter les passages d'évidence avec la
     même règle de chevauchement que CUAD, puis le **tester** (traçabilité, comme pour CUAD) ;
   - **risque principal** : dans un NDA, presque tout le texte porte sur la confidentialité ;
     décider quelles hypothèses comptent pour la famille, et d'où viennent les **exemples
     négatifs** (segments non annotés des NDA ? contrats CUAD, au risque d'y trouver des clauses
     de confidentialité non annotées ?). Ce choix fera l'objet d'une décision dédiée (**D-009**).
   - si l'adaptation n'est pas fiable, on le documente et on s'appuie sur la baseline par mots-clés.
3. **Découpage** : respecter le découpage train / dev / test **propre à ContractNLI** s'il en a un
   (règle 2), sinon un découpage par document, fixé et versionné comme pour CUAD (D-004, D-005).
4. **Baseline par mots-clés** : liste écrite à la main et justifiée, **figée avant toute
   évaluation**, jamais modifiée après avoir vu les résultats (comme `mots_cles.py`).
5. **Présentation** : les résultats de la famille confidentialité seront présentés **à part**
   (données d'une autre source, NDA uniquement) et non comparés directement aux trois autres familles.

---

## D-003 — Versionner les annotations, sans le texte des contrats

- **Date** : 2026-11-15
- **Statut** : Acceptée

### Contexte
La règle absolue 5 interdit de commiter des données. Or le binôme va produire ses propres
annotations humaines sur des contrats réels. Ces annotations sont un **livrable du projet**,
et Sara et Ilyas doivent se les **partager pour mesurer leur accord** (accord inter-annotateurs).
Le dépôt est public, et les contrats peuvent être soumis à licence ou confidentiels.

### Options envisagées
1. **Ignorer `data/annotations/`** comme les autres données : la règle 5 est respectée
   sans exception, mais le partage dans le binôme et la conservation du livrable deviennent
   compliqués (échange de fichiers à la main, risque de versions divergentes).
2. **Versionner les annotations complètes** (avec le texte annoté) : simple, mais cela
   publierait des extraits de contrats.
3. **Versionner des annotations par références uniquement** : chaque annotation pointe
   vers le texte sans le recopier.

### Décision
Option 3. `data/annotations/` est versionné. Une annotation contient **uniquement** :
- l'identifiant du contrat (CUAD) ou du document ;
- les positions de début et de fin ;
- l'étiquette ;
- l'annotateur ;
- la date.

Elle ne contient **jamais le texte du contrat**.

### Raisons
- Les annotations sont notre travail et un livrable : elles doivent être historisées et partagées.
- Git garde l'historique de chaque annotation (qui, quand, quelle modification).
- Les références suffisent pour retrouver le texte à partir des données sources, sans les publier.
- C'est cohérent avec la règle de traçabilité : une annotation, comme une sortie, désigne un
  segment par sa provenance.

### Conséquences
- `CLAUDE.md` : exception ajoutée à la règle 5, limitée à `data/annotations/`.
- Le format des fichiers d'annotation reste à définir (CSV ou JSONL), avec un schéma documenté.
- Les positions doivent être **reproductibles** : préciser par rapport à quel texte elles sont
  calculées (texte fourni par CUAD, ou texte extrait d'une page par PyMuPDF, avec sa version).
- Prévoir un test automatique qui vérifie qu'aucun fichier de `data/annotations/` ne contient
  de champ de texte.
- L'annotateur est désigné par son identifiant GitHub, pas par une donnée personnelle.

---

## D-004 — Découpage entraînement / validation / test de CUAD

- **Date** : 2026-11-22
- **Statut** : **Acceptée (Sara, 2026-11-22), à présenter à l'encadrant** (option 1)

### Contexte
Avant tout entraînement (F2), il faut fixer quels contrats servent à **entraîner**, à **régler**
(validation : hyperparamètres, seuils, choix de modèle) et à **évaluer une seule fois** (test).
La règle absolue 2 interdit d'utiliser le test pour régler quoi que ce soit.

Ce que l'exploration (`notebooks/01_exploration_cuad.ipynb`) et les sources nous apprennent :
- **510 contrats**, un seul texte par contrat ; le découpage doit se faire **par contrat**, jamais
  par passage. Sinon, des passages d'un même contrat seraient à la fois en entraînement et en
  test (fuite de données).
- **Découpage officiel** : l'article utilise 80 % / 20 % des contrats, tiré au hasard. Le zip
  Zenodo ne le contient pas. Le dépôt GitHub `TheAtticusProject/cuad` contient un `data.zip`
  (18 Mo) ; son script `run.sh` entraîne sur `data/train_separate_questions.json` et évalue sur
  `data/test.json`. **Il n'y a pas de jeu de validation officiel.** Le contenu exact de
  `data.zip` n'a pas encore été téléchargé ni vérifié.
- **Catégories rares** parmi les nôtres : *Uncapped Liability* et *Notice Period To Terminate
  Renewal* n'apparaissent que dans 111 contrats. Un test de 102 contrats en contiendrait environ 22 :
  les mesures par catégorie seront peu précises.
- **25 types de contrats**, de 3 à 34 contrats par type.

### Options envisagées
1. **Reprendre le découpage officiel** (`test.json` du dépôt GitHub) comme test, puis découper le
   train officiel en entraînement + validation (par exemple 85 % / 15 % des contrats, tirage fixé).
   - ➕ Même **jeu de test** que l'article et les autres travaux sur CUAD (mais voir la limite
     de comparabilité dans « Décision »).
   - ➕ Le test est fixé par d'autres : impossible de le « choisir » à notre avantage.
   - ➖ Il faut télécharger et vérifier `data.zip` (téléchargement à documenter dans
     `data_provenance.md`) et retrouver la liste des titres de chaque partie.
   - ➖ Le test officiel n'est peut-être pas équilibré pour nos 9 catégories.
2. **Notre propre découpage aléatoire par contrat** (par exemple 70 / 15 / 15), avec une graine
   fixée, et la liste des titres de chaque partie versionnée (des titres, pas de texte).
   - ➕ Simple, entièrement sous notre contrôle, documenté.
   - ➖ Résultats **non comparables** directement à l'article.
   - ➖ Le hasard peut laisser trop peu d'exemples d'une catégorie rare dans un jeu.
3. **Notre propre découpage stratifié par contrat** : même chose que l'option 2, en équilibrant
   la présence de nos 9 catégories (et/ou le type de contrat) entre les trois jeux.
   - ➕ Chaque jeu contient assez d'exemples de chaque catégorie : mesures plus stables.
   - ➖ Plus complexe à expliquer et à implémenter (un contrat a plusieurs catégories à la fois).
   - ➖ Pas comparable à l'article non plus.
4. **Validation croisée par contrat** (k plis) sur la partie entraînement, avec un test fixe
   (officiel ou le nôtre) mis de côté.
   - ➕ Utilise mieux les 510 contrats pour le réglage ; mesure aussi la variabilité.
   - ➖ k fois plus d'entraînements : coûteux pour un Transformer sur une machine personnelle
     (règle 4 : pas de service payant).

### Décision
**Option 1** :
- **Test** : les contrats du `test.json` officiel de CUAD (dépôt GitHub `TheAtticusProject/cuad`,
  `data.zip`), sans modification.
- **Entraînement + validation** : les contrats du train officiel, découpés **par contrat** en
  **85 % entraînement / 15 % validation** (dans la fourchette 10–15 % fixée par Sara ; on prend le
  haut de la fourchette pour avoir plus d'exemples de validation des catégories rares).
- **Tirage de la validation** : aléatoire, avec une **graine fixée à l'avance : 42**, notée ici
  avant le tirage.
- **Contrôle** : on vérifie que nos 9 catégories sont présentes dans **chacun** des trois jeux.
  Si une catégorie manquait, on **ne change pas de graine en silence** : on le note ici et on
  décide ensemble (par exemple passer à un tirage stratifié).

**Résultat du tirage (2026-11-22)** : train 347 contrats, validation 61, test 102 ; partition des
510 contrats vérifiée. Nos 9 catégories sont présentes dans chaque jeu (minimum : 13 contrats
*Uncapped Liability* dans le test, 14 *Notice Period To Terminate Renewal* en validation). Aucun
nouveau tirage n'a été nécessaire. Fichier : `data/splits/cuad_v1_splits.json` (voir D-005).

**Limite de comparabilité** : notre tâche n'est **pas** celle de l'article. L'article évalue un
modèle de questions-réponses qui doit retrouver les passages exacts, sur les 41 catégories, avec des
métriques propres (AUPR, précision à 80 % de rappel…). Nous classerons des **segments** (D-001) par
**famille**, sur 9 catégories seulement. Même avec le même jeu de test, **nos chiffres ne seront
pas directement comparables** à ceux de l'article ; on le dira à chaque présentation de résultats.

### Raisons
- Le test est fixé par les auteurs de CUAD, avant nous : il est impossible de le « choisir » à
  notre avantage, ce qui protège la règle 2.
- Le jeu de test est **le même** que celui des travaux publiés : utile pour situer nos résultats,
  même si les chiffres ne se comparent pas directement.
- Une validation tirée du train donne un jeu pour régler les modèles **sans toucher au test**.
- Plus simple qu'un découpage stratifié ou qu'une validation croisée, et moins coûteux en calcul.

### Conséquences (quelle que soit l'option)
- Le découpage se fait **par contrat** et est **enregistré dans un fichier** (liste des titres
  par jeu), versionné ; il ne contient aucun texte de contrat.
- Le jeu de test n'est **ouvert qu'une fois**, pour l'évaluation finale (règle 2). Les explorations
  déjà faites portent sur tout CUAD mais sont descriptives : elles n'ont réglé aucun modèle.
- Les catégories rares seront présentées avec leur nombre d'exemples de test, pour rappeler
  l'incertitude des mesures.
- Nos futures annotations humaines (D-002, D-003) devront respecter le même découpage si elles
  portent sur des contrats CUAD.

---

## D-005 — Où stocker le fichier des splits, et faut-il le commiter ?

- **Date** : 2026-11-22
- **Statut** : **Acceptée** (validée par Sara le 2026-11-22)

### Contexte
Le fichier des splits (D-004) liste, pour chaque jeu, les **titres** des contrats CUAD
(`train`, `val`, `test`), avec la source, la graine et la date. Il ne contient **aucun texte de
contrat** (40 Ko). Pour la reproductibilité, Sara, Ilyas et l'encadrant doivent utiliser
**exactement** les mêmes jeux : si chacun régénère le fichier, une différence de version de
Python ou de code pourrait changer le tirage sans qu'on s'en aperçoive.

La règle absolue 5 interdit de commiter des données, avec une seule exception : `data/annotations/`
(D-003, références sans texte).

### Options envisagées
1. **Ne pas commiter** (fichier dans `data/processed/`, régénéré par chacun).
   - ➕ Aucune question vis-à-vis de la règle 5.
   - ➖ Reproductibilité fragile ; impossible de prouver quels contrats étaient dans le test.
2. **Commiter `data/splits/cuad_v1_splits.json`** et étendre l'exception de la règle 5 à
   `data/splits/`, aux mêmes conditions que D-003 (identifiants seulement, jamais de texte).
   - ➕ Un seul découpage de référence, historisé par Git : on peut montrer à l'encadrant que le
     test a été fixé **avant** le premier entraînement (date du commit).
   - ➕ Les titres sont des identifiants publics de CUAD, comme ceux déjà prévus par D-003.
   - ➖ Il faut modifier la règle 5 de `CLAUDE.md` et vérifier avant chaque commit qu'aucun texte
     n'est présent.
3. **Commiter seulement la recette** (graine + proportion + empreinte du fichier), pas les titres.
   - ➕ Pas de liste de titres dans le dépôt.
   - ➖ On ne voit pas les jeux sans relancer le script ; une empreinte différente dit qu'il y a un
     problème, pas lequel.

### Décision
**Option 2.** Emplacement : `data/splits/cuad_v1_splits.json` (déjà non ignoré par `.gitignore`,
qui n'ignore que `data/raw/*` et `data/processed/*`). Si Sara l'accepte : ajouter `data/splits/` à
l'exception de la règle 5 dans `CLAUDE.md`, au même titre que `data/annotations/`.

**Option 2, validée par Sara.** `CLAUDE.md` (règle 5) est mis à jour : `data/splits/` est la seconde exception, aux mêmes conditions que `data/annotations/` (identifiants seulement, jamais de texte). Le fichier est commité le 2026-11-22, avant tout entraînement.

### Conséquences
- Toute nouvelle version du découpage = nouveau fichier (`cuad_v2_splits.json`) et nouvelle
  décision ; on ne modifie jamais un fichier de splits déjà utilisé pour entraîner.
- Prévoir un test qui vérifie que les fichiers de `data/splits/` ne contiennent que des titres.

---

## D-006 — Protocole des baselines d'extraction (F2) et ordre du planning

- **Date** : 2026-11-22
- **Statut** : **Acceptée, confirmée par Sara le 2026-11-22**, à présenter à l'encadrant

### Contexte
Les données de l'étape 1 sont prêtes (splits D-004, segments v1). Il faut un point de comparaison
pour F2 et un protocole d'évaluation qui respecte la règle 2, avec un fort déséquilibre
(≈ 97 % de segments sans famille).

### Décision
1. **Ordre du planning** : la baseline d'extraction (étape 3) passe **avant** l'ingestion PDF et
   la base de données (étape 2). Raisons : données prêtes, résultat chiffré rapide, validation de
   la chaîne de bout en bout ; l'étape 2 commencera par vérifier sur quelques PDF du **train** que
   les segments PyMuPDF ressemblent aux segments CUAD.
2. **Tâche** : multi-étiquette, un classifieur oui / non par famille (durée, résiliation,
   responsabilité).
3. **Métriques** : précision, rappel, F1 par famille et macro-F1 ; **jamais l'exactitude globale**.
4. **Baseline 1 (mots-clés)** : liste écrite à la main depuis les définitions CUAD, **figée avant
   toute évaluation**.
5. **Baseline 2** : TF-IDF (`sublinear_tf`, `min_df=2`) + régression logistique
   `class_weight="balanced"` ; grille fixée à l'avance : n-grammes {1, 2} × C {0,1 ; 1 ; 10} ;
   seuil par famille de 0,05 à 0,95 ; tout est choisi par F1 **sur la validation**.
6. **Test fermé** : `charger_segments` refuse le test sans `ouvrir_test=True`.
7. **Suivi** : un run MLflow par baseline (base locale `mlflow.db`, non commitée).

### Raisons
- Une baseline simple dit si un modèle plus coûteux (Transformer) apporte vraiment quelque chose.
- Figer mots-clés et grille avant de voir les résultats évite de « régler à la main » sur la
  validation au-delà de ce qui est prévu.

### Conséquences
- Les métriques de validation sont **optimistes** (seuils réglés dessus) ; le chiffre de référence
  viendra du test, ouvert une seule fois à la fin de F2.
- Résultat 2026-11-22 : C = 10 (bord de la grille) retenu pour les 3 familles ; élargir la grille
  serait une nouvelle expérience, notée comme telle.

---

## D-007 — Méthode d'alignement des annotations CUAD sur le texte PDF (PyMuPDF)

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-23)**, à présenter à l'encadrant

### Contexte
Les positions des annotations CUAD portent sur le texte `context` de CUAD, pas sur le texte que
PyMuPDF extrait des PDF (limite 3 de `data_provenance.md`). Pour entraîner ou évaluer sur des
segments PDF avec leur page (règle 1), il faut retrouver chaque passage annoté dans le texte
PyMuPDF. Mesures sur les **347 contrats du train** (voir `docs/analyses/verification_pdf_pymupdf.md`).

### Options envisagées
1. **Correspondance exacte, normalisation des espaces seulement** : 70,7 % des annotations de nos
   9 catégories retrouvées.
   - ➕ La plus simple. ➖ Rate près d'un tiers des annotations (guillemets typographiques du PDF).
2. **Correspondance exacte, normalisation étendue** (espaces, minuscules, guillemets et tirets
   unifiés, ligatures, césures) : **98,3 %** (2 230 / 2 269) ; 99,3 % sur les 41 catégories.
   - ➕ Aucune position inventée : un passage est retrouvé tel quel, ou pas du tout.
   - ➕ Simple à expliquer et à tester ; ~0,1 s par contrat.
   - ➖ 1,7 % d'annotations perdues (39), dont des défauts du texte CUAD lui-même.
3. **Option 2 + repli approximatif** (recherche de la zone la plus ressemblante, par exemple avec
   `difflib`) pour les annotations restantes.
   - ➕ Récupérerait une partie des 1,7 %.
   - ➖ Risque de positions **fausses** (une zone qui ressemble n'est pas forcément la bonne), donc
     risque pour la traçabilité ; plus complexe ; il faudrait un seuil de ressemblance à régler.
4. **Ne pas aligner** : entraîner et évaluer uniquement sur le texte CUAD ; les PDF ne servent que
   dans l'application.
   - ➕ Aucun travail d'alignement.
   - ➖ Aucune mesure des modèles sur de vrais segments PDF, alors que c'est ce que verra l'application.

### Proposition de Claude
**Option 2.** Les annotations non retrouvées sont **comptées, listées (références seulement) et
exclues**, jamais placées approximativement. Le taux d'alignement est recalculé et affiché à
chaque préparation de données. L'option 3 pourra être réexaminée si le taux baisse sur d'autres
données.

### Décision
**Option 2** (Sara, 2026-11-23) : correspondance **exacte** après **normalisation étendue**. Les
annotations non retrouvées sont **comptées, listées par référence et exclues**, jamais placées
approximativement.

### Raisons
- 98,3 % des annotations de nos 9 catégories retrouvées sur le train, sans aucune position inventée.
- Pour la règle de traçabilité, une position fausse est pire qu'une annotation manquante.

### Conséquences
- `cg.ingestion.alignement` (niveau `"etendue"`) devient la méthode de référence ; ses tests
  font partie de la suite.
- Toute préparation de données à partir des PDF affiche le taux d'alignement et liste les
  annotations exclues (références seulement : titre, catégorie, positions CUAD).
- **Point lié** : la segmentation v1 sur le texte PDF produit une queue de segments coupés au
  plafond (18,8 % contre 6,6 % pour CUAD sur train + validation ; l'échantillon de 10 contrats
  avait exagéré l'écart). Voir **D-008**.
- Les pages sans texte (46 dans le train, aucun contrat entièrement scanné) sont signalées ; l'OCR
  reste hors périmètre.

---

## D-008 — Segmentation des PDF : texte brut (v1) ou blocs PyMuPDF

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-23)**, à présenter à l'encadrant

### Contexte
La baseline (D-006) a été entraînée sur des segments du **texte CUAD**. L'application segmentera
des **PDF** lus par PyMuPDF (D-007 pour l'alignement des annotations). Les segments doivent rester
traçables (page, positions) et ressembler le plus possible à ce que le modèle a appris.

Mesures sur les **408 contrats de train + validation** (test fermé), avec
`evaluation/comparer_segmentation_pdf.py` ; même règle de segmentation v1 (lignes vides, plafond
1 500 caractères) et même règle d'étiquetage (chevauchement ≥ min(20, longueur)) :

| | CUAD (référence) | PDF « texte » (v1 sur le texte brut) | PDF « blocs » (v1 sur les blocs PyMuPDF) |
|---|---|---|---|
| Segments | 66 253 | 44 996 | 96 244 |
| Longueur médiane | 153 | 148 | **83** |
| 90 % des segments sous | 1 008 | 1 455 | **647** |
| Segments < 20 caractères | 14,7 % | 27,0 % | 24,6 % |
| Segments ≥ 1 400 caractères (au plafond) | 6,6 % | **18,8 %** | **2,0 %** |
| Traçabilité (texte exact + segment dans sa page) | — | 100 % | 100 % |
| Annotations (nos 9) alignées (D-007) | — | 98,2 % | 98,2 % |
| … projetées sur ≥ 1 segment | — | 98,2 % | 98,2 % |
| … **entières dans un seul segment** | — | 89,1 % | **92,0 %** |
| Segments positifs : durée / résiliation / responsabilité | 1,40 / 0,91 / 0,84 % | 1,94 / 1,23 / 1,23 % | 0,95 / 0,64 / 0,66 % |

### Options envisagées
1. **v1 sur le texte brut PyMuPDF** (mode `"texte"`).
   - ➕ Médiane proche de CUAD ; moins de segments.
   - ➖ Près d'un segment sur cinq coupé au plafond : des clauses mélangées, coupées au hasard
     (dans les contrats où PyMuPDF ne laisse pas de lignes vides).
2. **v1 sur les blocs PyMuPDF** (mode `"blocs"`, un bloc = un paragraphe visuel).
   - ➕ Presque plus de segments coupés au plafond (2 %) ; plus d'annotations tiennent dans un
     seul segment (92,0 %) ; la mise en page du PDF guide le découpage.
   - ➖ Segments plus courts que CUAD (médiane 83) et plus nombreux : encore plus de déséquilibre
     (≈ 1 % de positifs par famille) ; un paragraphe coupé en plusieurs blocs donne plusieurs segments.
3. **Blocs + fusion des fragments** (par exemple rattacher un bloc très court au bloc suivant de la
   même page) : *non mesurée* ; viserait les 25 % de segments de moins de 20 caractères (titres,
   numéros, lignes isolées). Plus de règles, donc plus à expliquer et à tester.

### Proposition de Claude
**Option 2 (blocs)**, en gardant l'option 3 comme amélioration possible plus tard, à mesurer sur la
validation. Raisons : c'est la seule qui supprime presque tous les segments coupés au plafond ;
elle garde le plus d'annotations entières ; elle est aussi simple que l'option 1 (même code, un
paramètre `mode`).

### Décision
**Option 2** (Sara, 2026-11-23) : les PDF sont segmentés à partir des **blocs** PyMuPDF
(`extraire_pdf(..., mode="blocs")`, puis segmentation v1).

L'**option 3** (fusion des fragments très courts) sera testée **comme expérience** lors du
réentraînement de la baseline sur les segments PDF : son seuil sera réglé, et la comparaison faite,
**sur la validation uniquement**.

### Conséquences (quelle que soit l'option)
- **Aucune des deux segmentations PDF ne ressemble exactement aux segments CUAD.** Pour que le
  modèle apprenne sur ce qu'il verra dans l'application, il faudra **préparer les données
  d'entraînement à partir des PDF** (segments PDF + annotations alignées, D-007), puis
  **réentraîner et réévaluer la baseline** sur ces segments (validation seulement).
- Les segments PDF gardent leur page et leurs positions ; le test de traçabilité couvre les deux modes.

---

## D-010 — Base de données de l'application : PostgreSQL + pgvector dans Docker

- **Date** : 2026-11-23
- **Statut** : **Acceptée telle quelle (Sara, 2026-11-23)**, à présenter à l'encadrant

### Contexte
La stack prévoit PostgreSQL + pgvector, lancés avec Docker, pour la base de l'application :
contrats importés, segments avec provenance, résultats d'analyse, et plus tard vecteurs (F5).
C'est le « monde de l'application », distinct des données d'entraînement (`data/`).

### Choix proposés (chacun peut être changé)
1. **Image Docker figée** : `pgvector/pgvector:0.8.7-pg17` (PostgreSQL 17 + pgvector 0.8.7),
   pas `latest`. ➕ Même base pour tout le monde. ➖ Mise à jour = changement explicite du fichier.
2. **Accès local uniquement** : port publié sur `127.0.0.1:5432`, pas sur le réseau.
3. **Identifiants** : dans `.env` (jamais commité, mot de passe aléatoire), modèle sans vraie
   valeur dans `.env.example` (commité). Règle 5 respectée.
4. **Données persistantes** dans un volume Docker nommé (`cg_pgdata`) : elles survivent à
   `docker compose down` ; `docker compose down -v` les efface (action destructrice, à éviter).
5. **Schéma** (`db/init/001_schema.sql`) :
   - `contrats` : titre, source (`cuad` / `import`), nom et empreinte SHA-256 du fichier, mode
     d'extraction, **texte complet**, nombre de pages ;
   - `pages` : numéro, début, fin dans le texte complet ;
   - `segments` : page, début, fin, texte ; contraintes : `fin > debut`, page existante ;
   - `resultats` : rattachés à un segment (tâche, étiquette, score, modèle).
   Le texte complet est stocké pour que la traçabilité soit **vérifiable dans la base** :
   `substring(texte from debut + 1 for fin - debut) = texte du segment`.
6. **pgvector activé, sans colonne de vecteurs pour l'instant** : sa dimension dépend du modèle
   d'embeddings, qui sera choisi avec F5.
7. **Évolution du schéma** : fichiers SQL numérotés dans `db/init/` (exécutés à la création du
   volume). Pas d'outil de migration (Alembic) tant que le schéma est jeune ; à reconsidérer dès
   qu'une base contiendra des données à conserver.
8. **Accès depuis Python** : `psycopg` 3 (pilote officiel), requêtes SQL écrites à la main, **sans
   ORM** (SQLAlchemy) : plus simple à lire et à expliquer ; à reconsidérer avec l'API (F6).

### Alternatives écartées
- **SQLite** : plus simple, mais pas d'extension vectorielle prévue par la stack (pgvector) et
  différent de ce que l'application utilisera.
- **Image `latest`** : non reproductible.
- **Mot de passe dans `docker-compose.yml`** : il serait commité dans un dépôt public.

### Décision
**Les 8 choix ci-dessus sont acceptés tels quels** (Sara, 2026-11-23). L'implémentation provisoire devient l'implémentation de référence.

---

## D-011 — Données d'entraînement de F2 : segments du texte CUAD ou segments PDF ?

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-23)**, à présenter à l'encadrant

### Contexte
L'application segmentera des PDF par blocs (D-008). La baseline a été entraînée sur des segments
du texte CUAD. Comparaison sur la **validation** (test fermé), même protocole que D-006 : voir
`docs/analyses/baseline_segments_pdf_val.md`.

| Configuration | macro-F1 (mêmes segments PDF de validation) | macro rappel par annotation |
|---|---|---|
| entraîné sur CUAD, appliqué aux PDF | 0,643 | 0,719 |
| entraîné sur PDF blocs, sans fusion | 0,656 | 0,724 |
| entraîné sur PDF blocs, fusion 20 / 40 / 80 | (segments différents) | 0,720 / 0,720 / 0,723 |

Les écarts de rappel par annotation tiennent à 1 ou 2 annotations par famille : non significatifs.

### Options envisagées
1. **Garder l'entraînement sur le texte CUAD.** ➕ Rien à changer. ➖ Le modèle apprend sur des
   segments qui ne sont pas ceux de l'application ; F1 un peu plus bas (0,643).
2. **Entraîner sur les segments PDF blocs, sans fusion.** ➕ Mêmes segments à l'entraînement et
   dans l'application, avec la page (traçabilité) ; meilleur F1 sur les mêmes segments (0,656) ;
   aucune règle de plus. ➖ Dépend de l'alignement (1,8 % d'annotations exclues, D-007).
3. **Entraîner sur les segments PDF blocs, avec fusion** (seuil à choisir). ➕ Moins de fragments.
   ➖ Pas de gain mesurable sur le rappel par annotation ; une règle de plus à expliquer et à tester.

### Proposition de Claude
**Option 2.** À résultats équivalents, c'est la plus cohérente avec l'application et la plus
simple. La fusion (option 3) n'est pas retenue pour l'instant ; la fonction `fusionner_fragments`
reste disponible et testée si un modèle Transformer en tirait profit.

### Décision
**Option 2** (Sara, 2026-11-23) : F2 est entraînée sur les **segments PDF par blocs, sans fusion** (`cuad_pdf_segments_fusion0.jsonl`), avec les annotations alignées selon D-007. La fusion des fragments n'est pas retenue pour la baseline.

---

## D-009 — Famille « confidentialité » : adapter ContractNLI et choisir les exemples négatifs

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-23)**, à présenter à l'encadrant

### Contexte
D-002 : ContractNLI est la source réelle de la famille confidentialité. Trois questions restent :
quelles hypothèses comptent, comment segmenter son texte, et **d'où viennent les négatifs**.
Mesures sur le **train** et le **dev** de ContractNLI et la **validation** CUAD (tests fermés),
avec la baseline par mots-clés **figée avant toute évaluation** (commit `e44cdf8`).

### Faits mesurés
- **Segmentation** (train ContractNLI) : le texte n'a **aucune ligne vide** (un paragraphe par
  ligne). v1 telle quelle : médiane 1 285 caractères, 31,6 % au plafond, 55 % de positifs.
  v1 **coupée à chaque saut de ligne** : médiane 132, 90 % sous 674, 2,0 % au plafond (proche des
  segments PDF par blocs : 83 / 647 / 2,0 %), 21,1 % de positifs ; 98,4 % des évidences entières
  dans un segment. Spans ContractNLI (phrases) : médiane 101.
- **Baseline par mots-clés**, dev, segmentation coupée aux lignes :

| Option de négatifs | Segments | Positifs | Précision | Rappel | F1 |
|---|---|---|---|---|---|
| A. NDA seulement (négatifs = segments sans évidence) | 2 872 | 18,3 % | 0,433 | 0,877 | **0,580** |
| B. Positifs NDA + négatifs = segments PDF val CUAD | 11 992 | 4,4 % | 0,313 | 0,877 | 0,462 |
| C. Tous les segments NDA + segments PDF val CUAD | 14 337 | 3,7 % | 0,222 | 0,877 | 0,355 |

- **Bruit dans CUAD** : 8,8 % des segments PDF de validation CUAD contiennent un mot-clé de
  confidentialité, dans **51 contrats sur 61**. Les contrats commerciaux ont presque tous une
  clause de confidentialité, que CUAD n'annote pas.

### Options envisagées (négatifs)
1. **A — négatifs pris dans les NDA** (segments sans évidence).
   - ➕ Étiquettes cohérentes : une seule source, un seul protocole d'annotation (ContractNLI).
   - ➖ Seulement des NDA ; un segment qui parle de confidentialité sans être évidence d'une des 16
     hypothèses est compté négatif (bruit modéré).
2. **B ou C — négatifs pris dans CUAD**.
   - ➕ Plus proche de l'application (contrats commerciaux variés).
   - ➖ **Faux négatifs certains** : de vraies clauses de confidentialité de CUAD seraient étiquetées
     « non » ; l'évaluation serait faussement pessimiste et un modèle apprendrait surtout à
     distinguer « NDA » de « contrat commercial ».
3. **D — annotation humaine** (D-003) d'un échantillon de segments CUAD pour la confidentialité,
   par Sara et Ilyas avec un guide, pour un jeu d'évaluation **propre** dans des contrats
   commerciaux. ➕ La seule mesure fiable dans le domaine de l'application. ➖ Du temps d'annotation.

### Proposition de Claude
- **Hypothèses retenues** : les 16 hypothèses, **sans nda-18** (non-sollicitation).
- **Segmentation** : v1 **coupée à chaque saut de ligne** pour le texte de ContractNLI.
- **Négatifs** : **option A** pour l'entraînement et l'évaluation principale ; **option D** plus tard,
  comme jeu d'évaluation complémentaire dans des contrats commerciaux (à planifier avec l'encadrant).
- Ne pas utiliser CUAD comme réservoir de négatifs (B, C) tant qu'il n'est pas annoté pour la
  confidentialité.

### Décision
**Acceptée telle que proposée** (Sara, 2026-11-23) : segmentation de ContractNLI **coupée à chaque saut de ligne** ; **16 hypothèses sur 17** (nda-18 exclue) ; **négatifs pris dans les NDA** (option A). L'**option D** (annotation manuelle d'un échantillon CUAD par Sara et Ilyas, D-003) est **prévue plus tard**, comme jeu d'évaluation complémentaire.

---

## D-012 — Modèle Transformer pour F2 et ses réglages

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-23)**, à présenter à l'encadrant ; **valeur de la précision minimale du critère : proposée**

### Contexte
Après les baselines (D-006, D-011), F2 doit utiliser un modèle de langage préentraîné (stack :
PyTorch + Transformers), entraînable gratuitement sur le Mac de Sara (M4 Pro, 24 Go, puce
graphique MPS ; règle 4). Mesures : `docs/analyses/transformer_f2_val.md` (validation, tests fermés).

### Options envisagées (modèle)
1. **`nlpaueb/legal-bert-small-uncased`** (141 Mo, CC BY-SA 4.0) : BERT préentraîné sur des textes
   juridiques (dont des contrats EDGAR). ➕ Spécialisé, petit, ≈ 45 min pour 3 époques sur CUAD.
   ➖ Petit modèle ; contamination possible du préentraînement par des contrats EDGAR.
2. **`nlpaueb/legal-bert-base-uncased`** (440 Mo) : même famille, plus grand. ➕ Probablement
   meilleur. ➖ ≈ 3 fois plus long à entraîner.
3. **`microsoft/deberta-v3-small`** (286 Mo, MIT) : très bon en général, non spécialisé.

### Options envisagées (poids des positifs)
- Rapport négatifs / positifs (≈ 100 sur CUAD) : trop de fausses alertes (macro-F1 0,506).
- **Racine carrée du rapport** (≈ 10) : macro-F1 0,625, rappel par annotation 0,773.

### Proposition de Claude
- **Modèle** : legal-bert-small (option 1), réglages fixes (5e-5, 3 époques, lots de 32,
  256 tokens, graine 0), **poids des positifs = racine carrée du rapport** pour CUAD.
- Pour la confidentialité, garder le poids = rapport (≈ 4) : F1 0,862, meilleur que TF-IDF.
- **Garder TF-IDF comme référence** : sur les 3 familles CUAD, les deux sont proches (F1 par
  segment 0,656 contre 0,625 ; rappel par annotation 0,724 contre 0,773).
- Plus tard, si le temps le permet (expériences sur la validation) : plus d'époques (le modèle
  progressait encore), legal-bert-base.
- **Le choix du modèle évalué une seule fois sur le test** sera une décision séparée, à la fin de F2.

### Décision
**Acceptée** (Sara, 2026-11-23) : Legal-BERT small ; poids des positifs **atténué** (racine) pour
CUAD, **normal** (rapport) pour la confidentialité ; **TF-IDF gardé comme référence**.

### Critère de sélection des modèles de F2 (fixé le 2026-11-23, avant toute ouverture du test)
- **Critère principal** (Sara) : **rappel par annotation**, sous contrainte d'une **précision
  minimale** (précision par segment) ; **macro-F1 affiché en complément**.
- **Valeur proposée par Claude : précision ≥ 0,50 pour chaque famille** (« au moins une alerte sur
  deux est juste »), valeur ronde et compréhensible, non ajustée sur un modèle. *À confirmer par Sara.*
- **Procédure** : pour chaque modèle candidat et chaque famille, le seuil est choisi **sur la
  validation** = le plus petit seuil (rappel maximal) dont la précision atteint le minimum ; un
  modèle est admissible si toutes ses familles l'atteignent ; on retient l'admissible au **meilleur
  rappel par annotation** (macro sur les familles).
- **Règle 2** : le critère **choisit le modèle sur la validation**. Le modèle retenu (et ses seuils)
  est figé, puis **lui seul** est évalué **une fois** sur le test ; le test ne sert jamais à
  départager.
- **Mesures (validation, `evaluation/critere_selection_f2.py`)**, 3 familles CUAD :

  | Précision min. | TF-IDF : rappel annot. (P macro, F1 macro) | Transformer atténué | Transformer poids fort |
  |---|---|---|---|
  | 0,40 | 0,842 (0,405 ; 0,520) | 0,842 (0,407 ; 0,524) | 0,621 |
  | **0,50** | **0,794** (0,502 ; 0,573) | 0,742 (0,506 ; 0,550) | non admissible |
  | 0,60 | **0,761** (0,607 ; 0,619) | 0,697 (0,602 ; 0,576) | non admissible |

- **Conséquence (si 0,50 est confirmé)** : pour les 3 familles CUAD, **TF-IDF** est retenu (le
  Transformer retrouve moins de clauses de résiliation à précision égale : 0,438 contre 0,640) ;
  pour la confidentialité, le critère reste à appliquer (Transformer : P 0,852, R 0,873).
- **Confirmation de Sara (2026-11-23)** : précision minimale **0,50 par famille**, à condition que
  la comparaison soit équitable (pour chaque modèle et chaque famille, seuil réglé sur la validation
  pour maximiser le **rappel par annotation** sous précision ≥ 0,50).
- **Calcul refait à la lettre** (`evaluation/critere_selection_f2_equitable.py`, validation) :
  mêmes seuils et mêmes chiffres que le premier calcul.

  | Famille (annotations) | TF-IDF : seuil, rappel annot. | Transformer atténué : seuil, rappel annot. |
  |---|---|---|
  | durée (208) | 0,30 ; 0,870 | 0,27 ; **0,909** |
  | résiliation (89) | 0,54 ; **0,640** | 0,84 ; 0,438 |
  | responsabilité (116) | 0,27 ; 0,871 | 0,34 ; **0,879** |
  | **macro** | **0,794** | 0,742 |

- **La condition posée par Sara (« TF-IDF meilleur pour les 3 familles ») n'est pas remplie** :
  TF-IDF gagne en résiliation et en moyenne ; le Transformer gagne en durée (≈ 8 clauses) et, de
  peu, en responsabilité (≈ 1 clause). **Choix final pour les 3 familles CUAD : en attente de
  Sara** (option 1 : TF-IDF partout ; option 2 : meilleur modèle par famille, rappel macro 0,809).
- **Choix final (Sara, 2026-11-23) : option 2, meilleur modèle par famille**, décidé **sur la
  validation, avant toute ouverture du test** :
  - **durée** : Transformer (poids atténué), seuil 0,27 ;
  - **résiliation** : TF-IDF (bigrammes, C = 10), seuil 0,54 ;
  - **responsabilité** : Transformer (poids atténué), seuil 0,34 ;
  - **confidentialité** : Transformer (D-013) ; seuil sous le même critère à fixer sur le dev avant le test.
- **Mises en garde (Sara)** : l'écart avec « TF-IDF partout » est **petit** (rappel par annotation
  macro 0,809 contre 0,794) ; choisir le meilleur modèle **famille par famille sur la validation**
  rend ce chiffre **optimiste** (on a pris le maximum de deux mesures bruitées) ; **seul le test,
  ouvert une seule fois** avec le modèle et les seuils ci-dessus figés, donnera le résultat de référence.

---

## D-013 — Combiner CUAD et ContractNLI pour F2 : un modèle ou deux ?

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-23)**, à présenter à l'encadrant

### Contexte
Les 3 familles viennent de CUAD (segments PDF, D-011) ; la confidentialité vient de ContractNLI
(D-009). Les segments CUAD n'ont **pas** d'étiquette de confidentialité (et en contiennent souvent,
non annotée) ; les NDA de ContractNLI n'ont **pas** d'étiquettes de durée, résiliation ou responsabilité.

### Options envisagées
1. **Deux modèles** : un modèle 3 familles (CUAD), un modèle confidentialité (ContractNLI).
   ➕ Chaque modèle n'apprend que sur des étiquettes connues ; simple à expliquer. ➖ Deux modèles
   à charger dans l'application.
2. **Un seul modèle à 4 sorties, perte masquée** : on ignore la perte d'une famille quand sa source
   ne l'annote pas. ➕ Un seul modèle. ➖ Plus complexe ; risque d'apprendre « NDA ou non » plutôt
   que la clause.
3. **Un seul modèle, étiquettes manquantes considérées négatives**. ➖ Faux négatifs certains
   (D-009) : à écarter.

### Proposition de Claude
**Option 1** pour l'instant (implémentée et mesurée) ; l'option 2 pourra être testée plus tard
comme expérience, si charger deux modèles pose problème dans l'application.

### Décision
**Option 1** (Sara, 2026-11-23) : **deux modèles séparés** (3 familles CUAD ; confidentialité ContractNLI).

---

## D-014 — Méthode de F4 (NLI sur ContractNLI)

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-23)**, à présenter à l'encadrant

### Contexte
F4 : pour un contrat et une hypothèse, dire *Entailment*, *Contradiction* ou *NotMentioned* en
citant les évidences (traçabilité). Données : ContractNLI (D-002), 17 hypothèses (nda-18 incluse :
son exclusion, D-009, ne concernait que la famille confidentialité de F2). Mesures sur le **dev** :
`docs/analyses/nli_f4_dev.md`.

### Options envisagées
1. **Classe majoritaire par hypothèse** (baseline de l'article) : exactitude 0,681, macro-F1 0,633 ;
   aucune évidence.
2. **Paires (hypothèse, phrase) + agrégation au niveau du document** : exactitude 0,778,
   macro-F1 0,717, évidences F1 0,630. ➕ Chaque décision s'appuie sur des phrases citées, avec
   positions ; *NotMentioned* sert d'abstention. ➖ Ne voit qu'une phrase à la fois.
3. **Document entier (ou fenêtres de plusieurs phrases) par hypothèse** : pourrait mieux traiter
   les contradictions qui combinent plusieurs phrases. ➖ Plus long, plus de mémoire ; à tester plus tard.

### Proposition de Claude
**Option 2**, avec : unité = phrase de ContractNLI ; Legal-BERT small (D-012) ; échantillonnage
d'entraînement fixé avant l'entraînement (évidences + 2 neutres, dont une difficile) ; seuils
réglés sur le dev (document 0,85 ; évidence 0,95) ; baseline majoritaire gardée comme référence.

### Décision
**Option 2** (Sara, 2026-11-23) : paires (hypothèse, phrase) + agrégation au niveau du document ; seuils réglés sur le dev (0,85 ; 0,95) ; baseline majoritaire en référence.

---

## D-015 — Modèle d'embeddings et recherche hybride (F5)

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-23)**, à présenter à l'encadrant

### Contexte
F5 doit retrouver, dans un contrat, les segments qui répondent à une question : par les **mots**
et par le **sens** (recherche hybride), avec la base PostgreSQL + pgvector (D-010).

### Options envisagées (modèle d'embeddings)
bge-small-en-v1.5 (133 Mo, MIT, 384 dim.) ; all-MiniLM-L6-v2 (90 Mo, Apache 2.0, un peu moins bon en
recherche de passages) ; e5-small-v2 (133 Mo, MIT, comparable) ; nomic-embed-text-v1.5 (546 Mo,
Apache 2.0, meilleur sur les textes longs mais 4 fois plus gros).

### Décision
- **Embeddings : `BAAI/bge-small-en-v1.5`** (vecteurs de 384 nombres, normalisés ; préfixe
  d'instruction pour les questions).
- **Recherche hybride dans PostgreSQL** (`db/init/002_recherche.sql`) : par les mots = texte intégral
  PostgreSQL (`tsvector`, racinisation anglaise, requête en « OU ») ; par le sens = distance cosinus
  pgvector (index HNSW) ; **fusion RRF** (1 / (60 + rang)). La recherche se fait **dans un contrat**.

### Raisons
Petit, libre, parmi les meilleurs de sa taille pour retrouver des passages ; tout reste dans la base
de l'application (pas de moteur de recherche en plus).

---

## D-016 — LLM local pour la réponse générative de F5

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-23)**, à présenter à l'encadrant

### Contexte
Le cahier des charges demande un RAG avec un **modèle de langage local ou ouvert**, orchestré avec
**LangGraph** (chercher → vérifier la preuve → répondre ou s'abstenir), sans service payant (règle 4).
Le réseau est lent (≈ 166 Ko/s mesurés le 2026-11-23) : télécharger 5 Go prendrait des heures.

### Options envisagées
`qwen3:8b` (5,2 Go, Apache 2.0, texte) ; `qwen3:4b` (2,5 Go, plus rapide, moins fiable) ;
`qwen3-vl:8b` (6,2 Go, Apache 2.0, texte + images, **déjà présent** sur le Mac).

### Décision
- **`qwen3-vl:8b`, via Ollama** (déjà présent : aucun téléchargement), pour avancer.
- **Le nom du modèle est un simple paramètre de configuration** (`CG_LLM_MODELE`, voir
  `src/cg/config.py`) : on pourra passer à `qwen3:8b` et **comparer les deux sur la même évaluation**.
- **`qwen3:8b` reste l'option cible** si le réseau permet de le télécharger.
- **Lien avec l'extension OCR** prévue au cahier des charges : Qwen-VL sait lire des **images**
  (pages scannées) ; ce même modèle pourra servir à l'extension OCR des PDF scannés (46 pages sans
  texte repérées dans le train, D-007), sans nouveau téléchargement.

### Conditions d'usage
Mode « réflexion » désactivé, température 0 (réponses reproductibles) ; le LLM ne voit que les
passages retrouvés ; chaque citation est vérifiée **mot pour mot** dans le segment cité, sinon
**abstention** (D-017 à venir pour le détail du graphe).

### Constat technique et correction (2026-11-24) — à valider par Sara
- `qwen3-vl:8b` est la variante **« thinking »** de Qwen3-VL : il **réfléchit toujours**, même avec
  `think: false` ou `/no_think` (3 essais). En **température 0**, sa réflexion **tourne en boucle**
  (2 048 tokens, 9 350 caractères, aucune réponse).
- **Correction** : réglages recommandés par Qwen pour ses modèles « thinking » — température 0,6,
  top_p 0,95, top_k 20, **graine fixe (0)** pour rester reproductible, jusqu'à 4 096 tokens
  (`cg.config`, variables `CG_LLM_*`). Essai : JSON valide, citation vérifiée, ≈ 73 s par question.
- **Conséquence** : l'évaluation sur 200 questions prendrait ≈ 4 h ; une **évaluation indicative sur
  20 questions** est faite ; la mesure de référence reste à faire avec **`qwen3:8b`** (cible), dont la
  réflexion peut être vraiment désactivée, quand le réseau le permettra (≈ 53 Ko/s le 2026-11-24).
- **Correction acceptée** (Sara, 2026-11-24) : réglages recommandés par Qwen (température 0,6,
  top_p 0,95, top_k 20, graine fixe 0) ; l'évaluation sur 20 questions est présentée comme
  **INDICATIVE**.

### Plan : passer à un modèle sans réflexion obligatoire (Sara, 2026-11-24)
- **Modèle** : `qwen3-vl:8b-instruct` (existe dans la bibliothèque Ollama, ≈ 6,2 Go ; fichier principal
  5,0 Go) : variante « instruct » de Qwen3-VL, **sans réflexion obligatoire**, et qui **garde la
  vision** (utile pour l'extension OCR du cahier des charges). Choisi plutôt que `qwen3:8b`.
- **Téléchargement lancé le 2026-11-24 à 21:44**, en arrière-plan avec `caffeinate`
  (`nohup caffeinate -i ollama pull qwen3-vl:8b-instruct > data/processed/ollama_pull.log 2>&1 &`) ;
  ≈ 336 Ko/s, ≈ 4 h estimées. Ollama **reprend** un téléchargement interrompu (fichiers `-partial`).
- **Dès qu'il est téléchargé** : le configurer (`CG_LLM_MODELE=qwen3-vl:8b-instruct` dans `.env`),
  vérifier que la réflexion est bien coupée (température 0 possible), puis **refaire l'évaluation
  complète sur les 200 questions** (`evaluation/evaluer_rag_llm_f5.py --seuil-extractif 0.71`,
  sans `--taille`), qui deviendra la mesure de référence de F5.

---

## D-017 — Réglages de F5 : critère d'abstention et graphe RAG

- **Date** : 2026-11-23
- **Statut** : **Acceptée (Sara, 2026-11-24)**, à présenter à l'encadrant

### Contexte
F5 doit répondre en citant exactement, ou s'abstenir. Mesures : `docs/analyses/qr_f5_val.md`
(validation ; réglage sur 60 contrats du train ; test fermé).

### Propositions de Claude
1. **Critère de réglage du seuil d'abstention : l'exactitude équilibrée** (moyenne des bonnes
   réponses et des bonnes abstentions), et non l'exactitude simple, qui récompense l'abstention
   systématique quand 2/3 des questions n'ont pas de réponse. *Transparence : ce critère a été
   choisi après avoir vu l'échec du premier ; le défaut était néanmoins visible avant tout calcul.*
2. **Recherche** : hybride (RRF) ; extractif = premier résultat si similarité ≥ 0,71 (réglé sur le train).
3. **Graphe RAG** (LangGraph) : 5 passages de la recherche hybride ; LLM `CG_LLM_MODELE` (D-016),
   température 0, sans « réflexion », réponse JSON ; **toutes** les citations doivent exister mot
   pour mot (espaces normalisés seulement) dans le passage cité et faire au moins 15 caractères,
   sinon **abstention** ; chaque citation vérifiée reçoit ses positions dans le contrat.
4. **Comparaison extractif / LLM** sur les mêmes 200 questions de validation (graine 0), avec
   l'exactitude équilibrée comme mesure principale et le taux de réponses fausses en complément.

### Décision
**Acceptée** (Sara, 2026-11-24), avec deux précisions :
- **Le critère d'exactitude équilibrée a été choisi APRÈS l'échec du premier critère**
  (l'exactitude simple), en regardant **la validation uniquement** ; **le test n'a pas été touché**.
- **Réglages du graphe** : **5 passages** ; citations **vérifiées mot pour mot**, d'**au moins
  15 caractères** ; sinon **abstention**.

### Piste d'amélioration (séance 5/5)
Utiliser le **modèle NLI de F4** pour vérifier qu'un passage contient bien la réponse avant de
répondre (le passage « implique »-t-il la réponse du LLM ?), et **comparer** avec la vérification
actuelle (citation mot pour mot), sur les mêmes questions de validation.

---

## D-018 — Protocole de F3 (paires, annotation, kappa) et règle d'alerte v1

- **Date** : 2026-11-24
- **Statut** : **Acceptée (Sara, 2026-11-24)**, à présenter à l'encadrant

### Contexte
Le cahier des charges prévoit un mini-jeu de 30 à 50 paires de clauses annoté par Sara et Ilyas,
avec mesure du kappa de Cohen ; les alertes de F3 sont évaluées sur ces annotations. Claude prépare,
**n'annote pas**.

### Proposition de Claude
1. **Paires** : 47 paires de deux segments d'un même contrat de **validation** (test fermé), en
   4 types (fin du contrat ↔ renouvellement / préavis ; durée ↔ résiliation sans motif ; plafond ↔
   non plafonné ; résiliation sans motif ↔ obligations après la fin), choisies grâce aux annotations
   CUAD alignées (indépendant de tout modèle) ; 12 par type au plus, 2 par contrat et par type au
   plus, graine 0. Références dans `data/annotations/f3_paires/paires_v1.csv`.
2. **Grille** *(remplacée par D-020 : trois étiquettes du cahier des charges)* : `COMPATIBLES`, `A_VERIFIER`, `CONTRADICTION_APPARENTE`, `NON_COMPARABLE`
   (`docs/annotation/GUIDE_F3_PAIRES.md`) ; en cas de doute, `A_VERIFIER`. Annotation **indépendante**,
   puis kappa (4 étiquettes et « alerte oui/non »), discussion des désaccords, **étiquette de consensus**.
3. **Règle d'alerte v1, figée avant les annotations** (`docs/analyses/f3_alertes_v1_predictions.csv`,
   commité avant toute étiquette) : R1 NLI (≥ 0,5), R2 délais différents, R3 formule d'exception.
   Résultat brut : **41 alertes sur 47 paires** (R3 seule : 27 ; R1 : jamais) → règle **très peu
   sélective**, attendue avec une précision faible. Elle sert de **référence v1**, non modifiée.
4. **Évaluation** : précision, rappel et F1 de « alerte oui/non » contre le consensus ; et les mêmes
   mesures pour la référence triviale « toujours alerter ».
5. **Règle v2 éventuelle** : à concevoir après l'évaluation, mais **sans** la régler sur ces 47
   paires (elles serviraient alors deux fois) : il faudrait un nouveau lot de paires annotées.
6. **25 questions de F5** : rédigées par Sara et Ilyas (au moins 8 sans réponse), contrats de
   validation, références seulement (`docs/annotation/GUIDE_F5_QUESTIONS.md`).

### Décision
**Acceptée** (Sara, 2026-11-24), points 1 à 6 ci-dessus.

### Lien avec le cahier des charges (risque n°1)
La faiblesse de la règle v1 (41 alertes sur 47, R3 quasi partout) et le **non-transfert du NLI**
(R1 ne se déclenche jamais) correspondent au **risque n°1 prévu par le cahier des charges** : « le NLI
ne se transfère pas bien aux paires de clauses ». Son **plan de repli s'applique** : si les annotations
de Sara et d'Ilyas confirment cette faiblesse, la **détection inter-clauses sera présentée comme une
étude expérimentale**, **mesurée honnêtement** (précision, rappel, comparaison avec « toujours
alerter »), et non comme une fonctionnalité fiable.

---

## D-019 — Seuil de la confidentialité selon le critère de D-012, et architecture de F6

- **Date** : 2026-11-24
- **Statut** : **Acceptée (Sara, 2026-11-24)**, à présenter à l'encadrant

### Contexte
D-012 prévoyait de fixer le seuil de la confidentialité « sous le même critère, sur le dev, avant le
test ». Calcul (`evaluation/seuil_confidentialite.py`, dev ContractNLI, 2 872 segments, 1 198 phrases
d'évidence ; test fermé) :

| Seuil | Choisi par | Précision | Rappel (segments) | Rappel par évidence | F1 |
|---|---|---|---|---|---|
| **0,07** | critère D-012 (rappel par évidence max., précision ≥ 0,50) | 0,510 | 0,979 | **0,988** | 0,671 |
| 0,95 | F1 maximal (entraînement, D-012) | **0,852** | 0,873 | — | **0,862** |

### Options
1. **0,07 (critère à la lettre)** : ➕ cohérent avec les autres familles ; presque aucune clause
   manquée. ➖ une alerte sur deux fausse **dans des NDA** (18 % de segments positifs) ; dans un contrat
   commercial, où la confidentialité est bien plus rare, la précision serait **encore plus basse**.
2. **0,95 (F1 maximal)** : ➕ précision 0,85 pour un rappel de 0,87. ➖ s'écarte du critère commun.

### Architecture de F6 (implémentée)
API FastAPI (`src/cg/api/`) : importer un PDF, clauses (F2), questions (F5, RAG ou extractif),
alertes (F3, **expérimental**), hypothèse (F4) ; avertissement dans chaque réponse ; provenance de
chaque citation ; interface React (Vite) minimale (`frontend/`). Résultats de F2 enregistrés dans la
table `resultats` avec le nom du modèle (F7).

### Décision
**Acceptée** (Sara, 2026-11-24) :
- **Seuil de la confidentialité : 0,95.** C'est une **exception explicite au critère de D-012**,
  justifiée par la **différence de domaine** : le seuil est réglé sur des **NDA** (18 % de segments
  positifs), alors que l'application analyse des **contrats commerciaux**, où la confidentialité est
  bien plus rare ; la précision mesurée à 0,07 (0,51) y serait donc **surestimée**. **Décidé sur le
  dev, avant toute ouverture du test.**
- **Architecture de F6 : acceptée telle qu'implémentée.**

---

## D-020 — Grille d'annotation F3 alignée sur les trois étiquettes du cahier des charges

- **Date** : 2026-11-25
- **Statut** : **Acceptée (Sara, 2026-11-25)**

### Contexte
L'audit de conformité (`docs/AUDIT_CONFORMITE_2026-11-25.md`) a montré que la grille de D-018
(quatre étiquettes) ne suivait pas le cahier des charges, qui impose trois étiquettes pour F3 :
« potentiellement incompatible », « compatible », « information insuffisante ». **Aucune annotation
n'avait commencé.**

### Décision
Grille : `POTENTIELLEMENT_INCOMPATIBLE` (= alerte), `COMPATIBLE`, `INFORMATION_INSUFFISANTE`
(`docs/annotation/GUIDE_F3_PAIRES.md`, version 2) ; script du kappa et tests mis à jour. Le reste de
D-018 est inchangé (47 paires, annotation indépendante, kappa, consensus, règle v1 figée).

---

## D-021 — Cahier des charges de référence

- **Date** : 2026-11-25
- **Statut** : **En attente de l'encadrant** (question posée par Sara)

### Contexte
Deux documents existent : le **cahier des charges ContractGuardian** (11 pages, utilisé jusqu'ici) et
le **cahier des charges technique « ContractGuardian 360 »** de l'EMSI (version de travail du
03/11/2026). Ils diffèrent surtout sur la **comparaison de deux versions d'un contrat (V1/V2)** :
**extension** dans le premier, **obligatoire** (MVP, recette, scénario de soutenance) dans le second.

### Mesure conservatoire (Sara, 2026-11-25)
En attendant la réponse, la comparaison V1/V2 est **prévue en séance 4** (elle ne modifie aucun
modèle), pour être prête si elle est obligatoire.

### Décision
*En attente de l'encadrant.*

---

## D-022 — LLM de référence de F5 et vérification NLI dans le graphe RAG

- **Date** : 2026-11-26
- **Statut** : **Acceptée (Sara, 2026-11-26)**, telle que proposée

### Contexte
L'évaluation de référence (200 questions de validation, `docs/analyses/qr_f5_val.md`) a été faite avec
`qwen3-vl:8b-instruct`, comme prévu dans D-016. Résultats (exactitude équilibrée) : extractif 0,477 ;
RAG + LLM 0,529 ; **RAG + LLM + vérification NLI 0,561**. Le modèle répond en 8,1 s par question
(82 s pour `qwen3-vl:8b`), mais s'abstient trop peu (50 réponses sur 130 questions sans réponse).

### Options envisagées
1. **LLM de référence** : (a) `qwen3-vl:8b-instruct` ; (b) garder `qwen3-vl:8b` (« thinking »), 10 fois
   plus lent, non mesuré sur 200 questions.
2. **Vérification NLI dans le graphe** : (a) l'activer par défaut (étape « vérifier » : citation mot
   pour mot **et** passage qui implique la réponse) ; (b) la laisser comme piste d'évaluation seulement.
3. **Mode par défaut dans l'application** : (a) extractif (rapide) avec le LLM sur demande ; (b) LLM.

### Proposition de Claude
- **1(a)** : `qwen3-vl:8b-instruct` devient le LLM de référence (défaut de `CG_LLM_MODELE`).
- **2(a)** : activer la vérification NLI dans le graphe, car c'est la meilleure variante mesurée sur la
  validation (+0,032 d'exactitude équilibrée ; 61 % de réponses fausses au lieu de 70 %).
- **3(a)** : rester en extractif par défaut, LLM sur demande, avec la mention « réponse à vérifier ».
- Régler ensuite, **en séance 2 et avant le gel**, un seuil d'abstention par courbe couverture / erreur
  (sur la validation), puis refaire la mesure sur les 200 questions.

### Décision (Sara, 2026-11-26 : acceptée telle que proposée)
- **`qwen3-vl:8b-instruct`** est le LLM de référence : défaut de `CG_LLM_MODELE` (`src/cg/config.py`,
  `.env.example`).
- **Vérification NLI dans le graphe** : `src/cg/recherche/verification_nli.py` (modèle de F4, seuil 0,5
  fixé d'avance) ; l'étape « vérifier » garde une réponse seulement si au moins un passage cité
  l'implique, sinon abstention (« réponse non impliquée par les passages cités (NLI) »).
- **Application** : mode **extractif par défaut** (API et interface) ; le mode LLM est proposé sur demande,
  avec la mention « réponse générée par un LLM local : à vérifier dans le texte cité » (`a_verifier`) et
  le type de vérification appliqué (`verification`).
- **Suite** : seuil d'abstention par courbe couverture / erreur (validation) en séance 2, avant le gel.

---

## D-023 — Corpus documentaire explicatif : sources (F5, cahier des charges section 5)

- **Date** : 2026-11-26
- **Statut** : **Proposée** (en attente de la validation de la liste par Sara ; **rien n'est indexé**)

### Contexte
Le cahier des charges prévoit un **petit corpus documentaire explicatif** (sources ouvertes, datées)
indexé **séparément** des contrats, pour expliquer les termes et les clauses (durée, résiliation,
responsabilité, confidentialité). Ce corpus **n'est pas** une donnée d'entraînement (règle 3) : il
sert seulement de base au RAG.

### Critères de sélection (fixés avant la recherche)
1. Licence **explicite et ouverte**, vérifiée sur la page de la source : CC BY 4.0, CC BY-SA 4.0,
   Open Government Licence v3.0 (OGL), ou œuvre du gouvernement fédéral américain (domaine public,
   17 U.S.C. § 105). 2. Gratuite, sans compte. 3. Datée (date de publication, de mise à jour ou de
   révision). 4. Explicative (glossaire, guide, notice), pas un avis sur un cas particulier.

### Sources proposées (20 ; licences vérifiées le 2026-11-26)

| # | Titre | URL | Éditeur | Date | Licence | Raison |
|---|---|---|---|---|---|---|
| 1 | Non-disclosure agreement | https://en.wikipedia.org/wiki/Non-disclosure_agreement | Wikipédia | révision du 2026-11-18 | CC BY-SA 4.0 | Définition de l'accord de confidentialité, types (unilatéral, mutuel) |
| 2 | Confidentiality | https://en.wikipedia.org/wiki/Confidentiality | Wikipédia | révision du 2026-11-11 | CC BY-SA 4.0 | Notion générale de confidentialité |
| 3 | Trade secret | https://en.wikipedia.org/wiki/Trade_secret | Wikipédia | révision du 2026-11-25 | CC BY-SA 4.0 | Ce que protège une clause de confidentialité, durée de protection |
| 4 | Breach of contract (dont *material breach*) | https://en.wikipedia.org/wiki/Breach_of_contract | Wikipédia | révision du 2026-10-04 | CC BY-SA 4.0 | Manquement, manquement grave : motifs de résiliation |
| 5 | Termination for convenience | https://en.wikipedia.org/wiki/Termination_for_convenience | Wikipédia | révision du 2025-07-13 | CC BY-SA 4.0 | Résiliation sans faute |
| 6 | Fundamental breach | https://en.wikipedia.org/wiki/Fundamental_breach | Wikipédia | révision du 2026-10-10 | CC BY-SA 4.0 | Manquement fondamental et clauses limitatives |
| 7 | Rescission (contract law) | https://en.wikipedia.org/wiki/Rescission_(contract_law) | Wikipédia | révision du 2026-08-28 | CC BY-SA 4.0 | Distinguer résolution et résiliation |
| 8 | Exclusion clause | https://en.wikipedia.org/wiki/Exclusion_clause | Wikipédia | révision du 2024-10-17 | CC BY-SA 4.0 | Clauses d'exclusion et de limitation de responsabilité |
| 9 | Indemnity | https://en.wikipedia.org/wiki/Indemnity | Wikipédia | révision du 2026-06-05 | CC BY-SA 4.0 | Indemnisation (souvent liée au plafond de responsabilité) |
| 10 | Liquidated damages | https://en.wikipedia.org/wiki/Liquidated_damages | Wikipédia | révision du 2026-06-24 | CC BY-SA 4.0 | Pénalités et dommages forfaitaires |
| 11 | Consequential damages | https://en.wikipedia.org/wiki/Consequential_damages | Wikipédia | révision du 2026-05-22 | CC BY-SA 4.0 | Dommages indirects, souvent exclus par les contrats |
| 12 | Force majeure | https://en.wikipedia.org/wiki/Force_majeure | Wikipédia | révision du 2026-09-29 | CC BY-SA 4.0 | Exonération de responsabilité, suspension, résiliation |
| 13 | Non-disclosure agreements (guidance) | https://www.gov.uk/government/publications/non-disclosure-agreements/non-disclosure-agreements | UK Intellectual Property Office (GOV.UK) | 2015-03-12 | OGL v3.0 | Guide public : objet d'un NDA, durée usuelle de confidentialité (3 à 5 ans) |
| 14 | Managing intellectual property and confidentiality | https://www.gov.uk/government/publications/managing-intellectual-property-and-confidentiality | UK government (GOV.UK) | 2023 | OGL v3.0 | Guide pratique de la confidentialité |
| 15 | Risk allocation and pricing approaches guidance note | https://www.gov.uk/government/publications/the-sourcing-and-consultancy-playbooks/risk-allocation-and-pricing-approaches-guidance-note-html | Cabinet Office / Government Commercial Function | mise à jour 2026-11-05 | OGL v3.0 | Plafonds de responsabilité (limites spécifiques et générale) |
| 16 | Model Services Contract — Guidance for buyers (v2.2A) | https://www.gov.uk/government/publications/guidance-on-the-model-services-contract | Cabinet Office, Government Legal Department | mise à jour 2025-09-01 | OGL v3.0 | Guide commenté d'un contrat type : durée, résiliation, responsabilité, confidentialité |
| 17 | FAR Part 49 — Termination of Contracts | https://www.acquisition.gov/far/part-49 | US General Services Administration | FAC 2026-01, en vigueur le 2026-03-13 | Domaine public (œuvre fédérale, 17 U.S.C. § 105) | Résiliation pour convenance et pour faute, préavis écrit |
| 18 | WIPO Guide to Trade Secrets and Innovation | https://www.wipo.int/publications/en/details.jsp?id=4748 | WIPO (OMPI) | 2024 | CC BY 4.0 | Secrets d'affaires et accords de confidentialité, vue internationale |
| 19 | Common Paper Mutual NDA — Standard Terms v1.0 | https://commonpaper.com/standards/mutual-nda/1.0/ | Common Paper | 2021-07-19 | CC BY 4.0 | Clauses types annotées (exceptions, durée, restitution) |
| 20 | Bonterms Cloud Terms v1.0 | https://bonterms.com/forms/bonterms-cloud-terms-v1/ | Bonterms | 2022 | CC BY 4.0 | Clauses types de durée, résiliation, plafond de responsabilité, confidentialité |

### Sources écartées
- **Wex (Cornell LII)** : licence CC BY-NC-SA dans une version ancienne (2.5) et conditions générales
  différentes selon les pages : **licence floue**.
- Blogs de cabinets d'avocats, Investopedia, Law Insider : contenus protégés (tous droits réservés).
- Textes de loi nationaux (par exemple l'Unfair Contract Terms Act) : ce sont des règles de droit d'un
  pays, pas des explications ; risque de laisser croire à un avis juridique.

### Limites à connaître
- Sources **anglo-saxonnes** (Royaume-Uni, États-Unis) et en partie **marchés publics** (15 à 17) :
  elles expliquent des notions, elles ne disent pas le droit applicable à un contrat donné.
- 19 et 20 sont des **clauses types**, pas des guides : utiles comme exemples de rédaction ; à retirer
  si Sara préfère un corpus purement explicatif.
- CC BY-SA et CC BY imposent de **citer l'auteur et la licence** : l'interface affichera la source,
  la date et la licence de chaque passage explicatif.

### Mise en œuvre proposée (après validation)
- Téléchargement dans `data/raw/explicatif/` (**jamais commité**), avec la date de consultation ;
  provenance et licences dans `docs/data_provenance.md`.
- Index **séparé** des contrats : tables `sources_explicatives` et `segments_explicatifs` (texte,
  section, embeddings, `tsv`), jamais mélangées avec `segments`.
- Dans le RAG : les passages explicatifs sont montrés au LLM dans un **bloc séparé** ; une réponse sur
  le contrat doit toujours citer le **contrat** ; un passage explicatif est cité comme « document
  explicatif » avec sa source.

### Décision
*À compléter par Sara.*

---

## D-024 — Vrai BM25 pour la recherche par les mots (F5)

- **Date** : 2026-11-26
- **Statut** : **Proposée** (méthode fixée avant la mesure ; choix de la recherche à décider après)

### Contexte
L'audit a montré que la recherche « par les mots » utilisait `ts_rank_cd` de PostgreSQL, qui **n'est pas
BM25**, alors que le cahier des charges demande BM25 + embeddings (F5, ablations section 9).

### Méthode (fixée avant la mesure)
- **Mots** : ceux de PostgreSQL (lexèmes de `to_tsvector('english', …)`, colonne `tsv`), pour que la
  comparaison ne mesure que la **formule de classement**.
- **BM25 Okapi**, idf = ln(1 + (N − n + 0,5) / (n + 0,5)), calculé sur les segments **du contrat
  interrogé** (la recherche se fait dans un seul contrat) ; **k1 = 1,2 et b = 0,75**, valeurs usuelles,
  **non réglées**.
- Code : `src/cg/recherche/bm25.py` ; modes `bm25` et `hybride_bm25` de `rechercher` (le mode par défaut
  ne change pas tant que la décision n'est pas prise).
- **Comparaison** sur les mêmes questions de validation avec réponse (809), 10 premiers résultats :
  rappel@1, @3, @5, @10 et MRR, pour : texte intégral PostgreSQL, BM25, embeddings, hybride actuel,
  hybride BM25 (`evaluation/evaluer_recherche_bm25.py`).

### Options après la mesure (à décider par Sara)
(a) remplacer le texte intégral par BM25 dans l'hybride ; (b) garder l'hybride actuel et présenter BM25
comme ablation.

### Décision
*À compléter par Sara.*

---

## D-025 — Seuil d'abstention du RAG par courbe couverture / erreur (F5, amélioration 2)

- **Date** : 2026-11-26
- **Statut** : **Proposée** — **critère écrit AVANT tout calcul** (preuve : date du commit)

### Contexte
Sur la validation, le RAG s'abstient trop peu (D-022). L'audit prévoit de régler le seuil d'abstention
avec une **courbe couverture / erreur**, sur des questions de **réglage du train** (jamais la validation
pour régler, jamais le test).

### Ce qui est seuillé
La **probabilité « implique »** du modèle NLI de F4 : p = max, sur les passages cités, de
P(Entailment | passage, réponse). Une réponse vérifiée mot pour mot est gardée si p ≥ s, sinon
abstention. Seuils essayés : s = 0,05 ; 0,10 ; … ; 0,95, plus « sans NLI ». Aujourd'hui s = 0,5 (fixé
d'avance, D-017).

### Questions de réglage
Les questions des **60 contrats du train** déjà utilisés pour régler l'extractif (`evaluer_qr_f5.py`,
graine 0) ; **200 questions tirées avec la graine 0**, comme pour la validation. Mêmes réglages du LLM
(`qwen3-vl:8b-instruct`, 5 passages, recherche hybride actuelle).

### Définitions
- **Couverture** = réponses données / questions.
- **Erreur** = réponses fausses / réponses données (fausse = aucun segment annoté cité, y compris une
  réponse à une question sans réponse).
- **Exactitude équilibrée** = (bonnes réponses / questions avec réponse + bonnes abstentions /
  questions sans réponse) / 2.

### Critère proposé (à accepter AVANT le choix du seuil)
- **Option A (recommandée)** : le seuil qui **maximise l'exactitude équilibrée** sur les 200 questions
  de réglage ; en cas d'égalité, le **plus élevé** (le plus prudent). Cohérent avec D-017.
- **Option B** : le seuil le plus bas dont l'**erreur ≤ 30 %** (couverture maximale sous contrainte
  d'erreur) ; si aucun seuil n'y arrive, repli sur l'option A.
- Dans les deux cas : la courbe couverture / erreur est tracée et publiée ; le seuil choisi est
  ensuite **appliqué tel quel** aux 200 questions de validation (mêmes questions, même graine).

### Déroulement prévu
1. Collecter les réponses du LLM sur les 200 questions de réglage et leur probabilité NLI (ne dépend
   pas du critère). 2. **Attendre l'accord de Sara sur le critère.** 3. Choisir le seuil, tracer la
   courbe. 4. Mesurer sur la validation (étape 3 de la séance, avec le corpus explicatif).

### Décision
*À compléter par Sara.*

---

## D-026 — Mesure de la fidélité des réponses du RAG (F5, section 9)

- **Date** : 2026-11-26
- **Statut** : **Proposée** (méthode seulement ; **rien n'est implémenté avant l'accord de Sara**)

### Ce qu'on mesure
Une réponse est **fidèle** si **tout** ce qu'elle affirme est contenu dans les passages qu'elle cite.
Ce n'est **pas** l'exactitude : une réponse peut être fidèle à un passage qui ne répond pas à la question
(c'est déjà mesuré par l'exactitude), ou juste mais ajouter des éléments absents du passage (infidèle).

### Méthode proposée (trois niveaux)
1. **Référence humaine (mesure principale)** : Sara et Ilyas annotent **indépendamment** un échantillon
   de **50 réponses données** par le RAG sur la validation (tirées avec la graine 0), avec trois
   étiquettes : `FIDELE` (tout est dans le passage cité), `PARTIELLEMENT_FIDELE` (un élément n'y est
   pas, ou est généralisé), `NON_FIDELE` (contredit ou invente). Kappa de Cohen, puis référence par
   consensus. Fichiers d'annotation **sans texte** (identifiants seulement, règle 5), comme pour F3.
2. **Contrôle automatique des éléments critiques** (indépendant des modèles) : on extrait de la réponse
   les **nombres, durées, montants, pourcentages et dates** (« 30 days », « two years », « $1,000,000 »)
   et on vérifie que chacun figure dans les passages cités (en reconnaissant « thirty (30) » = « 30 »).
   Mesure : part des réponses dont tous les éléments critiques sont retrouvés.
3. **Score NLI** (modèle de F4) : probabilité que les passages cités impliquent la réponse. Rapporté
   **à titre indicatif seulement**.

Écarté : **un LLM juge** (le même LLM local jugerait ses propres réponses : biais d'auto-évaluation ;
un autre LLM demanderait un nouveau téléchargement et ne serait pas validé).

### Limites
- **50 réponses** : intervalle de confiance large (environ ± 14 points à 95 %) ; c'est une estimation,
  pas une preuve. Coût : environ 1 heure d'annotation chacun.
- Le contrôle des éléments critiques **ignore les paraphrases et les négations** (« may » contre
  « may not ») : il ne détecte que les chiffres et dates inventés.
- Le score NLI **n'est pas indépendant** : le même modèle filtre déjà les réponses (D-022), donc il
  surestime la fidélité ; et il a été entraîné sur des NDA (ContractNLI), pas sur des réponses de RAG.
- Les annotateurs connaissent le système : risque de complaisance ; le guide fixera des règles écrites
  (comme pour F3).

### Décision
*À compléter par Sara.*
