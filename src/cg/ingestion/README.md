# `src/cg/ingestion/` — lecture et segmentation des contrats (F1)

Rôle : transformer le texte d'un contrat en **segments** (D-001), chacun avec sa **provenance**
(contrat, positions de début et de fin, page quand elle est connue). C'est la base de la
traçabilité (F7) : toute sortie du projet pointera vers un segment.

## Fichiers

| Fichier | Contenu |
|---|---|
| `segmentation.py` | La classe `Segment` et la fonction `segmenter(titre, texte)` (règle v1). |
| `pdf.py` | `extraire_pdf` (PyMuPDF, texte page par page + positions des pages ; modes « texte » et « blocs », D-008), `segmenter_pdf` (segments avec numéro de page), `trouver_pdf` (PDF CUAD d'un titre). |
| `alignement.py` | `normaliser` (niveaux « espaces » et « etendue », lien avec les positions d'origine) et `aligner` (retrouver un passage CUAD dans le texte PyMuPDF). |

Les pages sont séparées par une ligne vide : un segment PDF ne chevauche jamais deux pages, et son numéro de page est exact. Vérification sur des PDF CUAD : `evaluation/verifier_extraction_pdf.py`.

## Règle de segmentation v1

1. **Couper aux lignes vides** (paragraphes).
2. **Retirer les espaces aux bords** de chaque bloc en décalant les positions ; supprimer les
   blocs vides.
3. **Plafond de 1 500 caractères** (`MAX_CARACTERES`) : un bloc plus long est recoupé aux sauts
   de ligne simples, en regroupant les lignes ; une ligne seule trop longue est coupée au dernier
   espace. Raison : un Transformer lit environ 512 tokens (≈ 2 000 caractères).

Garantie : les segments ne se chevauchent pas, et `texte[s.debut:s.fin] == s.texte`
(vérifié par `tests/test_tracabilite.py`).

## Exemple

```python
from cg.ingestion.segmentation import segmenter

segments = segmenter("mon_contrat", texte)
premier = segments[0]
print(premier.debut, premier.fin, premier.texte)
```
