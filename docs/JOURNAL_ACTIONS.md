# Journal des actions exécutées par Claude Code

Ce journal trace **chaque action** que Claude Code a exécutée lui-même, quand Sara l'y a
autorisé par une exception ponctuelle à la règle « Sara exécute les commandes » (CLAUDE.md).
Il sert à réexpliquer chaque étape plus tard : Claude n'a pas de mémoire d'une séance à l'autre.

Pour chaque action : heure, commande exacte, explication simple, pourquoi, résultat,
fichiers touchés, commit.

---

## Séance du 2026-11-22 — exception « Claude exécute »

**Périmètre accordé par Sara, pour cette séance uniquement :**
- Autorisé : exécuter le notebook et les scripts avec le `.venv`, créer ou modifier des
  fichiers, `git add` et `git commit` sur `exp/exploration-cuad`, télécharger des données
  documentées.
- Soumis à l'accord préalable de Sara : `git push`, toute fusion, toute suppression, toute
  installation de dépendance, toute action sur `main` ou qui touche GitHub.
- À la séance suivante, la règle habituelle s'applique de nouveau : Sara exécute les commandes.

**Branche** : `exp/exploration-cuad` (dernier commit au début : `26f4188`).

### A1 — 03:56 — Vérifier l'environnement (lecture seule)

- **Commande** :
  ```bash
  date "+%Y-%m-%d %H:%M" && .venv/bin/python --version && ls .venv/bin | grep -E "jupyter|ipython" \
    && .venv/bin/jupyter kernelspec list && jq '.metadata.kernelspec' notebooks/01_exploration_cuad.ipynb
  ```
- **Explication** : affiche l'heure, la version du Python du `.venv`, les outils Jupyter
  installés, les noyaux connus, et le noyau demandé par le notebook.
- **Pourquoi** : avant d'exécuter le notebook, vérifier qu'il tournera avec le bon Python.
- **Résultat** : Python 3.11.18 ; Jupyter présent dans le `.venv` ; le noyau `python3` pointe
  vers `.venv/share/jupyter/kernels/python3`, et c'est celui que demande le notebook.
- **Fichiers touchés** : aucun.
- **Commit** : aucun.

### A2 — 03:56 — Créer ce journal

- **Action** : création de `docs/JOURNAL_ACTIONS.md` avec l'outil d'écriture de fichiers
  (pas de commande shell).
- **Pourquoi** : demande de Sara, pour tracer chaque action de la séance.
- **Fichiers touchés** : `docs/JOURNAL_ACTIONS.md` (créé).
- **Commit** : à venir (étape 5).

### A3 — 03:56 — Exécuter le notebook en le réécrivant (refusé)

- **Commande** :
  ```bash
  .venv/bin/jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.kernel_name=python3 --ExecutePreprocessor.timeout=600 \
    notebooks/01_exploration_cuad.ipynb
  ```
- **Explication** : `nbconvert --execute` exécute toutes les cellules dans l'ordre, sans ouvrir
  VS Code ; `--inplace` réécrit le notebook avec ses sorties ; `kernel_name=python3` choisit le
  noyau du `.venv` ; `timeout=600` laisse 10 minutes au plus par cellule.
- **Résultat** : **refusé** par le contrôle de sécurité de Claude Code (réécriture d'un fichier
  existant). Rien n'a été modifié.
- **Fichiers touchés** : aucun. **Commit** : aucun.

### A4 — 03:56 — Exécuter le notebook vers une copie temporaire

- **Commande** :
  ```bash
  .venv/bin/jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.kernel_name=python3 --ExecutePreprocessor.timeout=600 \
    --output-dir <dossier temporaire de la séance> --output 01_exploration_cuad_execute.ipynb \
    notebooks/01_exploration_cuad.ipynb
  ```
- **Explication** : même exécution, mais le résultat (cellules + sorties) est écrit dans une
  **copie** hors du dépôt ; le notebook d'origine n'est pas touché.
- **Pourquoi** : contourner le refus de A3 de la façon la plus sûre ; en bonus, le notebook du
  dépôt ne contient jamais de sorties (donc jamais d'extrait de contrat).
- **Résultat** : 18 cellules de code exécutées, **aucune erreur**. Sorties lues avec `jq`.
- **Fichiers touchés** : la copie temporaire seulement (hors dépôt). **Commit** : aucun.

### A5 — 03:57 — Ajouter les cellules f.3 et g.3

- **Action** : 4 cellules insérées dans le notebook (outil d'édition de notebook) :
  - **f.3** (Markdown + code) : compte les passages *Uncapped Liability* qui ont exactement les
    mêmes positions qu'un passage *Cap On Liability* du même contrat.
  - **g.3** (Markdown + code, fonction `nb_omitted`) : compte les `<omitted>` du CSV et teste
    « passages JSON = éléments CSV + `<omitted>` ».
- **Pourquoi** : la première exécution montrait que les 111 contrats *Uncapped* avaient tous *Cap*,
  et que le CSV donnait exactement 13 101. Il fallait vérifier ces deux pistes par des chiffres.
- **Fichiers touchés** : `notebooks/01_exploration_cuad.ipynb` (38 → 42 cellules).
- **Commit** : voir A9.

### A6 — 03:57 — Réexécuter le notebook complet (copie temporaire)

- **Commande** : la même qu'en A4.
- **Résultat** : aucune erreur. f.3 : 125 passages *Uncapped* sur 167 sont aussi *Cap* ; 73 contrats
  sur 111 ont tous leurs passages *Uncapped* aussi *Cap*. g.3 : 733 `<omitted>` ; CSV + `<omitted>`
  = 13 834 pour 13 823 passages JSON ; égalité exacte pour 32 catégories sur 41.
- **Fichiers touchés** : la copie temporaire seulement. **Commit** : aucun.

### A7 — ~04:00 — Consulter le dépôt GitHub de CUAD (lecture seule)

- **Commandes** :
  ```bash
  gh api repos/TheAtticusProject/cuad/contents --jq '.[] | "\(.type) \(.name) \(.size)"'
  gh api repos/TheAtticusProject/cuad/contents/run.sh --jq .content | base64 -d
  ```
  (plus deux consultations de pages web avec l'outil WebFetch).
- **Explication** : requêtes GET, qui lisent la liste des fichiers du dépôt CUAD et le script
  `run.sh` ; `base64 -d` décode le contenu renvoyé par l'API.
- **Pourquoi** : préparer D-004 avec des faits, pas des suppositions.
- **Résultat** : `data.zip` (18 Mo) existe ; `run.sh` entraîne sur
  `data/train_separate_questions.json` et évalue sur `data/test.json` ; pas de fichier de validation.
  Rien n'a été téléchargé.
- **Fichiers touchés** : aucun. **Commit** : aucun.

### A8 — ~04:05 — Rédiger les Conclusions, D-004 et l'entrée de PROGRESS

- **Actions** :
  - cellule « Conclusions » du notebook remplie, puis relue : un extrait de date d'un contrat a
    été retiré (dépôt public) ;
  - D-004 ajoutée à la fin de `docs/decisions.md` avec `cat >> docs/decisions.md <<'EOF' … EOF`
    (`>>` ajoute à la fin du fichier sans effacer le reste) ;
  - entrée du 2026-11-22 ajoutée à `docs/PROGRESS.md`, avec la mention de l'exception.
- **Vérification** : `jq` sur le notebook : 20 cellules de code, **0 avec sortie**, 0 exécutée.
- **Fichiers touchés** : `notebooks/01_exploration_cuad.ipynb`, `docs/decisions.md`,
  `docs/PROGRESS.md`, ce journal.
- **Commit** : A9 (notebook, PROGRESS, journal) et A11 (D-004, fiche encadrant).

### A9 — Premier commit : notebook, PROGRESS, journal

- **Commandes** :
  ```bash
  git status --short
  git add notebooks/01_exploration_cuad.ipynb docs/PROGRESS.md docs/JOURNAL_ACTIONS.md
  git commit -m "exp(data): explorer CUAD dans un notebook et journaliser la séance"
  ```
- **Explication** : `git add` met ces 3 fichiers seulement dans l'index ; `git commit` les
  enregistre dans l'historique local de la branche (pas sur GitHub).
- **Pourquoi** : étape 5 demandée par Sara ; le notebook est vérifié sans sortie.
- **Résultat et commit** : voir A10.

### A10 — Résultat du premier commit

- **Résultat** : commit **`dcf5760`** `exp(data): explorer CUAD dans un notebook et journaliser la séance`
  sur `exp/exploration-cuad`. Il reste `docs/decisions.md` modifié (D-004), commité en A12.
- **Fichiers touchés** : `notebooks/01_exploration_cuad.ipynb`, `docs/PROGRESS.md`,
  `docs/JOURNAL_ACTIONS.md`.

### A11 — Créer la fiche encadrant

- **Action** : création de `docs/FICHE_ENCADRANT.md` (outil d'écriture de fichiers) : ce qui a été
  fait, chiffres clés, 3 découvertes, décisions à valider (D-001, D-002, D-004), 5 questions avec
  réponses.
- **Pourquoi** : étape 6 demandée par Sara, pour préparer l'entretien.
- **Fichiers touchés** : `docs/FICHE_ENCADRANT.md` (créé).

### A12 — Second commit : D-004 et fiche encadrant

- **Commandes** :
  ```bash
  git add docs/decisions.md docs/FICHE_ENCADRANT.md docs/JOURNAL_ACTIONS.md
  git commit -m "docs(decisions): proposer D-004 et préparer la fiche encadrant"
  ```
- **Explication** : un commit séparé, parce que ce sont des documents de décision et de préparation,
  pas l'exploration elle-même : l'historique reste lisible.
- **Résultat** : voir `git log` (le numéro de ce commit ne peut pas figurer dans le commit lui-même).

### A13 — Push : en attente de l'accord de Sara

- Aucun `git push` n'a été fait. Commande proposée : `git push -u origin exp/exploration-cuad`.

### A14 — 04:03 — Push de la branche (avec l'accord de Sara)

- **Accord** : Sara a répondu « oui pousse la branche ».
- **Vérification avant** : `git diff --stat main..HEAD` → uniquement de la documentation et le
  notebook ; `jq` → 0 cellule avec sortie (aucun extrait de contrat publié).
- **Commande** :
  ```bash
  git push -u origin exp/exploration-cuad
  ```
- **Explication** : envoie sur GitHub les commits de la branche absents du serveur (`26f4188`,
  `dcf5760`, `21c9c4e`) ; `-u` relie la branche locale à `origin/exp/exploration-cuad`, pour que
  les prochains `git push` / `git pull` sachent où aller.
- **Résultat** : branche créée sur GitHub et suivie. `main` n'a pas été touchée, aucune PR créée.
  Lien proposé par GitHub pour une future PR :
  https://github.com/Sara-hjd/ContractGuardian/pull/new/exp/exploration-cuad
- **Fichiers touchés** : aucun localement. Ce paragraphe est commité en local (A15), **non poussé**.
