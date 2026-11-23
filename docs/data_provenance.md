# Provenance des données

Ce document recense **chaque jeu de données** utilisé par ContractGuardian : d'où il vient,
quelle version, sous quelle licence, comment on l'utilise et quelles sont ses limites.

Rappels (voir [CLAUDE.md](../CLAUDE.md)) :
- les données brutes sont dans `data/raw/` et ne sont **jamais commitées** ;
- seules les sources autorisées servent à l'entraînement : CUAD, ContractNLI, et nos annotations
  humaines sur des contrats réels ;
- les données de test ne servent **jamais** à régler un modèle.

---

## CUAD — Contract Understanding Atticus Dataset

### Identification

| | |
|---|---|
| **Nom** | Contract Understanding Atticus Dataset (CUAD) |
| **Version** | v1 (champ `"version": "aok_v1.0"` dans `CUAD_v1.json`) |
| **Producteur** | The Atticus Project, Inc. |
| **Source officielle** | Zenodo : https://zenodo.org/records/4595826 |
| **DOI** | [10.5281/zenodo.4595826](https://doi.org/10.5281/zenodo.4595826) |
| **Publication** | 11 mars 2021 (dernière modification de la notice Zenodo : 29 juillet 2021) |
| **Article** | Hendrycks, Burns, Chen, Ball, *CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review*, NeurIPS 2021 (Datasets and Benchmarks Track), [arXiv:2103.06268](https://arxiv.org/abs/2103.06268) |
| **Autres sources** | Site : https://www.atticusprojectai.org/cuad · Code : https://github.com/TheAtticusProject/cuad |

### Téléchargement

| | |
|---|---|
| **Date** | 2026-11-16 |
| **Par** | Sara-hjd |
| **Fichier** | `data/raw/cuad/CUAD_v1.zip` (conservé pour la traçabilité) |
| **Taille** | 105 883 672 octets (105,9 Mo) |
| **Empreinte MD5** | `c38f490a984420b8a62600db401fafd5`, **vérifiée** : identique à celle publiée sur Zenodo |
| **Extraction** | `data/raw/cuad/CUAD_v1/`, 1 051 fichiers, 173,7 Mo |

Commandes utilisées :

```bash
curl -L --create-dirs -o data/raw/cuad/CUAD_v1.zip "https://zenodo.org/records/4595826/files/CUAD_v1.zip?download=1"
md5 data/raw/cuad/CUAD_v1.zip
unzip -q data/raw/cuad/CUAD_v1.zip -d data/raw/cuad/
```

### Licence et citation

- **Licence** : [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
  Utilisation, modification et redistribution autorisées, y compris commerciales,
  **à condition de citer la source**.
- **Contrats sous-jacents** : selon le README de CUAD, l'Atticus Project « ne fait aucune
  déclaration ni garantie » sur le statut de licence des contrats eux-mêmes. Ces contrats
  sont publics et proviennent d'EDGAR (SEC). C'est une raison de plus pour ne pas les
  republier dans notre dépôt (règle 5, D-003).
- **Citation à faire** (rapport, soutenance, README des résultats) :

```bibtex
@article{hendrycks2021cuad,
  title   = {CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review},
  author  = {Dan Hendrycks and Collin Burns and Anya Chen and Spencer Ball},
  journal = {NeurIPS},
  year    = {2021}
}
```

Mention courte : *« Contract Understanding Atticus Dataset (CUAD) v1, The Atticus Project,
CC BY 4.0, DOI 10.5281/zenodo.4595826. »*

### Description

- **510 contrats commerciaux** en anglais, de **25 types** (distribution, licence, maintenance,
  sponsoring…), tirés d'**EDGAR**, la base publique de la SEC américaine.
- **41 catégories** de clauses jugées importantes par des avocats lors d'opérations
  d'entreprise (fusions-acquisitions, investissements…).
- **Plus de 13 000 annotations** (13 101 clauses annotées selon l'article).
- **Processus d'annotation** :
  1. étudiants en droit formés pendant 70 à 100 heures ;
  2. annotation manuelle dans l'outil eBrevia, puis recherche par mots-clés ;
  3. revue catégorie par catégorie ;
  4. revue par des avocats expérimentés ;
  5. revue des suggestions de l'outil d'IA d'eBrevia (« extras ») ;
  6. export final.

  Selon l'article, chaque annotation a été vérifiée par trois annotateurs supplémentaires.

### Contenu du zip

```
CUAD_v1/
├── CUAD_v1.json          40,1 Mo   annotations au format SQuAD 2.0
├── CUAD_v1_README.txt    26,7 Ko   documentation officielle (catégories, processus, licence)
├── master_clauses.csv     4,0 Mo   tableau récapitulatif : 1 ligne par contrat, 83 colonnes
├── full_contract_pdf/    510 PDF   contrats originaux (Part_I/, Part_II/… puis par type)
├── full_contract_txt/    510 TXT   texte brut des contrats, converti depuis les PDF par CUAD
└── label_group_xlsx/      28 XLSX  clauses regroupées par groupe de catégories
```

Le format de **`CUAD_v1.json`** reproduit celui de SQuAD 2.0 :

```
data[]                        → un élément par contrat (510)
 ├─ title                     → nom du contrat
 └─ paragraphs[]
     ├─ context               → texte du contrat
     └─ qas[]                 → une question par catégorie (41)
         ├─ id                → "<titre du contrat>__<catégorie>"
         ├─ question          → "Highlight the parts (if any) of this contract related to "<catégorie>" ..."
         ├─ is_impossible     → true si la catégorie est absente du contrat
         └─ answers[]         → passages : { text, answer_start }
```

### Usage dans ContractGuardian

| Usage | Détail |
|---|---|
| **F2 — Extraction de clauses** | Entraînement et évaluation, d'abord d'une baseline (scikit-learn) puis d'un Transformer, sur les catégories liées à nos familles. |
| **Famille « durée »** | Agreement Date, Effective Date, Expiration Date, Renewal Term, Notice Period To Terminate Renewal |
| **Famille « résiliation »** | Termination For Convenience, Post-Termination Services, Notice Period To Terminate Renewal |
| **Famille « responsabilité »** | Cap On Liability, Uncapped Liability |
| **F3 — Comparaison de clauses** | Source possible de paires de clauses réelles d'un même contrat (à évaluer). |
| **D-003 — Nos annotations** | Les annotations du binôme sur des contrats CUAD les référencent par leur `title` et des positions, sans recopier le texte. |
| **Étape 1** | Exploration : répartition des catégories, longueur des contrats, catégories rares. |

### Limites connues

1. **Pas de catégorie « confidentialité ».** Le mot n'apparaît que comme exemple dans la
   description d'*Uncapped Liability*. Notre 4ᵉ famille devra venir d'ailleurs : voir **D-002**
   (ContractNLI, annotations humaines, ou retrait du périmètre de F2).
2. **Une annotation ne veut pas dire qu'une clause est risquée.** Une annotation signifie
   seulement « ce passage relève de cette catégorie ». Elle ne dit pas si la clause est
   inhabituelle, défavorable ou problématique. ContractGuardian ne doit jamais présenter une
   détection comme un jugement de risque, ni comme un avis juridique.
3. **Les positions `answer_start` sont calculées sur le texte fourni par CUAD** (le champ
   `context` de `CUAD_v1.json`), **pas sur un texte que nous aurions extrait du PDF**. CUAD a
   lui-même converti les PDF en texte. Notre extraction avec PyMuPDF (F1) produira un texte
   différent (espaces, sauts de ligne, ordre de lecture), donc :
   - les positions CUAD ne sont **pas directement transposables** à nos segments ;
   - il faudra une étape d'**alignement** (retrouver chaque passage CUAD dans notre texte),
     documentée et testée, pour respecter la règle de traçabilité (page, positions) ;
   - **vérifié le 2026-11-22** (`notebooks/01_exploration_cuad.ipynb`, sections a.4 et h) :
     les 13 823 positions retombent exactement sur le texte annoté, et `context` est **identique
     caractère pour caractère** au fichier de `full_contract_txt/` pour les 510 contrats.
   - **alignement sur le texte PyMuPDF mesuré le 2026-11-23** (347 contrats du train) : 98,3 % des annotations
     de nos 9 catégories retrouvées après normalisation étendue (D-007, `docs/analyses/verification_pdf_pymupdf.md`).
4. **Le texte converti est imparfait.** D'après le README, la conversion PDF → TXT ne conserve
   ni la mise en page ni les tableaux, et les espaces entre mots et paragraphes sont parfois
   irréguliers. Le texte contient aussi des pieds de page, des numéros de page et des
   mentions de confidentialité ajoutées lors du dépôt à la SEC.
5. **Passages caviardés.** Certaines parties sont masquées par les entreprises (`***`, `___`,
   blancs), et les annotations reflètent ces masquages.
6. **Annotations non contiguës.** Dans `master_clauses.csv` et les fichiers Excel, les annotateurs
   ont remplacé les parties non pertinentes par `<omitted>`. Ces textes ne sont donc pas des
   extraits exacts du contrat.
7. **Représentativité limitée.** Ce sont des contrats américains de sociétés cotées, déposés à
   la SEC, en anglais, répartis inégalement entre 25 types (de 3 à 34 contrats par type).
   Le README précise que ni les catégories ni les contrats ne sont exhaustifs ou représentatifs.
8. **Découpage entraînement/test.** L'article utilise une séparation aléatoire 80 % / 20 %
   des contrats. Le zip Zenodo ne contient pas ce découpage ; il est dans le `data.zip` du dépôt
   GitHub (**vérifié le 2026-11-22**, voir la section suivante) : 408 contrats de train, 102 de
   test, sans recouvrement. **Pas de jeu de validation officiel.** Notre découpage : D-004.
9. **Comptages réconciliés (2026-11-22).** L'article annonce 13 101 clauses annotées ;
   `CUAD_v1.json` contient 13 823 passages-réponses, sans doublon. **13 101 est exactement le
   nombre d'éléments de `master_clauses.csv`.** Une annotation non contiguë y est un seul élément
   (avec `<omitted>`), mais plusieurs passages dans le JSON : éléments + `<omitted>` = 13 834,
   soit l'écart expliqué à 11 passages près (égalité exacte pour 32 catégories sur 41).
   Voir le notebook, sections g.1 à g.3.
10. **Catégories qui se recouvrent.** Une même phrase peut être annotée dans deux catégories :
    125 des 167 passages *Uncapped Liability* ont exactement les positions d'un passage
    *Cap On Liability* (notebook, section f.3). Un modèle multi-étiquette est donc nécessaire,
    et la co-présence de ces deux catégories n'indique pas une incohérence.

---

## CUAD — découpage officiel train / test (`data.zip` du dépôt GitHub)

### Identification

| | |
|---|---|
| **Source** | Dépôt GitHub `TheAtticusProject/cuad`, fichier `data.zip` |
| **Version figée** | commit `7aad649183846688381a147eeb3601aff590fe4a` (2021-03-11), dernier commit touchant `data.zip` |
| **URL utilisée** | `https://raw.githubusercontent.com/TheAtticusProject/cuad/7aad649183846688381a147eeb3601aff590fe4a/data.zip` |
| **Utilisation dans le dépôt officiel** | `run.sh` entraîne sur `data/train_separate_questions.json` et évalue sur `data/test.json` |

### Téléchargement

| | |
|---|---|
| **Date** | 2026-11-22 |
| **Par** | Claude Code, avec l'accord de Sara-hjd (exception de séance, voir `docs/JOURNAL_ACTIONS.md`, B3) |
| **Fichier** | `data/raw/cuad_official/data.zip` (ignoré par Git, **non extrait** : les scripts lisent dans le zip) |
| **Taille** | 18 309 308 octets |
| **Empreinte Git (SHA-1 de blob)** | `1ae94ff0a9b70b2e3b9b8d215737c8bfae460ddc`, **vérifiée** avec `git hash-object` : identique à celle de l'API GitHub |
| **Empreinte MD5** | `24b7c808f1cb6373ae8f4faf49364f98` (calculée localement, pas de référence publiée) |

```bash
curl -sSL --create-dirs -o data/raw/cuad_official/data.zip "<URL ci-dessus>"
git hash-object data/raw/cuad_official/data.zip
```

### Contenu

| Fichier dans le zip | Taille | Contenu |
|---|---|---|
| `CUADv1.json` | 40,1 Mo | **Identique** à `CUAD_v1.json` de Zenodo (même MD5 `5174daa1…`) |
| `train_separate_questions.json` | 35,1 Mo | Train officiel, format SQuAD : **408 contrats** |
| `test.json` | 7,4 Mo | Test officiel, format SQuAD : **102 contrats** |

Vérifications (`PYTHONPATH=src .venv/bin/python -m cg.datasets.creer_splits`) : aucun contrat
commun aux deux fichiers ; leur union est exactement l'ensemble des 510 titres de `CUAD_v1.json`.

### Licence et limites

- **Le dépôt GitHub ne déclare aucune licence** (l'API renvoie `null`). Les données sont celles
  de CUAD, publiées sous CC BY 4.0 sur Zenodo ; on cite CUAD comme ci-dessus. On n'en redistribue
  rien : seuls des **titres** de contrats figurent dans notre fichier de splits (D-005).
- Le découpage officiel est un tirage aléatoire de l'article (80 / 20) : il n'est pas stratifié
  pour nos 9 catégories. Vérification faite : toutes sont présentes dans chacun de nos jeux
  (minimum : 13 contrats *Uncapped Liability* dans le test).
- Il n'y a **pas de validation officielle** : la nôtre (61 contrats) est tirée du train officiel
  (D-004). Nos résultats ne seront pas directement comparables à ceux de l'article (tâche différente).

---

## ContractNLI — accords de confidentialité annotés (D-002)

### Identification

| | |
|---|---|
| **Nom** | ContractNLI: A Dataset for Document-level Natural Language Inference for Contracts |
| **Producteur** | Hitachi America, Ltd. / Stanford NLP (Yuta Koreeda, Christopher Manning) |
| **Source officielle** | https://stanfordnlp.github.io/contract-nli/ (fichier `resources/contract-nli.zip`) |
| **Version** | pas de numéro ; publication initiale 2021-10-05 ; fichier modifié le 2022-02-11 (en-tête HTTP) |
| **Article** | Koreeda & Manning, *Findings of EMNLP 2021*, p. 1907–1919, https://aclanthology.org/2021.findings-emnlp.164 |

### Téléchargement

| | |
|---|---|
| **Date** | 2026-11-23 |
| **Par** | Claude Code, mode temporaire décidé par Sara (journal, I3) |
| **Fichier** | `data/raw/contractnli/contract-nli.zip` (ignoré par Git, **non extrait** : lu directement dans le zip) |
| **Taille** | 65 362 913 octets (identique à la taille annoncée par le serveur) |
| **MD5** | `d1ab038c2d6d771959a75bbb28792c56` (calculée ; aucune empreinte officielle publiée) |
| **SHA-256** | `e03fc77bbf8b53e2976a250e81d8a294bc3d5e5fb014521e477dee9340d6287b` |

```bash
curl -sSL --retry 10 --retry-delay 5 -C - --create-dirs -o data/raw/contractnli/contract-nli.zip "https://stanfordnlp.github.io/contract-nli/resources/contract-nli.zip"
shasum -a 256 data/raw/contractnli/contract-nli.zip
```

### Licence, conditions et citation

- **Licence** : CC BY 4.0 (fichier `LICENSE` du zip).
- **Conditions d'utilisation** (fichier `TERMS`, Hitachi America) : accéder au jeu de données vaut
  acceptation de ces conditions ; l'usage est régi par CC BY 4.0. **À lire par Sara et Ilyas.**
- **Citation** :

```bibtex
@inproceedings{koreeda-manning-2021-contractnli-dataset,
  title     = {ContractNLI: A Dataset for Document-level Natural Language Inference for Contracts},
  author    = {Koreeda, Yuta and Manning, Christopher},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2021},
  year      = {2021},
  pages     = {1907--1919}
}
```

### Contenu et format

- **607 accords de confidentialité (NDA)**, **17 hypothèses** fixes (par exemple « Receiving Party
  shall not reverse engineer… »). Découpage officiel : **train 423**, **dev 61**, test 123
  (déduit par soustraction : le test n'a pas été ouvert).
- Pour chaque document : texte, *spans* (phrases ou éléments de liste, positions en caractères),
  et pour chaque hypothèse un choix (`Entailment`, `Contradiction`, `NotMentioned`) et les indices
  des spans d'**évidence**. Positions vérifiées valides sur train et dev.
- Train : 3 530 Entailment, 841 Contradiction, 2 820 NotMentioned ; 18,7 % des spans servent
  d'évidence (au moins une hypothèse).

### Usage dans ContractGuardian

| Usage | Détail |
|---|---|
| **F2 — famille confidentialité** | Évidences des hypothèses (sauf nda-18, D-009) projetées sur nos segments. |
| **F4 — NLI** | Jeu d'entraînement et d'évaluation prévu. |

### Limites connues

1. **Uniquement des NDA** : des contrats dont la confidentialité est l'objet même. Une clause de
   confidentialité dans un contrat commercial (CUAD) peut être rédigée autrement.
2. **Les évidences répondent aux 17 hypothèses**, pas à « toute clause de confidentialité » : un
   segment qui parle de confidentialité sans servir d'évidence est compté négatif (25,8 % des
   segments négatifs du dev contiennent un mot-clé de confidentialité).
3. **Texte sans lignes vides** : un paragraphe par ligne ; la segmentation v1 doit couper à chaque
   saut de ligne (D-009), sinon les segments font ~1 300 caractères.
4. **nda-18 (« No solicitation »)** n'est pas de la confidentialité : exclue de la famille (D-009).
5. **CUAD n'annote pas la confidentialité**, alors que 51 contrats de validation CUAD sur 61
   contiennent des mots de la confidentialité : on ne peut pas utiliser CUAD comme source de
   négatifs « propres » (D-009).

---

## Modèles préentraînés utilisés

Les modèles ne sont **pas** des données d'entraînement : ils sont téléchargés (ou présents
localement) et ne sont **jamais commités** (`models/`, cache Hugging Face, cache Ollama).

| Modèle | Usage | Source | Licence (vérifiée) | Date |
|---|---|---|---|---|
| `nlpaueb/legal-bert-small-uncased` | F2 (extraction), F4 (NLI) — D-012, D-014 | Hugging Face | CC BY-SA 4.0 | 2026-11-23 |
| `BAAI/bge-small-en-v1.5` | F5 (embeddings) — D-015 | Hugging Face | MIT | 2026-11-23 |
| `qwen3-vl:8b` (Qwen3-VL 8B Instruct, 8,2 milliards de paramètres, quantification Q4_K_M) | F5 (réponse générative) — D-016 | Ollama (déjà présent localement, téléchargé hors du projet le 2026-11-22) ; modèle d'origine `Qwen/Qwen3-VL-8B-Instruct` | **Apache 2.0** (licence affichée par `ollama show qwen3-vl:8b --license` et fiche Hugging Face officielle) | vérifiée le 2026-11-23 |

**Limites** :
- Legal-BERT a été préentraîné sur des textes juridiques incluant des contrats EDGAR : certains
  contrats de CUAD (eux aussi issus d'EDGAR) ont pu y figurer (pas leurs étiquettes).
- `qwen3-vl:8b` a été obtenu en dehors du projet (déjà sur la machine) : sa provenance exacte est
  celle de la bibliothèque Ollama ; empreinte locale : identifiant Ollama `9cf69da2b16d`.
