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

### C1 — Point 2 : D-005 acceptée, exception de la règle 5 étendue

- **Accord de Sara** : « 2 oui : étends l'exception de la règle 5 à data/splits/ (identifiants
  seulement, jamais de texte), passe D-005 en Acceptée et commite le fichier des splits. »
- **Actions** :
  - `CLAUDE.md`, règle 5 : deux exceptions (`data/annotations/`, `data/splits/`), mêmes conditions ;
  - `docs/decisions.md` : D-005 « Acceptée » (lignes modifiées avec `sed -i ''`) ;
  - `.gitignore` : commentaire expliquant que `data/splits/` n'est pas ignoré (aucune règle changée) ;
  - `tests/test_splits.py` créé (conséquence prévue par D-005) : clés autorisées seulement,
    titres courts (≤ 300 caractères, le plus long en fait 161), pas de doublon, couverture des 510.
- **Vérification** : les 2 tests appelés à la main → OK.
- **Commit** :
  ```bash
  git add CLAUDE.md .gitignore docs/decisions.md docs/JOURNAL_ACTIONS.md data/splits/cuad_v1_splits.json tests/test_splits.py
  git commit -m "chore(data): versionner les splits CUAD (D-005) et étendre la règle 5"
  ```

### C2 — Point 3 : installer pytest et lancer les tests

- **Accord de Sara** : « 3 oui : installe pytest, ajoute-le dans requirements.txt, puis lance les
  tests avec pytest et montre-moi le résultat. »
- **Commandes** :
  ```bash
  .venv/bin/python -m pip install "pytest>=8"
  .venv/bin/python -m pytest --version
  .venv/bin/python -m pytest -v
  ```
- **Explication** : `python -m pip install` installe dans le Python du `.venv` ; `python -m pytest`
  cherche les fichiers `tests/test_*.py` (réglage `testpaths` de `pytest.ini`), lance chaque
  fonction `test_*` et affiche PASSED ou FAILED ; `-v` (verbose) affiche une ligne par test.
- **Résultat** : pytest 9.2.0 ; **6 passed in 0.27s** (2 tests de splits, 4 de traçabilité).
- **Fichiers touchés** : `requirements.txt` (ligne `pytest>=8`), `.venv/` (non versionné),
  `docs/PROGRESS.md` (pytest installé, D-005 acceptée).
- **Commit** :
  ```bash
  git add requirements.txt docs/PROGRESS.md docs/JOURNAL_ACTIONS.md
  git commit -m "chore(deps): ajouter pytest et lancer la suite de tests"
  ```

### C3 — Point 1 : push de tous les commits

- **Accord de Sara** : « 1 oui, mais en dernier : une fois 2 et 3 commités, pousse tout en une
  seule fois. »
- **Commande** : `git push` (la branche suit déjà `origin/exp/exploration-cuad` depuis A14).
- **Résultat** : voir la sortie de la commande dans la conversation ; ce paragraphe est commité
  avant le push, donc il est inclus dans ce qui est poussé.

---

## Séance du 2026-11-22 (suite 2) — baselines d'extraction (même exception)

Sara a décidé : baseline d'abord, puis étape 2 (changement d'ordre du planning, noté dans
PROGRESS.md). Même exception ; installation de scikit-learn et MLflow **autorisée d'avance**.

### D1 — 04:25 — Créer la branche et installer scikit-learn et MLflow

- **Commandes** :
  ```bash
  git switch -c exp/baseline-extraction          # depuis exp/exploration-cuad, à jour avec GitHub
  .venv/bin/python -m pip install "scikit-learn>=1.5" "mlflow>=2.17"
  ```
- **Explication** : `git switch -c` crée une branche à partir de la branche courante et s'y
  place. `pip install` télécharge et installe les deux bibliothèques et leurs dépendances.
- **Pourquoi** : une branche par tâche (CLAUDE.md) ; scikit-learn pour la baseline 2, MLflow
  pour le suivi des expériences (F7).
- **Résultat** : branche créée ; installation longue (réseau lent), lancée en arrière-plan,
  voir D6.

### D2 — Lire les définitions officielles des catégories (lecture seule)

- **Commandes** : `grep` et `sed -n` sur `data/raw/cuad/CUAD_v1/CUAD_v1_README.txt`.
- **Pourquoi** : justifier les mots-clés de la baseline 1 par les définitions de CUAD, **sans
  regarder les segments de validation ni de test**.

### D3 — Code de l'extraction

- **Fichiers créés** : `src/cg/extraction/__init__.py`, `mots_cles.py` (baseline 1, liste figée
  avant évaluation), `metriques.py`, `tfidf.py`, `README.md` ; `src/cg/datasets/segments.py`
  (`charger_segments` refuse le test sans `ouvrir_test=True`) ;
  `training/baselines_extraction.py` (grille n-grammes {1, 2} × C {0,1 ; 1 ; 10}, seuil par
  famille, MLflow, erreurs de validation).
- **Tests** : `tests/test_extraction.py` (7 tests).

### D4 — Configuration

- `requirements.txt` : `scikit-learn>=1.5`, `mlflow>=2.17`.
- `.gitignore` : `mlflow.db` (base locale des runs) et `mlartifacts/` ajoutés à côté de `mlruns/`.
- `src/cg/README.md`, `src/cg/datasets/README.md` : nouveaux fichiers mentionnés (via `sed -i ''`).

### D5 — Échec de la première installation (réseau)

- **Résultat de D1** : `error: incomplete-download` : un téléchargement coupé par le réseau ;
  rien n'a été installé.

### D6 — Deuxième tentative (≈ 04:40 → 06:43)

- **Commandes** :
  ```bash
  .venv/bin/python -m pip install --retries 10 --timeout 120 --progress-bar off "scikit-learn>=1.5"
  .venv/bin/python -m pip install --retries 10 --timeout 120 --progress-bar off "mlflow>=2.17"
  ```
- **Explication** : `--retries 10` réessaie jusqu'à 10 fois une connexion qui échoue ;
  `--timeout 120` attend jusqu'à 120 s une réponse ; installer en deux fois permet de garder
  scikit-learn même si MLflow échoue.
- **Résultat** : **scikit-learn 1.9.1 installé** (avec scipy 1.17.1, joblib 1.6.0,
  threadpoolctl 3.8.0, narwhals, cloudpickle). **MLflow : échec** sur le téléchargement de
  `pyarrow` (dépendance d'environ 40 Mo), « issue with network connectivity, not pip ».

### D7 — 09:46 — Troisième tentative pour MLflow, tests

- **Commande** : la même avec `--resume-retries 50` (reprendre un téléchargement interrompu
  au lieu de le recommencer).
- **En parallèle** : `.venv/bin/python -m pytest -q` → **13 passed** (6 anciens + 7 d'extraction).

### D8 — 12:18 — Résultat de la troisième tentative

- **Résultat** : **MLflow 3.18.0 installé** (avec pyarrow 26.0.1, sqlalchemy, flask…).
  L'installation affiche une « astuce » qui propose de charger une documentation de traçage :
  message du paquet, sans rapport avec notre usage, ignoré.

### D9 — 12:37 — Entraîner et évaluer les baselines

- **Commande** :
  ```bash
  MLFLOW_DISABLE_AGENT_HINT=1 PYTHONPATH=src .venv/bin/python training/baselines_extraction.py
  ```
- **Explication** : `MLFLOW_DISABLE_AGENT_HINT=1` coupe le message d'astuce de MLflow ;
  `PYTHONPATH=src` permet `import cg`.
- **Résultat** (validation) : macro-F1 mots-clés **0,247**, TF-IDF **0,669** (0,635 au seuil 0,5).
  Réglages retenus : bigrammes, C = 10, seuils 0,80 / 0,55 / 0,80. 201 erreurs écrites dans
  `data/processed/erreurs_val_tfidf.jsonl` (ignoré). Fichiers MLflow : `mlflow.db`, `mlruns/` (ignorés).

### D10 — Vérifier MLflow (lecture)

- **Commande** : `mlflow.search_runs(experiment_names=['F2-extraction-baselines'])` en Python.
- **Résultat** : 2 runs FINISHED, `baseline-1-mots-cles` et `baseline-2-tfidf-logreg`.

### D11 — Analyse d'erreurs

- **Commande** : script Python court qui lit `data/processed/erreurs_val_tfidf.jsonl` et tire
  4 FP + 4 FN par famille (`sample(random_state=0)`), puis affiche les textes **dans le terminal
  seulement**. Premier essai en erreur (pandas 3 et `groupby().apply()`), refait avec une boucle.
- **Résultat** : 24 erreurs classées. Fichier créé : `docs/analyses/erreurs_baseline_tfidf_val.md`
  (provenance + descriptions en français, **aucun extrait**).

### D12 — Documentation

- `docs/decisions.md` : **D-006** (protocole des baselines, ordre du planning).
- `README.md` : tableau des résultats (validation).
- `docs/PROGRESS.md` : entrée « suite 2 » avec le changement d'ordre du planning.
- `docs/FICHE_ENCADRANT.md` : section baselines, D-005/D-006, question 6.

### D13 — Commit

- **Commandes** :
  ```bash
  .venv/bin/python -m pytest -q
  git status --short
  git add .gitignore requirements.txt README.md docs/ src/ tests/test_extraction.py training/baselines_extraction.py
  git commit -m "exp(extraction): baselines mots-clés et TF-IDF évaluées sur la validation"
  ```
- **Résultat** : voir `git log` ; push en attente de l'accord de Sara.

### D14 — 23:11 — Push de `exp/baseline-extraction` (accord de Sara) — fin de l'exception

- **Accord** : « Oui, pousse exp/baseline-extraction. »
- **Commande** : `git push -u origin exp/baseline-extraction`
- **Résultat** : branche créée sur GitHub (commit `0de4008`), suivie localement. `main` non touchée,
  aucune PR créée.
- **Fin de l'exception** : à partir d'ici, Sara exécute de nouveau toutes les commandes
  (CLAUDE.md). Ce paragraphe n'est **pas commité** par Claude : Sara le commitera.

---

## Séance du 2026-11-22 (suite 3) — exception limitée : décisions, commit, push, PR

**Périmètre accordé par Sara, et seulement celui-ci** : mettre à jour les décisions, PROGRESS et la
fiche ; commiter sur `exp/baseline-extraction` (journal D14 + ces mises à jour) et pousser ; créer
la PR A et la PR B avec ILyas394 comme relecteur ; ajouter ILyas394 comme relecteur de la PR #1.
**Aucune fusion.** Ensuite, la règle habituelle reprend.

Note : un premier message de Sara demandait seulement de modifier les fichiers et de lui donner
les commandes Git ; le second, plus récent, autorise explicitement ces actions : c'est lui qui
est appliqué.

### E1 — Mettre à jour les décisions, PROGRESS et la fiche

- **Action** : modifications avec l'outil d'édition (pas de commande shell).
  - `docs/decisions.md` : D-001 et D-002 « Acceptée (Sara, 2026-11-22), à présenter à
    l'encadrant » ; D-002 : décision (ContractNLI + baseline par mots-clés), raisons, 5 conséquences ;
    D-004 « Acceptée » ; D-006 « confirmée par Sara le 2026-11-22 ».
  - `docs/FICHE_ENCADRANT.md` : tableau « Décisions prises par Sara, à présenter pour validation ».
  - `docs/PROGRESS.md` : entrée « suite 3 ».

### E2 — Commit et push de `exp/baseline-extraction`

- **Commandes** :
  ```bash
  git status --short
  git add docs/decisions.md docs/PROGRESS.md docs/FICHE_ENCADRANT.md docs/JOURNAL_ACTIONS.md
  git commit -m "docs(decisions): accepter D-001, D-002, D-004 et confirmer D-006"
  git push
  ```
- **Explication** : `git push` sans argument envoie la branche courante vers la branche suivie
  (`origin/exp/baseline-extraction`, reliée en D14 avec `-u`).
- **Résultat** : commit **`daf93eb`**, poussé (`0de4008..daf93eb`).

### E3 — Créer la PR A (#2)

- **Commande** :
  ```bash
  gh pr create --base main --head exp/exploration-cuad \
    --title "exp(data): étape 1 — exploration de CUAD, splits D-004/D-005, segmentation v1 et traçabilité" \
    --body-file <description rédigée dans un fichier temporaire> --reviewer ILyas394
  ```
- **Explication** : `--base` = branche qui reçoit, `--head` = branche proposée ; `--body-file`
  lit la description dans un fichier ; `--reviewer` demande la relecture d'Ilyas.
- **Résultat** : https://github.com/Sara-hjd/ContractGuardian/pull/2 (7 commits, relecteur ILyas394).

### E4 — Créer la PR B (#3), empilée sur la PR A

- **Commande** : même forme, avec `--base exp/exploration-cuad --head exp/baseline-extraction`.
- **Pourquoi cette base** : la PR ne montre que les 2 commits nouveaux ; elle basculera vers `main`
  quand la PR #2 sera fusionnée et sa branche supprimée.
- **Résultat** : https://github.com/Sara-hjd/ContractGuardian/pull/3 (2 commits, relecteur ILyas394).

### E5 — Relecteur de la PR #1 (relecture a posteriori)

- **Commande** : `gh pr edit 1 --add-reviewer ILyas394`
- **Vérification** : `gh pr view <n> --json …` pour #1, #2, #3 → relecteur ILyas394 sur les trois ;
  #1 MERGED, #2 et #3 OPEN. **Rien n'a été fusionné.**

### Fin de l'exception

Ces paragraphes E2 (résultat) à E5 ne sont **pas commités** par Claude (l'autorisation couvrait un
seul commit et un seul push). Sara les commitera elle-même. La règle habituelle reprend.

---

## Séance du 2026-11-22 (suite 4) — fusions directes, puis mode « Claude exécute tout » (séance 1/3)

**Consignes de Sara** : (1) fusionner directement les PR #2 et #3 sans attendre l'approbation
d'Ilyas (relecture a posteriori), avec un commentaire pour lui ; (2) inscrire dans `CLAUDE.md` un
mode temporaire de 3 séances où Claude exécute toutes les commandes (interdits listés dans
`CLAUDE.md`) ; cette suite de séance compte comme séance 1/3 ; (3) après la séance 3/3, rédiger un
diagnostic total depuis le 16/11.

### F1 — 23:32 — Commit et push du journal (E2 à E5)

- **Commandes** : `git add docs/JOURNAL_ACTIONS.md` ;
  `git commit -m "docs(journal): tracer la création des PR #2 et #3"` ; `git push`.
- **Résultat** : commit `6ce6d6f`, poussé sur `exp/baseline-extraction` ; la PR #3 compte 3 commits.

### F2 — 23:32 — Commentaire pour Ilyas et fusion de la PR #2

- **Commandes** :
  ```bash
  gh pr comment 2 --body "Fusionnée par Sara… sans attendre ta relecture… règle 5 / D-005…"
  gh pr merge 2 --merge --delete-branch
  ```
- **Explication** : `gh pr comment` ajoute un commentaire sur la PR ; `gh pr merge --merge` crée
  un commit de fusion (on garde les commits d'origine) ; `--delete-branch` supprime la branche
  `exp/exploration-cuad` sur GitHub et en local.
- **Résultat** : PR #2 **fusionnée**, commit de fusion `060de9d`.

### F3 — 23:32 — Incident : la PR #3 a été fermée au lieu de basculer vers `main`

- **Constat** : `gh pr view 3` → `base=exp/exploration-cuad état=CLOSED`. Quand la branche de base
  d'une PR est supprimée **par `gh pr merge --delete-branch`**, GitHub a **fermé** la PR empilée
  au lieu de la rebasculer vers `main`, contrairement à ce que Claude avait annoncé à Sara.
- **Leçon** : pour des PR empilées, fusionner la première **sans** `--delete-branch`, changer la
  base de la seconde vers `main` (`gh pr edit <n> --base main`), puis seulement supprimer la branche.

### F4 — 23:33 — Réparation (réversible)

- **Commandes** :
  ```bash
  git push origin 18e219e:refs/heads/exp/exploration-cuad   # recréer la branche sur GitHub
  gh pr reopen 3
  gh pr edit 3 --base main
  ```
- **Explication** : `git push origin <commit>:refs/heads/<nom>` crée sur GitHub une branche qui
  pointe sur ce commit (le dernier de `exp/exploration-cuad`), sans rien réécrire ; une PR fermée
  ne peut être rouverte que si sa branche de base existe ; `gh pr edit --base` change la base.
- **Résultat** : PR #3 `OPEN`, `base=main`, `MERGEABLE`, 3 commits.

### F5 — 23:33 — Commentaire pour Ilyas et fusion de la PR #3, nettoyage

- **Commandes** :
  ```bash
  gh pr comment 3 --body "Fusionnée par Sara… D-006, D-002… note technique…"
  gh pr merge 3 --merge --delete-branch
  git push origin --delete exp/exploration-cuad     # supprimer la branche recréée en F4
  git fetch --prune
  git pull
  ```
- **Explication** : `gh pr merge` a aussi basculé le dépôt local sur `main` et l'a mis à jour ;
  `git push origin --delete` supprime une branche sur GitHub ; `git fetch --prune` efface les
  images locales de branches qui n'existent plus sur GitHub.
- **Résultat** : PR #3 **fusionnée**, commit de fusion `0f9b683`. Plus aucune branche que `main`,
  en local comme sur GitHub. `main` à jour.

### F6 — 23:34 — Tests et graphe sur `main`

- **Commandes** : `.venv/bin/python -m pytest -q` ; `git log --oneline --graph -16`.
- **Résultat** : **13 passed** ; graphe : `5cf0cb5` → PR #1 (`2a558c8`) → PR #2 (`060de9d`,
  7 commits) → PR #3 (`0f9b683`, 3 commits).

### F7 — 23:35 — Mode temporaire dans `CLAUDE.md`

- **Commande** : `git switch -c docs/mode-temporaire` (une branche par tâche).
- **Action** : section « ⚠️ Mode temporaire : « Claude exécute tout » (3 séances) » ajoutée en tête
  de « Qui exécute les commandes » : date, compteur 1/3 à 3/3, fin automatique, interdits,
  obligations (plan, journal, fin de séance, diagnostic total).
- **Fichiers touchés** : `CLAUDE.md`, ce journal, `docs/PROGRESS.md`.
- **Commit, push, PR, fusion** : F8.

### F8 — Commit, PR et fusion de `docs/mode-temporaire` (mode actif, séance 1/3)

- **Commandes** :
  ```bash
  git add CLAUDE.md docs/JOURNAL_ACTIONS.md docs/PROGRESS.md
  git commit -m "docs(claude): mode temporaire « Claude exécute tout » pendant 3 séances"
  git push -u origin docs/mode-temporaire
  gh pr create --base main --head docs/mode-temporaire --title … --body …
  gh pr merge <n> --merge --delete-branch
  git pull
  ```
- **Résultat** : voir la PR et `git log` (ce paragraphe est écrit avant le commit).

---

## Séance 1/3 du mode temporaire — 2026-11-22 (suite 5) — vérification PDF avec PyMuPDF

**Plan annoncé** : installer PyMuPDF ; `src/cg/ingestion/pdf.py` (texte par page + positions) ;
`src/cg/ingestion/alignement.py` ; vérifier sur 10 PDF du **train** ; tests ; proposer D-007
(Sara décide).

### G1 — 23:37 — Branche et installation de PyMuPDF

- **Commandes** :
  ```bash
  git switch -c feat/ingestion-pdf
  .venv/bin/python -m pip install --retries 10 --timeout 120 --resume-retries 50 --progress-bar off "pymupdf>=1.24"
  ```
- **Pourquoi** : une branche par tâche ; PyMuPDF est l'outil prévu pour lire les PDF (stack).
  Options de pip reprises de D7 à cause du réseau lent. Lancé en arrière-plan.

### G2 — 23:37 — Correspondance titres CUAD ↔ fichiers PDF (lecture)

- **Commande** : petit script Python qui compare les noms des 510 PDF (sans extension) aux 510
  titres de `CUAD_v1.json`.
- **Résultat** : 505 correspondances exactes ; 5 différences (espace final, tiret final, « É »
  encodé autrement en Unicode, suffixe ajouté). D'où `trouver_pdf` (comparaison normalisée,
  puis par début de nom). Extensions `.pdf` et `.PDF` mélangées.

### G3 — Code et tests

- **Fichiers créés** : `src/cg/ingestion/pdf.py`, `src/cg/ingestion/alignement.py`,
  `evaluation/verifier_extraction_pdf.py`, `tests/test_ingestion_pdf.py` (7 tests).
- **Fichier modifié** : `src/cg/ingestion/README.md` (nouveaux fichiers, via `sed -i ''`).
- **Choix v1** : pages séparées par une ligne vide → aucun segment PDF sur deux pages.
- **Vérification** : `pytest tests/test_ingestion_pdf.py` → 5 passed, 2 skipped (PyMuPDF pas
  encore installé).

### G4 — 2026-11-23 00:28 — Arrêter l'installation de PyMuPDF 2.1 et relancer en 1.x

- **Constat (23:55)** : pip téléchargeait `pymupdf-2.1` à ~8 Ko/s (8,1 Mo en 17 min). La
  version 2.1 ajoute des dépendances lourdes inutiles pour nous (`onnxruntime`,
  `pymupdf_layout`, `pymupdf4llm`) : installation estimée à plus d'une heure.
- **Décision de Sara** : « arrête et relance ».
- **Commandes** :
  ```bash
  kill 58296                                   # arrêter le processus pip (numéro trouvé avec ps)
  .venv/bin/python -m pip list | grep -i -E "mupdf|onnx|flatbuffers"   # rien d'installé à moitié
  .venv/bin/python -m pip install --retries 10 --timeout 120 --resume-retries 50 --progress-bar off "pymupdf>=1.24,<2"
  ```
- **Explication** : `kill` envoie un signal d'arrêt au processus ; `<2` limite la version à la
  série 1.x, qui lit le texte page par page sans ces dépendances.
- **Résultat** : arrêt propre, aucun paquet partiel ; nouvelle installation lancée en arrière-plan.

### G5 — 00:31 — PyMuPDF installé ; tests ; vérification sur 10 PDF

- **Résultat de G4** : `pymupdf 1.28.2` installé (≈ 3 minutes).
- **Commandes** :
  ```bash
  .venv/bin/python -m pytest -q
  PYTHONPATH=src .venv/bin/python evaluation/verifier_extraction_pdf.py
  ```
- **Résultat** : **20 passed**. 10 contrats du train : 0 page vide, traçabilité « oui » partout ;
  alignement 79,5 % (espaces) et **98,6 %** (étendu) sur nos 9 catégories ; 1 échec
  (`data/processed/alignement_echecs.jsonl`, non commité).

### G6 — 00:32 — Diagnostic des échecs et des segments (lecture, terminal seulement)

- **Commandes** : deux scripts Python courts (lecture seule des données, rien d'écrit).
- **Résultats** : les échecs au niveau « espaces » viennent des **guillemets typographiques** du
  PDF (207 dans un contrat) ; le seul échec étendu est un défaut du texte CUAD (mot coupé dans une
  date). Segments PDF : médiane 1 422 caractères contre 136 pour CUAD, 54 % au plafond ; un
  contrat n'a que 22 lignes vides pour 199 blocs PyMuPDF.

### G7 — 00:32 — Mesure sur les 347 contrats du train (lecture)

- **Commande** : script Python court qui extrait les 347 PDF du train et aligne toutes les
  annotations aux deux niveaux ; puis un second script qui classe les pages vides (avec ou sans
  image). Le test n'est pas touché.
- **Résultats** : nos 9 catégories : espaces 70,65 % (1 603 / 2 269), **étendu 98,28 %**
  (2 230 / 2 269) ; 41 catégories : étendu 99,31 %. 46 pages vides dans 21 contrats : 39 blanches,
  7 avec une image ; aucun contrat entièrement scanné.

### G8 — Documentation, D-007 proposée

- `docs/analyses/verification_pdf_pymupdf.md` créé (chiffres, aucun extrait).
- `docs/decisions.md` : **D-007 « Proposée »** (4 options, proposition : option 2). Sara décide.
- `docs/data_provenance.md` : limite 3 complétée (script Python qui insère une ligne après un
  repère précis, avec vérification que le repère existe).
- `requirements.txt` : `pymupdf>=1.24,<2`.

### G9 — Commit, push, PR (sans fusion : D-007 attend Sara)

- **Commandes** :
  ```bash
  git add requirements.txt src/cg/ingestion/ evaluation/verifier_extraction_pdf.py tests/test_ingestion_pdf.py docs/
  git commit -m "feat(ingestion): extraction PDF PyMuPDF, alignement des annotations, D-007 proposée"
  git push -u origin feat/ingestion-pdf
  gh pr create --base main --head feat/ingestion-pdf …
  ```
- **Pas de fusion** : la PR intégrera la décision de Sara sur D-007 avant d'être fusionnée.

### G10 — 00:36 — D-007 acceptée par Sara ; numérotation

- **Décision de Sara** : D-007 option 2 (exact + normalisation étendue ; annotations non
  retrouvées comptées, listées par référence, exclues). Statut « Acceptée (Sara, 2026-11-23) ».
- **Numérotation** : la segmentation des PDF devient **D-008** ; les exemples négatifs de
  ContractNLI deviennent **D-009** (renvoi ajouté dans D-002). « D-008 » n'était écrit dans aucun
  fichier (vérifié avec `grep -rn -E "D-00[89]" docs CLAUDE.md README.md src`).
- **Fichiers** : `docs/decisions.md` (édition + `sed -i ''` pour le renvoi D-009).

### G11 — Mode « blocs » de l'extraction PDF

- **Fichier modifié** : `src/cg/ingestion/pdf.py` : paramètre `mode` de `extraire_pdf`
  (`"texte"` ou `"blocs"`) ; en mode « blocs », le texte d'une page est la suite des blocs de texte
  PyMuPDF (`page.get_text("blocks")`, blocs d'image ignorés), séparés par une ligne vide : la
  segmentation v1 coupe donc à chaque bloc, sans nouveau code de segmentation.
- **Test ajouté** : `test_mode_blocs_coupe_a_chaque_paragraphe` ; suite : **21 passed**.

### G12 — 00:42 — Comparer les segmentations sur train + validation

- **Commande** : `PYTHONPATH=src .venv/bin/python evaluation/comparer_segmentation_pdf.py`
  (script créé ; 408 contrats de train + validation, test fermé ; 71 s).
- **Résultats** : CUAD médiane 153, ≥ 1 400 : 6,6 % ; PDF « texte » médiane 148, ≥ 1 400 : 18,8 %,
  annotations entières dans un segment 89,1 % ; PDF « blocs » médiane 83, ≥ 1 400 : 2,0 %, entières
  92,0 % ; traçabilité 100 % dans les deux modes ; alignement 98,2 % dans les deux modes.
- **Correction** : l'échantillon de 10 contrats (G6) avait exagéré l'écart de longueur (médiane
  1 422) ; corrigé dans `docs/analyses/verification_pdf_pymupdf.md` et dans D-007.

### G13 — D-008 proposée

- `docs/decisions.md` : **D-008 « Proposée »** (tableau des mesures, 3 options, proposition :
  blocs ; conséquence : préparer les données d'entraînement à partir des PDF et réentraîner la
  baseline). Sara décidera.

### G14 — Clôture de la séance 1/3

- `src/cg/ingestion/README.md`, `docs/PROGRESS.md`, `README.md`, `docs/FICHE_ENCADRANT.md`,
  `CLAUDE.md` (compteur : séance 1/3 terminée).
- **Commandes** :
  ```bash
  .venv/bin/python -m pytest -q
  git add -A src/cg/ingestion evaluation tests docs README.md CLAUDE.md
  git commit -m "feat(ingestion): mode blocs, comparaison des segmentations PDF, D-007 acceptée, D-008 proposée"
  git push
  gh pr comment 5 --body "…correction de la médiane…"
  gh pr merge 5 --merge --delete-branch
  git pull
  ```
- **Résultat de G14** : commit `8708b02` poussé ; commentaire sur la PR #5 (correction de la
  médiane) ; PR #5 **fusionnée** (commit de fusion `2b7340f`) ; branche supprimée ; `main` à jour ;
  **21 passed** sur `main`. **Fin de la séance 1/3.** Ce paragraphe sera commité au début de la
  séance 2/3 (sur la première branche de la séance), pour ne pas commiter directement sur `main`.

---

## Séance 2/3 du mode temporaire — 2026-11-23 — Docker, PostgreSQL, pgvector ; segments PDF ; réentraînement

**Plan annoncé** : (1) D-008 acceptée + commit du journal en attente ; (2) Docker, PostgreSQL,
pgvector (priorité) — décisions de fond **proposées** (D-010) ; (3) segments PDF étiquetés
(blocs) ; (4) réentraînement de la baseline sur ces segments, comparaison sur la validation, avec
l'expérience « fusion des fragments » ; (5) clôture.

### H1 — 00:52 — État de Docker et branche

- **Commandes** : `docker --version` ; `docker compose version` ; `docker info --format …` ;
  `git switch -c infra/postgres-pgvector`.
- **Résultat** : Docker Desktop 29.8.2 installé **et lancé** ; Compose v5.6.0.

### H2 — 00:52 — Choisir et télécharger l'image

- **Commandes** :
  ```bash
  curl -s "https://hub.docker.com/v2/repositories/pgvector/pgvector/tags?page_size=40&ordering=last_updated" | jq …
  docker pull pgvector/pgvector:0.8.7-pg17
  ```
- **Explication** : la première commande lit (GET) la liste des versions de l'image officielle ;
  `docker pull` télécharge l'image choisie. Version figée pour la reproductibilité (D-010).
- **Résultat** : `0.8.7-pg17` (164 Mo compressés) ; téléchargement lancé en arrière-plan (réseau lent).

### H3 — 00:52 — Installer psycopg 3

- **Commande** : `.venv/bin/python -m pip install --retries 10 --timeout 120 --resume-retries 50 --progress-bar off "psycopg[binary]>=3.2"`
- **Explication** : psycopg est le pilote qui permet à Python de parler à PostgreSQL ; « binary »
  = version précompilée, sans compilation sur la machine.
- **Résultat** : `psycopg 3.3.9`.

### H4 — D-008 acceptée

- **Action** : `docs/decisions.md`, D-008 « Acceptée (Sara, 2026-11-23) » : option 2 (blocs) ;
  option 3 testée comme expérience lors du réentraînement, réglée et comparée sur la validation.

### H5 — Fichiers de la base

- **Créés** : `docker-compose.yml`, `.env.example`, `db/init/001_schema.sql`,
  `src/cg/stockage/` (`__init__.py`, `connexion.py`, `depot.py`, `ingerer_pdf.py`, `README.md`),
  `tests/test_stockage.py`.
- **`.env` local** (jamais commité) :
  ```bash
  if [ -e .env ]; then echo "existe déjà"; else sed "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -hex 16)/" .env.example > .env && chmod 600 .env; fi
  git check-ignore -v .env .env.example
  ```
  **Explication** : on ne crée `.env` que s'il n'existe pas (pas d'écrasement) ; `openssl rand -hex 16`
  tire un mot de passe aléatoire (32 caractères hexadécimaux) ; `chmod 600` = lisible par ton seul
  compte. Le mot de passe n'a été affiché nulle part. **Résultat** : `.env` ignoré, `.env.example` suivi.

### H6 — Fusion des fragments (option 3 de D-008)

- **Fichier modifié** : `src/cg/ingestion/segmentation.py`, fonction `fusionner_fragments`
  (fragment < seuil rattaché au suivant de la même page, sans dépasser le plafond).
- **Test ajouté** : `test_fusionner_fragments` ; suite : 23 passed, 2 skipped (base pas encore lancée).

### H7 — 00:57 — Segments PDF étiquetés (train + val)

- **Fichier créé** : `src/cg/datasets/preparer_segments_pdf.py`.
- **Commande** : `for s in 0 20 40 80; do PYTHONPATH=src .venv/bin/python -m cg.datasets.preparer_segments_pdf --seuil-fusion $s; done`
- **Grille des seuils fixée avant tout entraînement** : {0, 20, 40, 80}.
- **Résultats** : seuil 0 : 96 244 segments, médiane 83, < 20 car. 24,6 % ; seuil 20 : 79 733, médiane 133,
  3,4 % ; seuil 40 : 70 719, médiane 169 ; seuil 80 : 61 819, médiane 216. Annotations (nos 9) :
  2 691, alignées 2 643, **exclues 48 (1,8 %)**, références dans
  `data/processed/cuad_pdf_annotations_exclues.jsonl`. Tous les fichiers dans `data/processed/` (ignoré).

### H8 — Réentraînement sur segments PDF (lancé)

- **Fichier créé** : `training/baselines_extraction_pdf.py` (configurations `cuad->pdf` et
  `pdf-fusion{0,20,40,80}` ; même grille que D-006 ; F1 par segment + **rappel par annotation**).
- **Commande** : `MLFLOW_DISABLE_AGENT_HINT=1 PYTHONPATH=src .venv/bin/python training/baselines_extraction_pdf.py`
  (en arrière-plan). Résultat : H9.

### H8 bis — D-010 proposée

- `docs/decisions.md` : **D-010 « Proposée »** (image figée, accès local, `.env`, volume, schéma,
  pgvector sans colonne pour l'instant, SQL numérotés sans Alembic, psycopg sans ORM). Sara décidera.

### H9 — 01:04 — Démarrer la base

- **Résultat de H2** : image `pgvector/pgvector:0.8.7-pg17` téléchargée (≈ 12 minutes ; 485 Mo une fois décompressée).
- **Commandes** :
  ```bash
  docker compose config --quiet          # vérifie que docker-compose.yml est valide
  docker compose up -d                   # crée et démarre le conteneur en arrière-plan (-d)
  docker inspect -f '{{.State.Health.Status}}' cg-postgres    # répété jusqu'à « healthy »
  docker compose ps
  ```
- **Résultat** : `cg-postgres Up (healthy) 127.0.0.1:5432->5432/tcp`.

### H10 — 01:04 — Vérifier le schéma et lancer les tests

- **Commandes** :
  ```bash
  docker exec cg-postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt" -c "SELECT extname, extversion FROM pg_extension WHERE extname = '\''vector'\'';" -c "SELECT version();"'
  .venv/bin/python -m pytest -q -rs
  ```
- **Explication** : `docker exec` lance une commande **dans** le conteneur ; `psql` est le client
  en ligne de commande de PostgreSQL ; `\dt` liste les tables. Les identifiants sont lus dans les
  variables du conteneur, jamais écrits dans la commande.
- **Résultat** : 4 tables (`contrats`, `pages`, `segments`, `resultats`) ; `vector 0.8.7` ;
  PostgreSQL 17.12 ; **25 passed** (dont les 3 tests de la base).

### H11 — 01:05 — Importer les 408 PDF de train + validation dans la base

- **Commande** : script Python court (boucle sur les titres train + val : `extraire_pdf(mode="blocs")`,
  `segmenter_pdf`, `enregistrer_document(source="cuad")`, `compter_segments_non_tracables`), puis
  `SELECT pg_size_pretty(pg_database_size(current_database()))`.
- **Pourquoi** : test de robustesse réel (caractères refusés par PostgreSQL, gros contrats) ; le test
  n'est pas importé.
- **Résultat** : **408/408 contrats**, 7 625 pages, **96 244 segments** (identique au fichier
  préparé en H7), **0 non traçable (vérifié en SQL)**, 0 erreur, 211 s ; base : 51 Mo.

### H12 — 01:09 — Résultats du réentraînement (H8)

- **Commande de lecture** : `mlflow.search_runs(experiment_names=['F2-extraction-segments-pdf'])`
  (l'affichage du script était tronqué par pandas).
- **Résultats (validation)** : `cuad->pdf` macro-F1 0,643, macro rappel par annotation 0,719 ;
  `pdf-fusion0` 0,656 / 0,724 ; fusion 20 / 40 / 80 : 0,657 / 0,665 / 0,669 (segments différents) et
  0,720 / 0,720 / 0,723. Annotations de validation alignées : durée 208, résiliation 89,
  responsabilité 116 → 1 annotation = 0,5 / 1,1 / 0,9 point : écarts non significatifs.

### H13 — Analyse, D-011 proposée, clôture

- `docs/analyses/baseline_segments_pdf_val.md` créé ; **D-011 « Proposée »** (segments PDF blocs,
  sans fusion) ; `requirements.txt` : `psycopg[binary]>=3.2`.
- `README.md` (F1, tableau des résultats), `docs/FICHE_ENCADRANT.md`, `docs/PROGRESS.md` (séance 2/3),
  `CLAUDE.md` (compteur : **2/3 terminée**) — modifiés par un script Python de remplacement
  vérifiant chaque repère.

### H14 — Commit, push, PR (fusion après les décisions de Sara sur D-010 et D-011)

- **Commandes** : `.venv/bin/python -m pytest -q` ; `git add …` ;
  `git commit -m "feat(stockage): PostgreSQL + pgvector, segments PDF et réentraînement (D-008 ; D-010, D-011 proposées)"` ;
  `git push -u origin infra/postgres-pgvector` ; `gh pr create …`.
- La base reste démarrée (`docker compose ps`) ; pour l'arrêter : `docker compose down`.
