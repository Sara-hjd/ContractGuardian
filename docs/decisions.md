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
