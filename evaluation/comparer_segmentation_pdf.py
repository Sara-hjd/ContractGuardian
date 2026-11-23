"""Script : comparer deux façons de segmenter les PDF (décision D-008), sur train + validation.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python evaluation/comparer_segmentation_pdf.py

Compare, sur les contrats de **train et de validation** (jamais le test) :
- référence : segmentation v1 sur le texte CUAD (``data/processed/cuad_segments_v1.jsonl``) ;
- ``texte`` : segmentation v1 sur le texte brut de PyMuPDF ;
- ``blocs`` : segmentation v1 sur les blocs PyMuPDF (un bloc = un paragraphe visuel).

Mesures : longueur des segments ; traçabilité (texte exact, segment dans sa page) ; part des
annotations de nos 9 catégories alignées (D-007) puis projetées sur au moins un segment ; part
entièrement contenue dans un seul segment ; part de segments positifs par famille.
"""

import statistics
import time
from pathlib import Path

from cg.datasets.cuad import FAMILLE_DE, FAMILLES, SEUIL_CHEVAUCHEMENT, Annotation, charger_cuad, chevauchement
from cg.datasets.segments import charger_segments
from cg.datasets.splits import lire_splits
from cg.ingestion.alignement import aligner, normaliser
from cg.ingestion.pdf import ModeExtraction, extraire_pdf, segmenter_pdf, trouver_pdf
from cg.datasets.cuad import projeter_annotations

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1"
CHEMIN_SPLITS = RACINE / "data" / "splits" / "cuad_v1_splits.json"
CHEMIN_SEGMENTS_CUAD = RACINE / "data" / "processed" / "cuad_segments_v1.jsonl"
JEUX = {"train", "val"}  # le test reste fermé (règle 2)
MODES: tuple[ModeExtraction, ...] = ("texte", "blocs")


def resume_longueurs(longueurs: list[int]) -> str:
    """Résumé lisible d'une liste de longueurs de segments.

    Args:
        longueurs: Longueurs en caractères.

    Returns:
        Nombre, médiane, déciles 10 % et 90 %, part < 20 et part ≥ 1 400 caractères.
    """
    triees = sorted(longueurs)
    n = len(triees)
    return (f"n={n:6d}  médiane={statistics.median(triees):6.0f}  p10={triees[n // 10]:5d}  "
            f"p90={triees[9 * n // 10]:5d}  <20 car.={sum(x < 20 for x in triees) / n:5.1%}  "
            f"≥1400 car.={sum(x >= 1400 for x in triees) / n:5.1%}")


def main() -> None:
    """Calcule et affiche les mesures pour la référence CUAD et les deux modes PDF."""
    textes, annotations = charger_cuad(DOSSIER_CUAD / "CUAD_v1.json")
    titres = sorted(t for t, jeu in lire_splits(CHEMIN_SPLITS).items() if jeu in JEUX)
    nos_annotations: dict[str, list[Annotation]] = {}
    for a in annotations:
        if a.categorie in FAMILLE_DE:
            nos_annotations.setdefault(a.titre, []).append(a)

    # Référence : segments du texte CUAD (déjà étiquetés par preparer_segments).
    reference = charger_segments(CHEMIN_SEGMENTS_CUAD, JEUX)
    longueurs_ref = (reference["fin"] - reference["debut"]).tolist()
    print(f"Contrats : {len(titres)} (train + val)\n")
    print(f"{'CUAD (référence)':18s} {resume_longueurs(longueurs_ref)}")
    print(f"{'':18s} segments positifs : " + "  ".join(
        f"{f} {reference[f].mean():.2%}" for f in FAMILLES))

    for mode in MODES:
        debut_chrono = time.perf_counter()
        longueurs: list[int] = []
        non_tracables = 0
        alignees = projetees = contenues = total = 0
        positifs = {f: 0 for f in FAMILLES}
        nb_segments = 0
        for titre in titres:
            document = extraire_pdf(trouver_pdf(DOSSIER_CUAD / "full_contract_pdf", titre), titre, mode)
            segments = segmenter_pdf(document)
            nb_segments += len(segments)
            longueurs += [s.fin - s.debut for s in segments]
            non_tracables += sum(
                1 for s in segments
                if document.texte[s.debut:s.fin] != s.texte
                or not (document.pages[s.page - 1].debut <= s.debut and s.fin <= document.pages[s.page - 1].fin)
            )

            # D-007 : alignement exact après normalisation étendue ; les échecs sont exclus.
            cible = normaliser(document.texte, "etendue")
            contexte = textes[titre]
            annotations_pdf: list[Annotation] = []
            for a in nos_annotations.get(titre, []):
                total += 1
                position = aligner(contexte[a.debut:a.fin], cible, "etendue", a.debut / len(contexte))
                if position is None:
                    continue
                alignees += 1
                b = Annotation(titre, a.categorie, position[0], position[1])
                annotations_pdf.append(b)
                seuil = min(SEUIL_CHEVAUCHEMENT, b.fin - b.debut)
                if any(chevauchement(s.debut, s.fin, b.debut, b.fin) >= seuil for s in segments):
                    projetees += 1
                if any(s.debut <= b.debut and b.fin <= s.fin for s in segments):
                    contenues += 1
            for etiquete in projeter_annotations(segments, annotations_pdf):
                for f in etiquete.familles:
                    positifs[f] += 1

        print(f"\n{'PDF « ' + mode + ' »':18s} {resume_longueurs(longueurs)}")
        print(f"{'':18s} segments positifs : " + "  ".join(
            f"{f} {positifs[f] / nb_segments:.2%}" for f in FAMILLES))
        print(f"{'':18s} traçabilité (texte + page) : {nb_segments - non_tracables}/{nb_segments}")
        print(f"{'':18s} annotations (nos 9) : alignées {alignees}/{total} = {alignees / total:.1%} ; "
              f"projetées sur ≥ 1 segment {projetees}/{total} = {projetees / total:.1%} ; "
              f"entières dans un seul segment {contenues}/{alignees} = {contenues / alignees:.1%}")
        print(f"{'':18s} durée : {time.perf_counter() - debut_chrono:.0f} s")


if __name__ == "__main__":
    main()
