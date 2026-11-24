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

### H15 — Décisions de Sara : D-010 et D-011 acceptées ; fusion de la PR #6

- **Décisions** : D-010 acceptée telle quelle ; D-011 option 2 (segments PDF blocs, sans fusion).
- **Fichiers** : `docs/decisions.md`, `docs/FICHE_ENCADRANT.md`, `docs/PROGRESS.md` (script Python
  de remplacement vérifiant chaque repère).
- **Commandes** : `git commit` ; `git push` ; `gh pr merge 6 --merge --delete-branch` ; `git pull`.

---

## Séance 3/3 du mode temporaire — 2026-11-23 — ContractNLI, D-009, baseline confidentialité

**Plan annoncé** : télécharger et documenter ContractNLI ; explorer train + dev (test fermé) ;
adapter les évidences en segments étiquetés + test de traçabilité ; figer la liste de mots-clés
**avant** toute évaluation ; proposer D-009 ; clôture, fin du mode, diagnostic total.

### I1 — 01:16 — PR #6 fusionnée, branche de la séance

- Voir H15 : commit `6353622`, PR #6 fusionnée (`a92d7d6`), 25 tests passent sur `main`.
- `git switch -c exp/contractnli`.

### I2 — Source officielle (lecture)

- **Consultation** : https://stanfordnlp.github.io/contract-nli/ ; `curl -sI -L <zip>` (en-têtes seulement).
- **Résultat** : 607 NDA, 17 hypothèses, CC BY 4.0, Koreeda & Manning, Findings of EMNLP 2021 ;
  zip 65 362 913 octets, modifié le 2022-02-11. **Conditions d'utilisation** (Hitachi America) :
  y accéder vaut acceptation ; usage régi par CC BY 4.0. À lire par Sara.

### I3 — 01:18 — Téléchargement

- **Commande** :
  ```bash
  curl -sSL --retry 10 --retry-delay 5 -C - --create-dirs -o data/raw/contractnli/contract-nli.zip "https://stanfordnlp.github.io/contract-nli/resources/contract-nli.zip"
  md5 data/raw/contractnli/contract-nli.zip ; shasum -a 256 data/raw/contractnli/contract-nli.zip
  unzip -l data/raw/contractnli/contract-nli.zip | grep -v -E "\.(txt|pdf|htm|html)$"
  ```
- **Explication** : `--retry 10` réessaie en cas d'échec réseau ; `-C -` reprend un téléchargement
  interrompu ; `shasum -a 256` calcule une empreinte SHA-256 (plus robuste que MD5).
- **Résultat** : 65 362 913 octets (= taille annoncée) ; MD5 `d1ab038c2d6d771959a75bbb28792c56` ;
  SHA-256 `e03fc77bbf8b53e2976a250e81d8a294bc3d5e5fb014521e477dee9340d6287b` (aucune empreinte
  officielle publiée) ; contenu : `train.json`, `dev.json`, `test.json`, `LICENSE`, `TERMS`,
  `README.md`, `raw/` (documents d'origine) ; fichier ignoré par Git.

### I4 — Lecture du README, des conditions et des 17 hypothèses (pas des documents)

- **Commandes** : `unzip -p … README.md` ; `unzip -p … TERMS` ;
  `unzip -p … train.json | jq -r '.labels | …'` (`-p` lit un fichier du zip sans l'extraire).
- **Résultat** : format compris (documents, spans = phrases ou éléments de liste, annotations par
  hypothèse : Entailment / Contradiction / NotMentioned + indices de spans d'évidence). Constat :
  **nda-18 (« No solicitation ») n'est pas de la confidentialité**.

### I5 — Liste de mots-clés de la confidentialité, figée AVANT toute évaluation

- **Fichier créé** : `src/cg/extraction/mots_cles_confidentialite.py` (10 motifs justifiés par les
  hypothèses ; aucun pour nda-18).
- **Preuve de l'ordre** : commité immédiatement (commit suivant), avant tout calcul de métriques et
  sans avoir lu aucun document ni aucune évidence.

### I6 — 01:21 — Module de lecture de ContractNLI ; description de train et dev

- **Fichier créé** : `src/cg/datasets/contractnli.py` (lecture dans le zip ; test refusé sans
  `ouvrir_test=True` ; évidences → annotations, sans nda-18).
- **Commande** : script Python court (statistiques de train et dev ; essai de lecture du test).
- **Résultat** : train 423 accords, dev 61 ; positions valides ; 18,7 % des spans (train) servent
  d'évidence ; lecture du test **refusée** (PermissionError), comme prévu.

### I7 — 01:22 — Préparation des segments : bug détecté et corrigé

- **Fichier créé** : `src/cg/datasets/preparer_segments_contractnli.py`.
- **Constat** : 0 % de positifs : `projeter_annotations` ne garde que les catégories CUAD.
- **Correction** : nouvelle fonction `categories_par_segment` dans `src/cg/datasets/cuad.py` (même
  règle de chevauchement, sans filtre), utilisée par ContractNLI. 25 tests passent toujours.
- **Second constat** : le texte de ContractNLI n'a aucune ligne vide (42,7 sauts de ligne par
  accord) → segments v1 de 1 285 caractères en médiane, 55 % de positifs.

### I8 — Segmentation coupée aux lignes ; comparaison

- **Fichier modifié** : `src/cg/ingestion/segmentation.py` (paramètre `coupe_aux_lignes`, défaut
  inchangé). Script Python de remplacement vérifiant chaque repère.
- **Mesure (train ContractNLI)** : v1 médiane 1 285, 31,6 % au plafond ; coupée aux lignes médiane
  132, 2,0 % au plafond, 21,1 % positifs ; spans ContractNLI médiane 101.

### I9 — 01:23 — Mesures pour D-009 (dev ContractNLI + val CUAD, tests fermés)

- **Fichier créé** : `training/baseline_confidentialite.py` (3 options, un run MLflow chacune,
  expérience `F2-confidentialite`).
- **Résultats** : A (NDA seulement) P 0,433 / R 0,877 / F1 0,580 ; B 0,313 / 0,877 / 0,462 ;
  C 0,222 / 0,877 / 0,355. Segments CUAD val avec un mot-clé : 8,8 %, **51 contrats sur 61**.
- `preparer_segments_contractnli` relancé avec la coupe aux lignes : train 18 355 segments
  (21,1 % positifs), dev 2 872 (18,3 %), 0 non traçable.
- **Tests** : `tests/test_contractnli.py` (3), `test_segmenter_coupe_aux_lignes` → **29 passed**.

### I10 — Documentation

- `docs/data_provenance.md` : section ContractNLI (source, empreintes, licence, conditions, format,
  5 limites). `docs/decisions.md` : **D-009 « Proposée »**. README de `datasets/` et `extraction/`.

### I11 — Diagnostic total

- **Fichier créé** : `docs/DIAGNOSTIC_2026-11-16_au_2026-11-23.md` (chronologie, étapes, notions,
  décisions, résultats, limites et erreurs, présentation, commandes pour tout refaire).
- **Sources** : `git log` (20 commits depuis `26f4188`), `gh pr list` (PR #1 à #6), ce journal.

### I12 — Clôture de la séance 3/3 et **fin du mode temporaire**

- `docs/PROGRESS.md`, `README.md`, `docs/FICHE_ENCADRANT.md`, `CLAUDE.md` (compteur 3/3 ; mode
  marqué **terminé** : la règle « Sara exécute les commandes » reprend).
- **Commandes** : `pytest` ; `git add` ; `git commit` ; `git push -u origin exp/contractnli` ;
  `gh pr create` ; `gh pr merge <n> --merge --delete-branch` ; `git pull`.
- **Après cette fusion, Claude n'exécute plus de commande modifiante** : il les donne à Sara.
- **Résultat de I12** : PR #7 créée et **fusionnée** (commit de fusion `1694b5b`), branche
  supprimée ; `main` à jour ; **29 passed** sur `main`. La base `cg-postgres` est toujours démarrée.
- **Fin du mode temporaire (2026-11-23).** Ce dernier paragraphe n'est pas commité par Claude :
  c'est Sara qui le commitera (règle habituelle).

---

## 2026-11-23 — Décisions de Sara et mise en place du second mode (5 séances) — séance 0/5

**Consignes de Sara** : D-009 acceptée telle que proposée (option D prévue plus tard) ; remplacer
l'extrait de date du rapport PDF par une description (règle 5) ; commiter le journal soi-même
(branche, commit, push, PR, fusion) ; **nouveau mode « Claude exécute tout » pour 5 séances**,
mêmes règles et interdits, avec un résumé de 10 lignes maximum à chaque fin de séance et un
diagnostic complet après la 5e ; proposer le plan des 5 séances et attendre sa validation.

### J1 — Mises à jour

- `git switch -c docs/d009-mode-5-seances`.
- `CLAUDE.md` : section « Mode temporaire (5 séances) » (compteur 0/5 à 5/5, fin automatique,
  mêmes interdits, décisions proposées avant d'être notées, résumé court, diagnostic après 5/5) ;
  le premier mode est mentionné en historique.
- `docs/decisions.md` : **D-009 acceptée** (Sara, 2026-11-23).
- `docs/analyses/verification_pdf_pymupdf.md` : le fragment de date d'un contrat est remplacé par
  une description. **Limite** : il reste dans l'historique Git (commit de la PR #5) ; l'en retirer
  imposerait de réécrire l'historique de `main`, ce qui est interdit ; fragment de quelques
  caractères, sans information sur le contrat.
- `docs/FICHE_ENCADRANT.md`, `docs/DIAGNOSTIC_2026-11-16_au_2026-11-23.md`, `docs/PROGRESS.md` :
  statut de D-009.
- Script Python de remplacement vérifiant chaque repère ; `grep -rn "19t h" docs src tests` : aucune
  occurrence restante.

### J2 — Commit, push, PR, fusion

- **Commandes** :
  ```bash
  .venv/bin/python -m pytest -q
  git add CLAUDE.md docs
  git commit -m "docs(claude): D-009 acceptée, règle 5 dans le rapport PDF, mode temporaire de 5 séances"
  git push -u origin docs/d009-mode-5-seances
  gh pr create --base main --head docs/d009-mode-5-seances …
  gh pr merge <n> --merge --delete-branch
  git pull
  ```
- **Résultat de J2** : PR #8 fusionnée (`d990568`) ; 29 tests passent ; compteur 0/5.

---

## Séance 1/5 du second mode — 2026-11-23 — Transformer pour F2

**Plan validé par Sara** : F2 → F4 → F5 → F3 → F6, avec deux corrections : F5 = réponse extractive
(base et comparaison) + petit LLM local (Ollama par exemple) orchestré avec LangGraph (chercher →
vérifier la preuve → répondre ou s'abstenir), citations vérifiées mot pour mot ; F3 = 30 à 50 paires
annotées **par Sara et Ilyas** (pas par Claude), kappa de Cohen. Rappeler à chaque fin de séance ce
qu'Ilyas doit relire (PR #2 à #8).

**Plan de la séance** : installer PyTorch + Transformers ; proposer D-012 (modèle) et D-013
(combiner CUAD et ContractNLI) ; entraîner (train), régler (val / dev), comparer à TF-IDF ;
tests ; MLflow ; PR ; clôture (résumé de 10 lignes, rappel Ilyas).

### K1 — 01:46 — Branche et installation

- **Commandes** : `git switch -c exp/transformer-f2` ;
  `.venv/bin/python -m pip install --retries 10 --timeout 120 --resume-retries 50 --progress-bar off "torch>=2.4" "transformers>=4.44,<5"`.
- **Explication** : PyTorch fait les calculs (sur la puce graphique du Mac, « MPS ») ; Transformers
  fournit les modèles préentraînés. `<5` évite une future version 5 aux changements incompatibles.
- **Résultat** : torch 2.15.0, transformers 4.57.6, MPS disponible ; moins d'une minute (réseau rapide).

### K2 — Candidats pour D-012 (lecture)

- **Commande** : `curl -s "https://huggingface.co/api/models/<modèle>?blobs=true" | jq …` pour 3 modèles.
- **Résultat** : legal-bert-small-uncased 141 Mo (CC BY-SA 4.0) ; legal-bert-base-uncased 440 Mo
  (CC BY-SA 4.0) ; deberta-v3-small 286 Mo (MIT).

### K3 — Code

- `src/cg/extraction/evaluation.py` : `rappel_par_annotation` **déplacée** depuis
  `training/baselines_extraction_pdf.py` (paramètre `dossier_pdf` explicite), script mis à jour et
  vérifié par import.
- `src/cg/extraction/transformer.py` (chargement, boucle d'entraînement à la main, perte pondérée,
  prédiction, MPS) ; `training/transformer_extraction.py` (2 tâches, réglages fixés avant, meilleure
  époque et seuils choisis sur la validation, comparaison TF-IDF, MLflow, sauvegarde dans `models/`).
- `tests/test_transformer.py` : 2 tests avec un minuscule BERT créé localement (aucun téléchargement) → 2 passed.
- `requirements.txt` : `torch>=2.4`, `transformers>=4.44,<5` ; README de `extraction/`.

### K4 — 01:48 — Entraînement lancé

- **Commande** : `MLFLOW_DISABLE_AGENT_HINT=1 PYTHONPATH=src .venv/bin/python training/transformer_extraction.py --tache les-deux`
  (en arrière-plan ; confidentialité puis CUAD). Résultats : K5.

### K5 — 03:07 — Résultats du premier entraînement (validation, tests fermés)

- **Durée** : 01:48 → 03:07 (1 h 19). Modèles dans `models/f2-confidentialite-legal-bert-small` et
  `models/f2-cuad-legal-bert-small` (dossier ignoré par Git).
- **Confidentialité** (dev ContractNLI) : époques 0,851 / 0,845 / **0,862** ; P 0,852, R 0,873,
  **F1 0,862** ; TF-IDF 0,830 ; mots-clés 0,580.
- **CUAD** (validation) : époques 0,385 / 0,501 / 0,506 ; F1 durée 0,673, résiliation 0,344,
  responsabilité 0,502, **macro 0,506** (TF-IDF : 0,656) ; rappel par annotation **0,786** (TF-IDF : 0,724).
- **Défaut de protocole constaté** : tous les seuils choisis valent 0,95, le maximum de la grille.
- **Erreur de Claude** : Python lancé sans `-u` → progression invisible pendant l'entraînement.

### K6 — 03:08 — Réévaluation avec une grille de seuils élargie (sans réentraîner)

- **Fichier créé** : `evaluation/reevaluer_seuils_transformer.py` (recharge les modèles sauvegardés ;
  seuils 0,05…0,95 + 0,96, 0,97, 0,98, 0,99, 0,995, 0,999 ; validation seulement ; runs MLflow
  `…-seuils-elargis`).
- **Commande** : `MLFLOW_DISABLE_AGENT_HINT=1 PYTHONPATH=src .venv/bin/python -u evaluation/reevaluer_seuils_transformer.py`
- **Résultat** : confidentialité inchangée (seuil 0,95, F1 0,862) ; CUAD macro-F1 0,531 (seuils 0,96 /
  0,95 / 0,98), rappel par annotation 0,717. **Le bord de la grille n'était pas la cause principale.**
- **Diagnostic** : la confidentialité (21 % de positifs, poids ≈ 4) marche bien ; CUAD (≈ 1 % de
  positifs, poids ≈ 100) donne beaucoup de fausses alertes → le poids des positifs est trop fort.

### K7 — 03:09 — Expérience 2 : poids des positifs atténué (racine carrée), décidée avant de lancer

- **Fichiers modifiés** : `src/cg/extraction/transformer.py` (`poids_positifs(..., racine=True)`,
  paramètre `poids_racine` ; `perte.detach()` pour supprimer l'avertissement) ;
  `training/transformer_extraction.py` (option `--poids-racine`, modèle et run suffixés
  `-poids-racine`). Test ajouté : `test_poids_positifs_racine` → **32 passed**.
- **Commande** (détachée, progression visible en direct) :
  ```bash
  MLFLOW_DISABLE_AGENT_HINT=1 PYTHONPATH=src nohup .venv/bin/python -u training/transformer_extraction.py --tache cuad --poids-racine > data/processed/progression_transformer_poids_racine.log 2>&1 &
  ```
- **Explication** : `nohup … &` lance le programme en arrière-plan, sans dépendre du terminal ;
  `-u` écrit chaque message immédiatement dans le fichier de progression. Tout le reste est identique.

### K8 — 03:56 — Résultats de l'expérience 2 (validation)

- Époques : 0,510 / 0,614 / **0,625** ; seuils 0,85 / 0,70 / 0,90 (à l'intérieur de la grille) ;
  F1 durée 0,732, résiliation 0,473, responsabilité 0,670 ; rappel par annotation **0,773**
  (TF-IDF 0,724). Modèle : `models/f2-cuad-legal-bert-small-poids-racine`.
- Lignes `MallocStackLogging` dans le journal de progression : messages système de macOS, sans effet.

### K9 — Analyse, décisions proposées, clôture de la séance 1/5

- `docs/analyses/transformer_f2_val.md` ; `docs/decisions.md` : **D-012** et **D-013 « Proposées »** ;
  `README.md` (résultats), `docs/FICHE_ENCADRANT.md`, `docs/PROGRESS.md`, `CLAUDE.md` (compteur 1/5).
- **Commandes** : `pytest` ; `git add` ; `git commit` ; `git push -u origin exp/transformer-f2` ;
  `gh pr create` ; `gh pr merge <n> --merge --delete-branch` ; `git pull`.
- **Résultat de K9** : PR #9 fusionnée (`f4dc3e9`) ; 32 tests passent ; compteur 1/5.

---

## Séance 2/5 du second mode — 2026-11-23 — décisions D-012 / D-013, critère de F2, puis NLI (F4)

### L1 — 04:05 — Décisions de Sara ; branche

- **Décisions** : D-012 acceptée (Legal-BERT small, poids atténué CUAD, normal confidentialité,
  TF-IDF en référence) ; **ajout demandé** : fixer avant toute ouverture du test le critère qui
  départage les modèles de F2 (rappel par annotation sous précision minimale ; macro-F1 en
  complément ; valeur à proposer). D-013 acceptée (deux modèles).
- **Point signalé à Sara** : pour respecter la règle 2, le critère départage les modèles **sur la
  validation** ; le test n'évalue ensuite que le modèle retenu.
- `git switch -c exp/nli-f4`.

### L2 — 04:06 — Précision de TF-IDF sur les segments PDF (validation)

- **Commande** : script Python court qui réutilise `regler` de `training/baselines_extraction_pdf.py`.
- **Résultat** : précision macro 0,728 (durée 0,742, résiliation 0,639, responsabilité 0,803).

### L3 — 04:12 — Critère appliqué sur la validation, 3 valeurs de précision minimale

- **Fichier créé** : `evaluation/critere_selection_f2.py` (seuil = plus petit seuil atteignant la
  précision minimale ; modèles rechargés depuis `models/`, sans réentraînement).
- **Commande** : `MLFLOW_DISABLE_AGENT_HINT=1 PYTHONPATH=src .venv/bin/python -u evaluation/critere_selection_f2.py`
- **Résultats** (rappel par annotation macro) : P ≥ 0,40 : TF-IDF 0,842, Transformer atténué 0,842,
  poids fort 0,621 ; P ≥ 0,50 : **TF-IDF 0,794**, atténué 0,742, poids fort non admissible ;
  P ≥ 0,60 : TF-IDF 0,761, atténué 0,697.
- **Proposition** : précision ≥ 0,50 par famille ; conséquence : TF-IDF retenu pour les 3 familles CUAD.
- `docs/decisions.md` : D-012 acceptée + section « Critère de sélection » (valeur **proposée**) ;
  D-013 acceptée ; `docs/FICHE_ENCADRANT.md` mis à jour.

### L4 — 04:14 — Code de F4 (NLI)

- **Fichiers créés** : `src/cg/nli/` (`__init__.py`, `paires.py`, `modele.py`, `evaluation.py`,
  `README.md`), `training/nli_contractnli.py`, `tests/test_nli.py` (4 tests → passed).
- **Méthode (D-014, à proposer)** : unité = phrase de ContractNLI ; paires (hypothèse, phrase) à
  3 classes ; échantillonnage fixé avant l'entraînement (évidences + 2 neutres par document et
  hypothèse, dont une « difficile ») ; décision du document par agrégation (seuil de confiance →
  sinon NotMentioned ; évidences = phrases au-dessus d'un second seuil) ; seuils réglés sur le dev.
- **Renommage** : `_lots` → `decouper_en_lots` dans `src/cg/extraction/transformer.py` et
  `src/cg/nli/modele.py` (fonction partagée, donc publique). Un premier essai avec `sed 's/\b…'`
  n'a rien fait (`\b` non reconnu par le `sed` de macOS) ; refait avec un script Python (`re.sub`).

### L5 — 04:15 — Entraînement NLI lancé

- **Commande** :
  ```bash
  MLFLOW_DISABLE_AGENT_HINT=1 PYTHONPATH=src nohup .venv/bin/python -u training/nli_contractnli.py > data/processed/progression_nli.log 2>&1 &
  ```
- **Premiers chiffres** (dev, test fermé) : 1 037 couples (document, hypothèse) : 519 Entailment,
  423 NotMentioned, 95 Contradiction. **Baseline majoritaire** : exactitude 0,681, macro-F1 0,633
  (F1 : NotMentioned 0,629, Entailment 0,753, Contradiction 0,516). Paires d'entraînement : 22 606
  (6 762 Entailment, 14 265 NotMentioned, 1 579 Contradiction).

### L6 — 04:18 — Critère de D-012 refait « à la lettre » (validation)

- **Demande de Sara** : confirmer que, pour chaque modèle et chaque famille, le seuil maximise le
  rappel par annotation sous précision ≥ 0,50, ou refaire le calcul.
- **Constat** : le premier calcul prenait le plus petit seuil admissible (rappel par segment
  maximal), équivalent en principe ; refait quand même à la lettre.
- **Fichier créé** : `evaluation/critere_selection_f2_equitable.py` (recherche exhaustive des seuils ;
  correspondance annotation → segments calculée une fois).
- **Résultat** : mêmes seuils et mêmes chiffres. TF-IDF : durée 0,870, résiliation 0,640,
  responsabilité 0,871, macro 0,794 ; Transformer atténué : 0,909, 0,438, 0,879, macro 0,742.
  **La condition de Sara (TF-IDF meilleur sur les 3 familles) n'est pas remplie** → choix en attente.

### L7 — 04:21 — Résultats de l'entraînement NLI (dev)

- Pertes 0,475 → 0,247 ; 86 734 paires évaluées ; seuils document 0,85, évidence 0,95 ;
  exactitude 0,778, macro-F1 0,717 (NotMentioned 0,739, Entailment 0,836, Contradiction 0,575) ;
  évidences P 0,678, R 0,588, F1 0,630. Modèle : `models/f4-nli-legal-bert-small`.

### L8 — 04:22 — Seuils NLI réévalués avec des grilles élargies (le seuil d'évidence était au bord)

- **Fichier créé** : `evaluation/reevaluer_seuils_nli.py` ; **résultat** : mêmes seuils (0,85 ; 0,95),
  mêmes métriques → 0,95 est un vrai optimum.

### L9 — Clôture de la séance 2/5

- `docs/analyses/nli_f4_dev.md` ; `docs/decisions.md` (D-012 : confirmation et tableau par famille,
  choix en attente ; **D-014 proposée**) ; `README.md`, `docs/FICHE_ENCADRANT.md`, `docs/PROGRESS.md`,
  `CLAUDE.md` (compteur 2/5).
- **Commandes** : `pytest` ; `git add` ; `git commit` ; `git push -u origin exp/nli-f4` ;
  `gh pr create` ; `gh pr merge <n> --merge --delete-branch` ; `git pull`.
- **Résultat de L9** : PR #10 fusionnée (`2bc80d4`) ; 36 tests passent ; compteur 2/5.

---

## Séance 3/5 du second mode — 2026-11-23 — F5 : recherche hybride, réponse extractive, LLM local

### M1 — 04:28 — Décisions de Sara ; branche

- **D-012** : option 2 (Transformer pour durée et responsabilité, TF-IDF pour résiliation), avec les
  mises en garde demandées (écart petit 0,809 / 0,794 ; choix par famille sur la validation donc
  optimiste ; seul le test, ouvert une fois, donnera la référence). **D-014** acceptée.
- `git switch -c feat/rag-f5` ; `docs/decisions.md` et `docs/FICHE_ENCADRANT.md` mis à jour.

### M2 — Candidats D-015 et D-016 (lecture)

- **Embeddings** (`curl …/api/models/<m>?blobs=true`) : bge-small-en-v1.5 133 Mo MIT ; all-MiniLM-L6-v2
  90 Mo Apache 2.0 ; e5-small-v2 133 Mo MIT ; nomic-embed-text-v1.5 546 Mo Apache 2.0.
- **Ollama** : déjà installé (0.40.16, serveur actif) ; modèle présent : `qwen3-vl:8b` (6,2 Go) ;
  bibliothèque Ollama : qwen3 4b (2,5 Go), 8b (5,2 Go)… Aucun téléchargement de LLM avant la décision de Sara.

### M3 — 04:33 — Migration de la base pour la recherche

- **Fichier créé** : `db/init/002_recherche.sql` (colonne générée `tsv` + index GIN ; colonne
  `embedding vector(384)` + index HNSW cosinus ; idempotent).
- **Commande** : `docker exec -i cg-postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < db/init/002_recherche.sql`
- **Explication** : `-i` transmet le fichier SQL au conteneur ; `ON_ERROR_STOP=1` arrête à la
  première erreur. **Résultat** : colonnes et index créés.

### M4 — Code de F5

- **Fichiers créés** : `src/cg/recherche/` (`embeddings.py` : encodeur bge, vecteurs normalisés,
  préfixe des questions ; `hybride.py` : recherche par mots (texte intégral PostgreSQL, requête en
  « OU »), par sens (pgvector), fusion RRF, provenance ; `extractive.py` : citer ou s'abstenir ;
  `indexer.py` : calcul des vecteurs en base) ; `evaluation/evaluer_qr_f5.py` ; `tests/test_recherche.py`
  (3 tests, avec de faux vecteurs).

### M5 — Bug trouvé et corrigé : les tests de la base laissaient des contrats

- **Constat** : 96 270 segments au lieu de 96 244 ; 13 contrats `test-…` laissés par les lancements
  de pytest depuis 01:04. **Cause** : après une lecture, la connexion restait dans une transaction
  implicite ; la suppression s'y faisait, puis était **annulée** à la fermeture ; le test la
  vérifiait dans la même transaction et passait à tort (bug de Claude, séance 2/3).
- **Correction** : `src/cg/stockage/connexion.py` → connexions en **autocommit** ; le test vérifie la
  suppression par une **autre** connexion. `pytest tests/test_stockage.py tests/test_recherche.py` →
  6 passed, aucun contrat de test restant.
- **Nettoyage** (données créées par les tests uniquement, filtre strict) :
  `DELETE FROM contrats WHERE source = 'import' AND mode_extraction = 'test' AND titre LIKE 'test-%';`
  → 13 supprimés ; la base revient à **408 contrats, 96 244 segments**.

### M6 — Calcul des vecteurs : téléchargement bloqué, relancé

- **Commande initiale** : `PYTHONPATH=src .venv/bin/python -u -m cg.recherche.indexer` (04:34).
- **Constat** : fichier des poids à 0 octet pendant plus de 2 minutes (client de téléchargement
  « Xet » de Hugging Face, `hf-xet` 1.8.0) ; le fichier était pourtant accessible (`curl -sI`).
- **Correction** : arrêt (`pkill -f cg.recherche.indexer`), suppression du fichier partiel vide
  (`*.incomplete` dans le cache Hugging Face, hors du dépôt), relance avec `HF_HUB_DISABLE_XET=1`
  (téléchargement HTTP classique).

### M7 — 04:39 — Décisions D-015 et D-016 ; licence ; configuration

- **Décisions de Sara** : D-015 bge-small-en-v1.5 ; D-016 `qwen3-vl:8b` (déjà présent), avec
  conditions : licence notée ; nom du modèle en paramètre ; `qwen3:8b` reste la cible ; lien OCR.
- **Licence vérifiée** : `ollama show qwen3-vl:8b --license` → Apache 2.0 ; fiche Hugging Face
  `Qwen/Qwen3-VL-8B-Instruct` → apache-2.0. `ollama show qwen3-vl:8b` : 8,2 milliards de paramètres,
  Q4_K_M, « thinking » désactivable.
- **Fichiers** : `docs/decisions.md` (D-015, D-016), `docs/data_provenance.md` (section « Modèles
  préentraînés utilisés »), `src/cg/config.py` (`CG_LLM_MODELE`, défaut `qwen3-vl:8b` ; `CG_LLM_URL`),
  `.env.example` (2 lignes).
- **LangGraph installé** : `pip install … "langgraph>=0.2"` → langgraph 1.2.24, langchain-core 1.8.4.

### M8 — Erreur de Claude : un `python3` parasite

- Une commande contenait par erreur `python3 - 2>/dev/null` : appel du **Python 3.9 du système**,
  interdit par `CLAUDE.md`. Il a lu une entrée vide et s'est arrêté sans rien exécuter ; mais la
  commande s'est bloquée et sa fin (test de la configuration, retrait d'un import, ajout dans
  `.env.example`) ne s'est pas exécutée. Vérifié, puis refait uniquement avec `.venv/bin/python`.

### M9 — RAG LangGraph

- **Fichiers créés** : `src/cg/recherche/llm.py` (client Ollama, bibliothèque standard),
  `src/cg/recherche/graphe.py` (chercher → générer → vérifier ; citations vérifiées mot pour mot,
  longueur ≥ 15 caractères, positions exactes ; abstention motivée), `src/cg/recherche/questions_cuad.py`
  (déplacé depuis `evaluation/evaluer_qr_f5.py`), `evaluation/evaluer_rag_llm_f5.py`,
  `src/cg/recherche/README.md` ; test du graphe avec un faux LLM (4 tests F5 passent).
- **Essai réel** (passages inventés) : réponse citée et vérifiée en 19,6 s (chargement compris) ;
  abstention correcte en 8,8 s.

### M10 — 04:49 — Évaluation recherche + extractif (validation ; réglage sur 60 contrats du train)

- **Indexation terminée** : 96 244 / 96 244 segments avec vecteur.
- **Commande** : `PYTHONPATH=src .venv/bin/python -u evaluation/evaluer_qr_f5.py`
- **Recherche** (809 questions avec réponse) : rappel@1 / @5 / @10 : mots 0,208 / 0,518 / 0,638 ;
  sens 0,313 / 0,543 / 0,642 ; **hybride 0,323 / 0,586 / 0,682**.
- **Défaut de méthode (Claude)** : réglé sur l'**exactitude**, le seuil (0,76) fait presque toujours
  s'abstenir (2,1 % de réponses) ; or 2/3 des questions n'ont pas de réponse, et « toujours
  s'abstenir » obtient la même exactitude (0,675). Le critère était mauvais d'avance.
- **Correction (après avoir vu ce résultat, à faire valider dans D-017)** : réglage sur l'**exactitude
  équilibrée** (moyenne bonnes réponses / bonnes abstentions ; 0,5 pour « toujours s'abstenir ») →
  seuil 0,71 ; validation : exactitude équilibrée 0,521, 12,5 % de réponses, 68,8 % de réponses fausses.
- **Lecture** : la similarité cosinus ne dit pas si la réponse est dans le contrat.

### M11 — 04:52 — Comparaison extractif / RAG + LLM lancée

- **Commande** : `MLFLOW_DISABLE_AGENT_HINT=1 PYTHONPATH=src nohup .venv/bin/python -u evaluation/evaluer_rag_llm_f5.py --seuil-extractif 0.71 > data/processed/progression_rag_llm.log 2>&1 &`
- 200 questions de validation (graine 0), modèle `qwen3-vl:8b`. Résultats : M12.

### M12 — 05:09 → 08:44 — Deux échecs du RAG + LLM, cause et corrections

- **Échec 1 (05:09)** : erreur 500 d'Ollama dès la première question : « Load failed: timed out
  waiting for llama-server to start » ; chargement du modèle très lent (17 min) avec 3,7 Go de
  mémoire libre sur 24 (nombreuses applications ouvertes ; autre projet dans Docker : conteneurs
  `tp_cdc-*`, ≈ 3 Go, **non touchés** car hors du plan de la séance).
- **Correction 1** : `src/cg/recherche/llm.py` → 3 tentatives (pause de 15 s) sur erreur du serveur ;
  préchauffage du modèle :
  `curl -s -m 900 http://127.0.0.1:11434/api/generate -d '{"model":"qwen3-vl:8b","prompt":"Reply OK.","stream":false,"think":false,"keep_alive":"30m","options":{"num_predict":5}}'`
  → chargé en 5,6 s, 100 % GPU.
- **Échec 2 (07:53)** : dépassement du délai (300 s) de la **première** requête, partie 1 h 30 après
  le lancement (06:17) ; trous dans le journal d'Ollama (06:17 → 07:53 → 08:44) : **mise en veille
  du Mac** pendant le calcul (programmes suspendus, délais dépassés au réveil).
- **Correction 2** : `evaluation/evaluer_rag_llm_f5.py` **reprenable** (chaque réponse écrite dans
  `data/processed/rag_llm_reponses.jsonl`, non commité ; une relance saute les questions déjà
  faites) ; lancement sous **`caffeinate -i`** (outil de macOS qui empêche la veille tant que le
  programme tourne, sans changer les réglages) :
  ```bash
  MLFLOW_DISABLE_AGENT_HINT=1 PYTHONPATH=src nohup caffeinate -i .venv/bin/python -u evaluation/evaluer_rag_llm_f5.py --seuil-extractif 0.71 > data/processed/progression_rag_llm.log 2>&1 &
  ```
  Vérification : `pmset -g assertions` montre « PreventUserIdleSystemSleep … caffeinate ».

### M13 — 11:39 — Troisième échec ; diagnostic par le journal système

- **Constat** : dépassement du délai sur la première question ; `pmset -g log` montre le Mac en
  **veille** (*Sleep*, *Deep Idle*) jusqu'au réveil par l'utilisatrice (11:40, *FullWake … UserActivity*).
  `caffeinate -i` n'empêche pas la veille quand l'écran du portable est fermé.
- **Décision de Claude** : ne pas relancer sans Mac éveillé ; évaluation du LLM **reportée à la
  séance 5/5** (débordement prévu par Sara), Mac ouvert et branché ; le script est reprenable.

### M14 — Clôture de la séance 3/5

- `docs/analyses/qr_f5_val.md` ; `docs/decisions.md` (**D-017 proposée**) ; `README.md` (F5, résultats) ;
  `docs/FICHE_ENCADRANT.md` ; `docs/PROGRESS.md` ; `CLAUDE.md` (compteur 3/5) ; `pytest` → 40 passed.
- **Commandes** : `git add` ; `git commit` ; `git push -u origin feat/rag-f5` ; `gh pr create` ;
  `gh pr merge <n> --merge --delete-branch` ; `git pull`.
- **Résultat de M14** : PR #11 fusionnée (`5a3698f`) ; 40 tests passent ; compteur 3/5.

---

## Séance 4/5 du second mode — 2026-11-24 — F3 : préparation de l'annotation humaine

### N1 — D-017 acceptée ; Recall@5 ; piste NLI

- `git switch -c feat/f3-annotation` ; `docs/decisions.md` (D-017 acceptée, deux précisions, piste
  NLI pour la séance 5) ; Recall@5 ajouté (`docs/FICHE_ENCADRANT.md`, `docs/analyses/qr_f5_val.md`,
  `docs/PROGRESS.md`) — scripts Python de remplacement vérifiant chaque repère.

### N2 — Paires candidates

- **Comptage** (validation, annotations CUAD alignées) : T1 12 paires / 6 contrats ; T2 29 / 14 ;
  T3 70 / 10 ; T4 52 / 12.
- **Fichiers créés** : `src/cg/annotation/` (`creer_paires_f3.py`, `accord.py`, `positions.py`, README).
- **Commande** : `PYTHONPATH=src .venv/bin/python -m cg.annotation.creer_paires_f3`
- **Résultat** : **47 paires** (T1 11, T2 12, T3 12, T4 12 ; 24 contrats) ;
  `data/annotations/f3_paires/paires_v1.csv` (suivi par Git) ; `data/processed/f3_paires_a_lire.md` (ignoré).

### N3 — Guides, modèles, tests

- `docs/annotation/GUIDE_F3_PAIRES.md`, `docs/annotation/GUIDE_F5_QUESTIONS.md` (exemples inventés) ;
  modèles vides `MODELE_annotations.csv`, `MODELE_questions.csv` ; `tests/test_annotations.py`
  (colonnes autorisées, longueurs, étiquettes ; kappa contre scikit-learn ; règle d'alerte).

### N4 — Alertes v1 figées avant les annotations

- **Fichiers créés** : `src/cg/comparison/` (`alertes.py`, `predire_alertes.py`, README).
- **Premier essai** : erreur « Sequence to truncate too short » (une clause en position d'hypothèse
  dépasse la limite avec `truncation="only_second"`) → `src/cg/nli/modele.py` : `longest_first`
  (sans effet pour F4, où l'hypothèse est toujours la plus courte).
- **Commande** : `PYTHONPATH=src .venv/bin/python -m cg.comparison.predire_alertes`
- **Résultat** : 41 alertes sur 47 ; raisons : R3 seule 27, R2+R3 12, R2 seule 2, aucune 6 ; R1 jamais.
  `docs/analyses/f3_alertes_v1_predictions.csv` (sans texte), commité avant toute annotation.
- `pytest` → **45 passed**.

### N5 — Clôture de la séance 4/5

- `docs/decisions.md` (**D-018 proposée**) ; `README.md`, `src/cg/README.md`, `docs/FICHE_ENCADRANT.md`,
  `docs/PROGRESS.md`, `CLAUDE.md` (compteur 4/5).
- **Commandes** : `git add` ; `git commit` ; `git push -u origin feat/f3-annotation` ; `gh pr create` ;
  `gh pr merge <n> --merge --delete-branch` ; `git pull`.
- **Résultat de N5** : PR #12 fusionnée (`f5fd709`) ; 45 tests passent ; compteur 4/5.

---

## Séance 5/5 du second mode — 2026-11-24 — F6 (API, interface), évaluation du LLM, diagnostic

**Plan** : D-018 acceptée ; lancer d'abord l'évaluation du LLM (Mac ouvert, sur secteur) ; API FastAPI
et interface React ; piste « vérification par le NLI » ; clôture, fin du mode, diagnostic complet.

### O1 — 20:58 — D-018 acceptée ; évaluation du LLM lancée

- `git switch -c feat/api-interface-f6` ; D-018 acceptée, avec le lien au **risque n°1 du cahier des
  charges** et son plan de repli (F3 présentée comme étude expérimentale si la faiblesse se confirme).
- `evaluation/evaluer_rag_llm_f5.py` enregistre aussi la phrase de réponse du LLM (pour la piste NLI).
- Préchauffage (`curl … /api/generate … "keep_alive":"60m"`, 4 s) puis lancement sous `caffeinate -i`.

### O2 — Modèle TF-IDF de la résiliation sauvegardé

- **Constat** : le choix de D-012 (TF-IDF pour la résiliation) n'avait jamais été sauvegardé.
- **Fichier créé** : `training/sauvegarder_tfidf_resiliation.py` → `models/f2-resiliation-tfidf.joblib`
  (6,5 Mo, ignoré par Git ; bigrammes, C = 10, train).

### O3 — API et interface

- **Fichiers créés** : `src/cg/extraction/pipeline.py` (modèles et seuils de D-012 / D-013),
  `src/cg/api/` (`services.py`, `app.py`, README), `tests/test_api.py` (4 tests, faux services → passed).
- **Interface** : `npm create vite@5.5.5 frontend -- --template react` puis `npm install` (React 18.3,
  Vite 5.4) ; `frontend/src/App.jsx`, `App.css`, `index.css`, `vite.config.js` (relais `/api` → port
  8000), `index.html` (titre, langue) ; fichiers d'exemple de Vite supprimés ; `npm run build` réussi
  (148 Ko de JavaScript) ; `frontend/dist/` ajouté au `.gitignore`.
- **Documentation** : README de l'API et de l'interface ; section **« Installation »** du README principal
  enfin rédigée ; `requirements.txt` (langgraph, fastapi, uvicorn, python-multipart).

### O4 — Seuil de la confidentialité (critère de D-012, dev)

- **Fichier créé** : `evaluation/seuil_confidentialite.py` ; **résultat** : seuil **0,07** (précision
  0,510, rappel par évidence 0,988, F1 0,671) contre 0,95 (F1 0,862) → **D-019 proposée**.

### O5 — Erreur de Claude : calculs simultanés sur la puce graphique

- La première réponse du LLM a pris 204 s et n'était pas du JSON (texte tronqué) ; Ollama déchargeait
  le modèle. **Cause** : le calcul du seuil (O4) et la compilation de l'interface ont été lancés
  pendant l'évaluation. **Corrections** : `src/cg/recherche/llm.py` → `num_predict = 512` (borne la
  longueur ; un JSON tronqué donne une abstention motivée) ; évaluation arrêtée, fichier de reprise
  vidé, modèle rechargé (18 s), **relance de zéro** à 21:05 ; plus aucun autre calcul GPU en parallèle.

### O6 — D-019 acceptée

- Seuil de la confidentialité **0,95** : exception explicite au critère de D-012 (différence de
  domaine NDA → contrats commerciaux), décidée sur le dev avant tout test ; architecture de F6
  acceptée. `docs/decisions.md`, docstring de `src/cg/extraction/pipeline.py`.

### O7 — 21:12 — Diagnostic : le LLM réfléchit toujours

- **Constat** : après 7 questions, 4 réponses « illisibles », 54 s par question. Sortie brute
  (`/api/chat` appelé directement sur une vraie question) : 512 tokens **tous dans la réflexion**,
  contenu vide. Trois variantes (`think: false` sans JSON ; JSON + `/no_think` ; les deux) : la
  réflexion continue (≈ 920 caractères à 200 tokens), contenu vide.
- **Explication** : `qwen3-vl:8b` est la variante « thinking » (moteur de rendu `qwen3-vl-thinking`).
- **Changement de modèle impossible** : débit mesuré ≈ 53 Ko/s (`curl -r 0-5242879 …`) → 5 Go ≈ 27 h ;
  tags Ollama lus (`curl https://ollama.com/library/qwen3-vl/tags`) : une variante `2b-instruct` existe
  (≈ 10 h). Rien n'a été téléchargé.

### O8 — Essai de bout en bout de l'application (API)

- `src/cg/config.py` : `CG_LLM_NUM_PREDICT` ; serveur :
  `PYTHONPATH=src nohup .venv/bin/python -m uvicorn cg.api.app:app --port 8000 > data/processed/api.log 2>&1 &`
- **Premier import : erreur 500** (titre déjà présent : le contrat de validation est dans la base en
  tant que contrat CUAD ; `UniqueViolation`). **Correction** : `titre_libre` dans
  `src/cg/api/services.py` (suffixe « (import n) ») + test (`tests/test_stockage.py`) → 8 passed.
- **Import** (contrat de validation, `curl -F "fichier=@…;type=application/pdf" http://127.0.0.1:8000/contrats`) :
  11 s, 9 pages, 139 segments, **23 clauses** (confidentialité 6, durée 6, responsabilité 8,
  résiliation 3), **0 segment non traçable** ; question extractive → citation page 6 ; alertes
  (expérimental) : 11 ; NLI (« Some obligations … may survive termination ») → Entailment 0,988,
  3 évidences (pages 1, 6, 7) ; question RAG → abstention « illisible » (boucle de réflexion).

### O9 — Réflexion sans fin à température 0 ; réglages recommandés

- Sortie brute à 2 048 tokens : réflexion de 9 350 caractères, jamais terminée (avec ou sans JSON).
- **Essai** avec les réglages recommandés par Qwen (température 0,6, top_p 0,95, top_k 20, graine 0,
  4 096 tokens) : 73 s, 2 760 tokens, JSON valide, **citation vérifiée** (page 6).
- **Fichiers** : `src/cg/config.py` (`CG_LLM_TEMPERATURE`, `CG_LLM_TOP_P`, `CG_LLM_TOP_K`,
  `CG_LLM_NUM_PREDICT` = 4096), `src/cg/recherche/llm.py`, `.env.example`, `docs/decisions.md`
  (D-016 : constat technique, à valider par Sara).

### O10 — 21:32 — Évaluation indicative (20 questions) avec la piste NLI

- `evaluation/evaluer_rag_llm_f5.py` : option `--taille` ; **piste NLI** (réponse gardée seulement si
  le modèle de F4 juge que le passage cité « implique » la phrase de réponse, seuil 0,5 fixé d'avance).
- Serveur de l'API arrêté (`pkill -f "uvicorn cg.api.app"`) pour libérer la mémoire ; fichier de reprise vidé.
- **Commande** : `… nohup caffeinate -i .venv/bin/python -u evaluation/evaluer_rag_llm_f5.py --seuil-extractif 0.71 --taille 20 …`

### O11 — D-016 : correction acceptée ; téléchargement de `qwen3-vl:8b-instruct`

- **Décision de Sara** : réglages recommandés par Qwen acceptés ; 20 questions = évaluation INDICATIVE ;
  télécharger un modèle sans réflexion obligatoire.
- **Vérification** : `curl -s https://ollama.com/library/qwen3-vl/tags` → `qwen3-vl:8b-instruct` existe
  (6,2 Go) ; choisi (garde la vision, utile pour l'OCR).
- **Commande** (21:44) : `nohup caffeinate -i ollama pull qwen3-vl:8b-instruct > data/processed/ollama_pull.log 2>&1 &`
  → ≈ 336 Ko/s, ≈ 4 h ; fichier principal `a0c1f7c1356e` (5,0 Go). Disque libre : 226 Go.
- **Constat** : des fichiers `-partial` d'un autre téléchargement (22/11, 23:56, antérieur aux séances)
  sont présents dans `~/.ollama/models/blobs/` : non touchés.
- `docs/decisions.md` : plan ajouté à D-016 (configurer `CG_LLM_MODELE`, refaire les 200 questions).

### O12 — 21:59 — Résultats de l'évaluation indicative (20 questions)

- Extractif : exactitude équilibrée 0,423 (0/7 bonnes réponses, 11/13 abstentions, 2 réponses fausses
  sur 2) ; **RAG + LLM : 0,643** (2/7, 13/13, **0 réponse fausse**) ; RAG + vérification NLI : identique.
  Issues : 2 réponses vérifiées, 12 abstentions du LLM, 5 sorties illisibles, 1 citation non retrouvée ;
  82,3 s par question.
- **Erreur de Claude** : enregistrement MLflow refusé (nom de paramètre accentué) ; corrigé (noms en
  ASCII, run NLI ajouté) ; relance immédiate grâce au fichier de reprise (aucun nouvel appel au LLM).

### O13 — Clôture, fin du mode, diagnostic

- `pytest` → **50 passed**. `docs/analyses/qr_f5_val.md` (section indicative), `README.md` (F5, F6,
  résultats), `docs/FICHE_ENCADRANT.md`, `docs/PROGRESS.md` (séance 5/5), `CLAUDE.md` (compteur 5/5 ;
  **mode marqué TERMINÉ**), **`docs/DIAGNOSTIC_2026-11-23_au_2026-11-24.md`** (avec « Comment lancer la
  démonstration », questions et hypothèse qui ont fonctionné).
- **Commandes** : `git add` ; `git commit` ; `git push -u origin feat/api-interface-f6` ; `gh pr create` ;
  `gh pr merge <n> --merge --delete-branch` ; `git pull`.
- **En cours au moment de la clôture** : téléchargement de `qwen3-vl:8b-instruct` (≈ 3 %, ≈ 4 h restantes).
- **Après cette fusion, la règle habituelle reprend : Sara exécute les commandes.**
