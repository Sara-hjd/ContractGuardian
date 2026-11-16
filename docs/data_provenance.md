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
   - il reste à vérifier pendant l'exploration si `context` est identique au fichier
     correspondant de `full_contract_txt/`.
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
   des contrats. Le zip Zenodo ne contient qu'un seul fichier JSON, sans ce découpage, qui se
   trouverait dans le `data.zip` du dépôt GitHub (à vérifier). Le choix du découpage, et
   sa protection (règle 2), fera l'objet d'une décision avant tout entraînement.
9. **Comptages à réconcilier.** L'article annonce 13 101 clauses annotées ; un premier comptage
   des passages-réponses dans `CUAD_v1.json` donne 13 823. L'écart vient probablement de la
   façon de compter (une clause peut être découpée en plusieurs passages) et sera examiné
   pendant l'exploration.
