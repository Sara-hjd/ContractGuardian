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

### A15 — Commit local du journal

- **Commande** : `git add docs/JOURNAL_ACTIONS.md` puis
  `git commit -m "docs(journal): tracer le push de exp/exploration-cuad"`.
- **Résultat** : commit local, non poussé (branche « ahead 1 »).

---

## Séance du 2026-11-22 (suite) — terminer l'étape 1 (même exception)

Sara a reconduit la même exception pour la suite de la séance, avec les mêmes conditions.

### B1 — 04:05 — Bloc 1 : passer D-004 en « Acceptée provisoirement »

- **Action** : 3 modifications de `docs/decisions.md` (outil d'édition) : statut ; option 1
  détaillée (test officiel, validation = 15 % du train officiel, graine 42 fixée avant le tirage,
  contrôle des 9 catégories, pas de changement de graine en silence) ; limite de comparabilité
  avec l'article ; raisons. L'avantage « comparable à l'article » de l'option 1 a été nuancé.
- **Pourquoi** : décision de Sara (option 1, 10–15 % de validation). On prend 15 % pour avoir
  plus d'exemples des catégories rares en validation.
- **Fichiers touchés** : `docs/decisions.md`. **Commit** : en fin de séance.

### B2 — 04:07 — Identifier `data.zip` (lecture seule)

- **Commandes** :
  ```bash
  gh api repos/TheAtticusProject/cuad/contents/data.zip --jq '{name, size, sha, download_url}'
  gh api 'repos/TheAtticusProject/cuad/commits?path=data.zip&per_page=1' --jq '.[0] | {sha, date: .commit.committer.date}'
  gh api repos/TheAtticusProject/cuad --jq '{license: .license.spdx_id, default_branch}'
  ```
- **Résultat** : 18 309 308 octets ; empreinte Git (SHA-1 de blob) `1ae94ff0a9b70b2e3b9b8d215737c8bfae460ddc` ;
  dernier commit touchant le fichier : `7aad649` du 2021-03-11 ; **aucune licence déclarée** sur le dépôt.
- **Fichiers touchés** : aucun.

### B3 — 04:08 — Télécharger `data.zip`

- **Commande** :
  ```bash
  curl -sSL --create-dirs -o data/raw/cuad_official/data.zip \
    "https://raw.githubusercontent.com/TheAtticusProject/cuad/7aad649183846688381a147eeb3601aff590fe4a/data.zip"
  ```
- **Explication** : `-s` silencieux, `-S` affiche quand même les erreurs, `-L` suit les
  redirections, `--create-dirs` crée le dossier, `-o` nomme le fichier. L'URL est **figée sur le
  commit `7aad649`** : même si le dépôt change, on retélécharge exactement le même fichier.
- **Pourquoi** : bloc 2, découpage officiel pour D-004.
- **Fichiers touchés** : `data/raw/cuad_official/data.zip` (ignoré par Git, `data/raw/*`).
- **Résultat** : voir B9 (téléchargement lent, ~5 minutes).

### B4 — Code : segmentation v1 (bloc 4, écrit pendant le téléchargement)

- **Fichiers créés** : `src/cg/__init__.py`, `src/cg/ingestion/__init__.py`,
  `src/cg/ingestion/segmentation.py`, `src/cg/ingestion/README.md`.
- **Contenu** : classe `Segment` (titre, debut, fin, texte, page) ; `segmenter()` : lignes vides,
  bords nettoyés, plafond 1 500 caractères.

### B5 — Code : jeux de données

- **Fichiers créés** : `src/cg/datasets/__init__.py`, `cuad.py` (familles, chargement avec
  vérification des positions, règle de chevauchement `min(20, longueur)`), `splits.py`,
  `creer_splits.py`, `preparer_segments.py`, `README.md`.
- **Correction pendant l'écriture** : exclure les annotations de longueur 0, qui auraient un
  seuil de 0 et étiquetteraient tous les segments.

### B6 — Code : tests (bloc 5)

- **Fichiers créés** : `tests/test_tracabilite.py` (3 tests unitaires + le test sur tous les
  segments), `pytest.ini` (`pythonpath = src`).
- **Constat** : **pytest n'est pas installé** dans le `.venv` → accord de Sara à demander.

### B7 — Lancer les tests unitaires sans pytest

- **Commande** :
  ```bash
  PYTHONPATH=src .venv/bin/python -c "import tests.test_tracabilite as t; ..."
  ```
  (appel direct des 3 fonctions de test unitaires).
- **Explication** : un test pytest est une simple fonction avec des `assert` ; on peut l'appeler
  à la main. `PYTHONPATH=src` permet `import cg`.
- **Résultat** : les 3 tests passent.

### B8 — README de `src/cg/`

- **Fichier modifié** : `src/cg/README.md` (ligne `datasets/`, état actuel, comment lancer un module).

### B9 — 04:15 — Résultat du téléchargement et vérifications

- **Commandes** (enchaînées après B3) :
  ```bash
  ls -l data/raw/cuad_official/data.zip
  git hash-object data/raw/cuad_official/data.zip
  md5 data/raw/cuad_official/data.zip
  unzip -l data/raw/cuad_official/data.zip
  git check-ignore -v data/raw/cuad_official/data.zip
  ```
- **Explication** : `git hash-object` calcule l'empreinte que Git donne au fichier ; si elle est
  égale à celle annoncée par GitHub, le fichier est intact. `unzip -l` liste sans extraire.
  `git check-ignore -v` dit quelle règle du `.gitignore` ignore le fichier.
- **Résultat** : 18 309 308 octets ; empreinte `1ae94ff0…` **identique** ; MD5 `24b7c808…` ;
  3 fichiers : `CUADv1.json`, `train_separate_questions.json`, `test.json` ; ignoré (`data/raw/*`).

### B10 — 04:15 — Comparer le `CUADv1.json` du zip avec celui de Zenodo

- **Commandes** : `md5 -q data/raw/cuad/CUAD_v1/CUAD_v1.json` et
  `unzip -p data/raw/cuad_official/data.zip CUADv1.json | md5` (`-p` envoie le contenu vers la
  commande suivante sans rien écrire sur le disque).
- **Résultat** : même MD5 `5174daa11351d36c02eee257e924db79` : fichiers identiques.

### B11 — 04:15 — Bloc 3 : créer les splits

- **Commande** : `PYTHONPATH=src .venv/bin/python -m cg.datasets.creer_splits`
- **Résultat** : train officiel 408, test officiel 102, 0 en commun, union = les 510 contrats.
  Splits : train 347, val 61, test 102 ; partition vérifiée ; 9 catégories présentes dans chaque
  jeu (min. 13). Fichier `data/splits/cuad_v1_splits.json` (40 Ko, titres + métadonnées).
- **Fichiers touchés** : `data/splits/cuad_v1_splits.json` (créé, **non commité** : D-005 en attente).

### B12 — 04:15 — Bloc 4 : segmenter et étiqueter

- **Commande** : `PYTHONPATH=src .venv/bin/python -m cg.datasets.preparer_segments`
- **Résultat** : 79 510 segments (train 58 000, val 8 253, test 13 257) ; « aucune famille » 96–97 % ;
  médiane 154 caractères ; 15 % de moins de 20 caractères ; 1 annotation sur 3 257 non projetée.
- **Fichiers touchés** : `data/processed/cuad_segments_v1.jsonl` (40 Mo, ignoré par Git).

### B13 — 04:15 — Bloc 5 : lancer les 4 tests (sans pytest)

- **Commande** : appel direct des 4 fonctions `test_*` de `tests/test_tracabilite.py` avec
  `PYTHONPATH=src .venv/bin/python -c "..."`.
- **Résultat** : 4 OK, dont **la traçabilité des 79 510 segments**.

### B14 — Documentation

- `docs/data_provenance.md` : limites 3, 8, 9 mises à jour, limite 10 ajoutée, nouvelle section
  « découpage officiel (`data.zip`) ».
- `docs/decisions.md` : résultat du tirage dans D-004 ; **D-005 proposée**.
- `docs/PROGRESS.md` : entrée « 2026-11-22 (suite) ».
- `README.md` : F1, F2, F7 passent « En cours » (modifié avec `sed -i ''`, qui remplace du texte
  directement dans le fichier ; `''` est requis par la version macOS de `sed`).
- `docs/FICHE_ENCADRANT.md` : réécrite avec les nouveaux résultats.

### B15 — Commit de fin de séance

- **Commandes** :
  ```bash
  git status --short
  git add README.md pytest.ini src/ tests/test_tracabilite.py docs/
  git commit -m "feat(datasets): splits D-004, segmentation v1 et test de traçabilité"
  ```
- **Volontairement exclu** : `data/splits/cuad_v1_splits.json` (D-005 en attente de Sara).
- **Résultat** : voir `git log`.
