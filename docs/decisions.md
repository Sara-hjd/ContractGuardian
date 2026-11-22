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
- **Statut** : Proposée

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
- La règle de découpage (paragraphe, clause numérotée…) reste à définir et à documenter.

---

## D-002 — La famille « confidentialité » est absente de CUAD

- **Date** : 2026-11-15
- **Statut** : Proposée, **à valider avec l'encadrant**

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
*À prendre avec l'encadrant.*

### Raisons
*À compléter après validation.*

### Conséquences
- Selon l'option : temps d'annotation à prévoir (option 2), ou périmètre de F2 réduit (option 3).
- Dans tous les cas, les résultats de la famille confidentialité seront présentés à part
  et non comparés directement aux trois autres familles.

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
- **Statut** : Proposée, **à trancher avec Sara (et l'encadrant)**

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
   - ➕ Résultats **comparables à l'article** et aux autres travaux sur CUAD.
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
*À prendre ensemble.*

### Raisons
*À compléter après la décision.*

### Conséquences (quelle que soit l'option)
- Le découpage se fait **par contrat** et est **enregistré dans un fichier** (liste des titres
  par jeu), versionné ; il ne contient aucun texte de contrat.
- Le jeu de test n'est **ouvert qu'une fois**, pour l'évaluation finale (règle 2). Les explorations
  déjà faites portent sur tout CUAD mais sont descriptives : elles n'ont réglé aucun modèle.
- Les catégories rares seront présentées avec leur nombre d'exemples de test, pour rappeler
  l'incertitude des mesures.
- Nos futures annotations humaines (D-002, D-003) devront respecter le même découpage si elles
  portent sur des contrats CUAD.
