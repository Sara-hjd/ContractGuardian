# Guide de rédaction — 25 questions pour F5 (cahier des charges)

*Pour : Sara et Ilyas. Version 1, 2026-11-24.*

## But

Évaluer la question-réponse (F5) sur des **questions écrites par des humains**, pas seulement sur
les 41 questions types de CUAD. Le système doit **citer exactement** la réponse, ou **s'abstenir**.

## Ce qu'il faut produire

- **25 questions** au total, dont **au moins 8 sans réponse** dans le contrat visé (le système doit
  s'abstenir).
- Sur des contrats de **validation** CUAD déjà dans la base (liste : clé `"val"` de
  `data/splits/cuad_v1_splits.json`) — **jamais** des contrats de test.
- Varier : durée, résiliation, responsabilité, confidentialité, et d'autres sujets (paiement, droit
  applicable…). Varier aussi les contrats (au moins 8 contrats différents).
- Se répartir le travail (par exemple 13 / 12) ; chaque question a un seul auteur.

## Règles de rédaction

1. Écrire la question **en anglais**, **avec vos mots** : ne pas recopier une phrase du contrat
   (ce serait du texte de contrat dans le dépôt, et une question trop facile).
2. Une question = un seul point (« What is the notice period to terminate for convenience? »).
3. **Question sans réponse** : vérifier en lisant le contrat que la réponse n'y est vraiment pas
   (par exemple, demander une clause d'arbitrage dans un contrat qui n'en a pas).
4. **Question avec réponse** : repérer le passage qui répond, le **copier dans l'outil** ci-dessous
   (pas dans le fichier), et recopier dans le fichier la page et les positions qu'il renvoie.

```bash
docker compose up -d
PYTHONPATH=src .venv/bin/python -m cg.annotation.positions --titre "TITRE CUAD EXACT" --extrait "passage copié du contrat"
# → page=3 debut=12345 fin=12410
```

Pour lire un contrat : `data/raw/cuad/CUAD_v1/full_contract_pdf/` (le PDF d'origine), ou demander à
Claude Code d'exporter son texte dans `data/processed/` (jamais commité).

## Format du fichier

Copier `data/annotations/f5_questions/MODELE_questions.csv` en `questions_v1.csv` (un seul fichier
pour vous deux) ; une ligne par question :

| Colonne | Contenu |
|---|---|
| `id_question` | `Q01` … `Q25` |
| `titre` | titre CUAD exact du contrat |
| `question` | la question, en anglais, avec vos mots (300 caractères maximum) |
| `avec_reponse` | `oui` ou `non` |
| `page`, `debut`, `fin` | positions de la réponse (données par l'outil) ; vides si `avec_reponse = non` |
| `auteur` | identifiant GitHub |
| `date` | AAAA-MM-JJ |

Contrôle : `.venv/bin/python -m pytest tests/test_annotations.py`.
