# Conventions du projet

Ce document détaille les règles de code et de Git de ContractGuardian.
Les règles absolues du projet sont dans [CLAUDE.md](../CLAUDE.md).

## 1. Documentation du code

### Règles

- **Chaque module** (fichier `.py`) commence par une docstring qui dit son rôle.
- **Chaque fonction et classe publique** a une docstring au **style Google** :
  `Args:`, `Returns:`, et `Raises:` si elle lève des exceptions.
- **Annotations de type partout** : paramètres, retours, attributs.
- **Les commentaires expliquent le pourquoi**, pas le quoi : le code dit déjà ce qu'il fait.
- **Chaque sous-dossier de `src/cg/`** contient un `README.md` : rôle, fichiers, comment l'utiliser.

### Exemple de docstring

```python
"""Découpage des contrats PDF en segments avec provenance (F1).

Ce module lit un PDF avec PyMuPDF et produit des segments de texte. Chaque segment
conserve sa page et ses positions, pour que toute sortie du projet puisse citer sa source.
"""

from dataclasses import dataclass


@dataclass
class Segment:
    """Un passage de texte du contrat et sa provenance.

    Attributes:
        text: Le texte du segment.
        page: Numéro de page (commence à 1).
        start: Position du premier caractère dans le texte de la page.
        end: Position juste après le dernier caractère.
    """

    text: str
    page: int
    start: int
    end: int


def find_segments(segments: list[Segment], keyword: str) -> list[Segment]:
    """Renvoie les segments qui contiennent un mot-clé.

    Args:
        segments: Les segments du contrat.
        keyword: Le mot recherché, sans tenir compte des majuscules.

    Returns:
        Les segments qui contiennent le mot-clé, dans l'ordre du document.

    Raises:
        ValueError: Si le mot-clé est vide.
    """
    if not keyword:
        raise ValueError("Le mot-clé ne peut pas être vide.")
    return [s for s in segments if keyword.lower() in s.text.lower()]
```

### Bon et mauvais commentaire

```python
# ❌ Mauvais : répète ce que le code dit déjà.
# On met le texte en minuscules.
text = text.lower()

# ✅ Bon : explique pourquoi.
# Les contrats écrivent "Term", "TERM" ou "term" selon les sections :
# on compare en minuscules pour ne rater aucune occurrence.
text = text.lower()
```

## 2. Conventions Git

### Branches

- `main` contient uniquement du travail terminé et relu.
- **Une branche par tâche**, nommée `type/description-courte` :
  - `feat/pdf-ingestion`
  - `docs/readme-installation`
  - `exp/baseline-tfidf-cuad`
- On fusionne dans `main` quand la tâche respecte la définition de « terminé » (section 3).

### Format des commits

```
type(module): description à l'impératif, en minuscules
```

| Type | Usage | Exemple |
|---|---|---|
| `feat` | nouvelle fonctionnalité | `feat(ingestion): extraire le texte page par page` |
| `fix` | correction de bug | `fix(ingestion): conserver les positions après nettoyage` |
| `docs` | documentation | `docs(readme): compléter l'installation macOS` |
| `test` | tests | `test(extraction): couvrir les clauses de résiliation` |
| `refactor` | réorganisation sans changer le comportement | `refactor(retrieval): séparer recherche lexicale et vectorielle` |
| `exp` | expérience (entraînement, évaluation) | `exp(extraction): baseline TF-IDF + régression logistique sur CUAD` |
| `chore` | maintenance | `chore(deps): ajouter PyMuPDF` |

Le `(module)` peut être omis quand le commit concerne tout le projet,
par exemple `docs: initialiser la documentation du projet`.

### Jamais commité

- **Données** : `data/raw/`, `data/processed/`, `storage/`, contrats PDF.
  Seule exception : `data/annotations/`, qui est versionné mais ne contient **jamais** le texte
  des contrats, uniquement des références (voir D-003).
- **Modèles entraînés** : `models/`, `*.bin`, `*.safetensors`, `*.pt`, `*.ckpt`.
- **Résultats MLflow** : `mlruns/`.
- **Secrets** : `.env`, `.env.*` (seul `.env.example`, sans vraies valeurs, est autorisé).
- **Fichiers générés** : `.venv/`, `__pycache__/`, `node_modules/`, `.DS_Store`…

Ces fichiers sont exclus par le [.gitignore](../.gitignore). **Avant chaque commit**,
vérifier avec `git status` qu'aucun d'eux n'apparaît.

## 3. Définition de « terminé »

Une tâche est terminée quand **toutes** les cases sont cochées :

- [ ] Le code fonctionne et a été testé à la main (commande et résultat notés).
- [ ] Les tests automatisés (`pytest`) passent.
- [ ] Chaque module a sa docstring, chaque fonction sa docstring Google, et tout est typé.
- [ ] Le `README.md` du sous-dossier concerné est à jour.
- [ ] Toute sortie produite référence un segment avec sa provenance (page, positions).
- [ ] Les données de test n'ont servi à régler aucun modèle.
- [ ] Aucune donnée, aucun modèle, aucun secret dans `git status`.
- [ ] Les messages de commit respectent le format `type(module): description`.
- [ ] Pour une expérience : le run est enregistré dans MLflow et le résultat est reporté dans le README.
- [ ] `docs/PROGRESS.md` est mis à jour, et `docs/decisions.md` aussi si un choix a été fait.
