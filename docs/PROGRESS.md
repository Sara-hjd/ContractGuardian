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

## 2026-11-15 — Mise en place du projet

- **Qui** : Sara-hjd (avec Claude Code)
- **Durée** : *à compléter*
- **Branche** : `main` (aucun commit pour l'instant)
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

- **Étape du planning** : étape 0, mise en place (environnement, dépôt, documentation).
  Le planning détaillé reste à établir avec l'encadrant.

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

### Décisions
- D-001 (proposée) : le segment comme unité de base.
- D-002 (proposée) : la famille confidentialité est absente de CUAD, à valider avec l'encadrant.

### Preuves
- `git ls-remote origin` : code de sortie 0, sortie vide (dépôt vide accessible).
- Invitation GitHub créée le 2026-11-15 pour ILyas394, permission `write`.

### Prochaine étape
- Premier commit `docs: initialiser la documentation du projet` et push sur `main`.
- Vérifier que ILyas394 a accepté l'invitation.
- Créer le `.venv` en Python 3.11.
