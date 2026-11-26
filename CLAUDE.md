# CLAUDE.md — ContractGuardian

Ce fichier est lu par Claude Code au début de chaque session. Il décrit le projet,
la façon de travailler et les règles à respecter. Le tenir à jour quand une décision change.

## Le projet

**ContractGuardian** est un PFA de l'EMSI réalisé en binôme par **Sara-hjd** et **ILyas394**.

C'est un outil d'aide à la lecture de **contrats commerciaux rédigés en anglais**. Il doit :

1. **Extraire les clauses** suivantes : durée, résiliation, responsabilité, confidentialité.
2. **Détecter avec prudence les incohérences** entre clauses. En cas de doute, il signale
   un point à vérifier, il n'affirme pas qu'il y a une contradiction.
3. **Répondre aux questions** sur un contrat, soit en **citant exactement** le texte source,
   soit en **s'abstenant** s'il ne trouve pas de réponse fiable.

⚠️ L'outil **ne donne jamais d'avis juridique**. Il aide à lire, il n'interprète pas le droit.

## Stack prévue

| Rôle | Outil |
|---|---|
| Langage | Python 3.11 |
| Lecture des PDF | PyMuPDF |
| Modèles classiques (baselines) | scikit-learn |
| Modèles de langage | PyTorch + Hugging Face Transformers |
| API | FastAPI |
| Base de données et recherche vectorielle | PostgreSQL + pgvector, lancés avec Docker |
| Interface | React |
| Suivi des expériences | MLflow |

### Python : toujours passer par `.venv`

Sur cette machine, `python3` pointe vers **Python 3.9** (la version de macOS).
**Ne jamais utiliser `python3` directement.**

```bash
python3.11 -m venv .venv        # création, une seule fois
source .venv/bin/activate       # à chaque nouveau terminal
python --version                # doit afficher 3.11.x
```

Toutes les commandes Python (`python`, `pip`, `pytest`…) se lancent avec le `.venv` activé,
ou bien via `.venv/bin/python`.

### Docker

Docker Desktop doit être lancé (`open -a Docker`) avant d'utiliser PostgreSQL et pgvector.

## Façon de travailler

Sara est **en apprentissage**. Concrètement :

- **Avant de coder**, expliquer les notions nouvelles : le concept, à quoi il sert ici,
  et un petit exemple.
- **Travailler par petites étapes**, une seule chose à la fois.
- **Proposer un plan et attendre l'accord** avant de modifier plusieurs fichiers.
- **Après chaque modification**, expliquer :
  - ce qui a changé,
  - pourquoi,
  - comment le tester (commande exacte et résultat attendu).

## ⚠️ Mode « Claude exécute tout » — SANS LIMITE DE SÉANCES (jusqu'à l'instruction « stop » de Sara)

> **À lire en premier à chaque début de séance.** Tant que ce mode est actif, il **remplace**
> la section « Qui exécute les commandes » ci-dessous. Il ne change **aucune règle absolue**.

- **Décidé par** : Sara, le 2026-11-24 ; **début** : 2026-11-24 (séance du 25/11 = séance 1).
- **Historique** : mode de 3 séances (22-23/11, bilan `docs/DIAGNOSTIC_2026-11-16_au_2026-11-23.md`) ;
  mode de 5 séances (23-24/11, bilan `docs/DIAGNOSTIC_2026-11-23_au_2026-11-24.md`).
- **Compteur** (Claude ajoute une ligne à la fin de chaque séance) :

  | Séance | Date | Contenu |
  |---|---|---|
  | 1 | 2026-11-25 → 26 | Audit de conformité ; grille F3 à 3 étiquettes (D-020) ; D-021 en attente ; RAG de référence sur 200 questions avec qwen3-vl:8b-instruct ; D-022 proposée |

- **Fin** : **uniquement sur instruction explicite de Sara** (« stop »). Claude marque alors cette section
  « terminée » et la règle habituelle « Sara exécute les commandes » reprend.
- **Une séance** = une session de travail ouverte par Sara (en général « Début de séance »)
  et close par le résumé de fin de séance et la mise à jour de `docs/PROGRESS.md`.

**Pendant ce mode, Claude exécute la totalité des commandes, sans demander l'accord à chaque
fois** : installations, téléchargements documentés, scripts, tests, `git add` / `commit` /
`push`, création et fusion de PR, Docker.

**Restent INTERDITS, même dans ce mode** (Claude s'arrête et demande à Sara) :
- `git push --force` (ou toute variante qui écrase l'historique distant) ;
- réécrire l'historique de `main` (rebase, reset, amend de commits déjà poussés) ;
- supprimer des données dans `data/raw/` ;
- ouvrir le jeu de test sans **décision écrite** de Sara dans `docs/decisions.md` ;
- commiter des données, des modèles entraînés ou des secrets (règle absolue 5 et ses exceptions) ;
- toute action **irréversible non prévue dans le plan de la séance**.

**Décisions de fond** : Claude les **propose** (options, mesures, recommandation) ; elles ne sont
notées « Acceptée » qu'après la décision de Sara. **Annotations humaines** (F3, questions F5) : faites
par Sara et Ilyas, **jamais par Claude**.

**Obligations pendant ce mode** :
- **Début de séance** : relire ce fichier et `docs/PROGRESS.md`, annoncer le numéro de séance et le plan.
- **Chaque action** est notée dans `docs/JOURNAL_ACTIONS.md` : heure, commande exacte,
  explication simple, pourquoi, résultat, fichiers touchés, commit.
- **Fin de séance** :
  - un **résumé court et simple (10 lignes maximum)** : ce qui a été fait, les chiffres clés, et
    ce que Sara doit savoir expliquer ; plus ce qu'Ilyas doit relire ;
  - mise à jour de `docs/PROGRESS.md` (avec « Ce que j'ai compris »), du `README.md` et de
    `docs/FICHE_ENCADRANT.md` ; ajout d'une ligne au compteur ci-dessus.

## Qui exécute les commandes

**Sara exécute elle-même toutes les commandes** dans le terminal de VS Code, de l'installation
jusqu'à la fin du projet :

- création du `.venv` et `pip install`,
- Git (`add`, `commit`, `push`, `branch`, `merge`…),
- Docker,
- lancement des scripts, des tests, de l'API et du frontend.

**Claude ne lance pas ces commandes.** Pour chaque commande, Claude donne :

1. la **commande exacte** dans un bloc de code ;
2. **ce qu'elle fait**, mot par mot si elle contient des options ;
3. le **résultat attendu** ;
4. puis **attend que Sara colle le résultat obtenu** avant de continuer.

Si le résultat est une **erreur**, Claude explique l'erreur et propose une correction,
que Sara exécute à son tour.

**Exception : les commandes en lecture seule.** Claude peut lancer lui-même, sans demander,
les commandes qui servent à se documenter ou à vérifier un état **sans rien modifier** :

- `git status`, `git log`, `git diff`, `git branch` (sans option de création ni de suppression) ;
- `gh repo view`, `gh pr view`, `gh api` en lecture (requêtes GET uniquement) ;
- `ls`, `cat`, `head`, `md5`, `du`, `wc`, et autres consultations de fichiers ;
- la consultation de pages web.

Claude dit alors simplement ce qu'il a lancé et ce qu'il a trouvé.

**Tout ce qui modifie quelque chose reste à Sara** : installations, téléchargements,
création ou suppression de fichiers par commande, `git add` / `commit` / `push` / `merge` /
`branch` (création ou suppression), Docker, lancement de scripts, de tests ou de l'API.
En cas de doute sur le caractère « lecture seule » d'une commande, la donner à Sara.

**Fichiers :**

- Claude **peut créer et modifier des fichiers** (code, documentation). Il doit d'abord
  dire quel fichier il va créer ou modifier et pourquoi, puis en expliquer le contenu après.
- Claude **peut lire les fichiers du projet** pour comprendre leur état (voir l'exception
  « lecture seule » ci-dessus).

## Documentation du code

- **Docstring en tête de chaque module** : rôle du fichier, et sa place dans le projet.
- **Docstrings au style Google** pour les fonctions et les classes (`Args:`, `Returns:`, `Raises:`).
- **Annotations de type partout** : paramètres, valeurs de retour, attributs.
- **Les commentaires expliquent le pourquoi**, pas le quoi.
- **Chaque sous-dossier de `src/cg/` contient un `README.md`** qui décrit son rôle et son contenu.

Exemple :

```python
"""Découpage d'un contrat PDF en segments avec leur provenance."""


def extract_segments(pdf_path: str) -> list[Segment]:
    """Extrait les segments de texte d'un PDF.

    Args:
        pdf_path: Chemin vers le fichier PDF du contrat.

    Returns:
        La liste des segments, chacun avec sa page et ses positions.
    """
```

## Règles absolues

Ces règles ne se négocient pas. Si une demande semble les contredire, s'arrêter et poser la question.

1. **Traçabilité** : toute sortie (clause, incohérence, réponse) référence un segment du
   contrat avec sa **provenance** (numéro de page, positions de début et de fin).
2. **Données de test intouchables** : ne jamais utiliser les données de test pour régler
   un modèle (hyperparamètres, seuils, choix de modèle). Pour cela, utiliser le jeu de validation.
3. **Aucune donnée synthétique pour l'entraînement**. Sources autorisées uniquement :
   **CUAD**, **ContractNLI**, et des **annotations humaines sur des contrats réels**.
4. **Aucun service payant obligatoire** : le projet doit fonctionner entièrement avec des
   outils gratuits ou en local.
5. **Ne jamais commiter** de données, de modèles entraînés ou de secrets (`.env`, clés,
   tokens). Le dépôt GitHub est **public**.
   - **Deux exceptions seulement**, qui ne contiennent **jamais le texte des contrats** :
     - **`data/annotations/`** (décision D-003). Nos propres annotations, sous forme de
       références : identifiant du contrat (CUAD ou document), positions de début et de fin,
       étiquette, annotateur, date.
     - **`data/splits/`** (décision D-005). Les fichiers de découpage train / validation / test :
       identifiants de contrats (titres CUAD) et paramètres du tirage (source, graine,
       proportion, date), rien d'autre.
   - Avant chaque commit touchant ces dossiers, vérifier qu'aucun extrait de texte n'y figure.

## Git

- Dépôt : https://github.com/Sara-hjd/ContractGuardian (déjà relié en tant que `origin`).
  Branche principale : `main`.
- **Une branche par tâche** (par exemple `feat/pdf-extraction`).
- Format des messages de commit : `type(module): description`. Types autorisés :

  | Type | Usage |
  |---|---|
  | `feat` | nouvelle fonctionnalité |
  | `fix` | correction de bug |
  | `docs` | documentation |
  | `test` | tests |
  | `refactor` | réorganisation du code sans changer son comportement |
  | `exp` | expérience (entraînement, évaluation) |
  | `chore` | maintenance (configuration, dépendances) |

- **Ne jamais pousser (`push`) ni fusionner (`merge`) sans demande explicite de Sara.**
- Avant tout commit, vérifier avec `git status` qu'aucun fichier interdit n'est inclus
  (voir la règle absolue 5).

## Suivi de l'avancement : `docs/PROGRESS.md`

**À chaque fin de séance, Claude met à jour `docs/PROGRESS.md`** :

- ce qui a été fait ;
- l'**avancement** : statut des fonctionnalités F1 à F7 et étape du planning ;
- la rubrique **« Ce que j'ai compris »**, rédigée de façon pédagogique : notions vues,
  pourquoi on les utilise, comment elles s'enchaînent dans le projet.

Sara relit la rubrique « Ce que j'ai compris » et la corrige si besoin.

Claude met aussi à jour le **tableau de statut des fonctionnalités du `README.md`**
quand une fonctionnalité avance.
