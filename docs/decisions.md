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
- **Statut** : **Proposée, à décider par Sara** (implémentation provisoire en place, modifiable)

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
*À prendre par Sara.*

---

## D-011 — Données d'entraînement de F2 : segments du texte CUAD ou segments PDF ?

- **Date** : 2026-11-23
- **Statut** : **Proposée, à décider par Sara**

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
*À prendre par Sara.*
