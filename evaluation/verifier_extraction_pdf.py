"""Script : vérifier l'extraction PDF (PyMuPDF) et l'alignement des annotations CUAD (étape 2).

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python evaluation/verifier_extraction_pdf.py

Sur un échantillon de contrats du **train** (le test n'est pas touché), le script mesure :
- les pages extraites, dont les pages sans texte (PDF scanné : il faudrait de l'OCR) ;
- la différence entre le texte PyMuPDF et le texte ``context`` de CUAD ;
- la traçabilité des segments PDF : ``texte[debut:fin] == segment`` et page cohérente ;
- le taux d'annotations CUAD retrouvées dans le texte PyMuPDF, pour deux niveaux de
  normalisation (``espaces``, ``etendue``), sur nos 9 catégories et sur les 41.

Les passages non retrouvés sont écrits dans ``data/processed/alignement_echecs.jsonl``
(texte de contrat : jamais commité).
"""

import json
import random
import time
from pathlib import Path

from cg.datasets.cuad import FAMILLE_DE, charger_cuad
from cg.datasets.splits import lire_splits
from cg.ingestion.alignement import Niveau, aligner, normaliser
from cg.ingestion.pdf import extraire_pdf, segmenter_pdf, trouver_pdf
from cg.ingestion.segmentation import segmenter

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1"
CHEMIN_SPLITS = RACINE / "data" / "splits" / "cuad_v1_splits.json"
CHEMIN_ECHECS = RACINE / "data" / "processed" / "alignement_echecs.jsonl"

TAILLE_ECHANTILLON = 10
GRAINE = 0
NIVEAUX: tuple[Niveau, ...] = ("espaces", "etendue")


def main() -> None:
    """Extrait, compare, aligne et affiche un résumé par contrat et global."""
    textes, annotations = charger_cuad(DOSSIER_CUAD / "CUAD_v1.json")
    jeu_de = lire_splits(CHEMIN_SPLITS)
    train = sorted(t for t, jeu in jeu_de.items() if jeu == "train")
    echantillon = random.Random(GRAINE).sample(train, TAILLE_ECHANTILLON)

    par_contrat: dict[str, list] = {}
    for a in annotations:
        par_contrat.setdefault(a.titre, []).append(a)

    totaux = {(n, portee): [0, 0] for n in NIVEAUX for portee in ("nos9", "toutes")}
    lignes_echecs: list[dict[str, object]] = []
    print(f"{'contrat':42s} {'pages':>5s} {'vides':>5s} {'car. CUAD':>9s} {'car. PDF':>9s} "
          f"{'seg CUAD':>8s} {'seg PDF':>7s} {'trac.':>5s} {'align esp.':>10s} {'align étendue':>13s}")
    for titre in echantillon:
        debut_chrono = time.perf_counter()
        document = extraire_pdf(trouver_pdf(DOSSIER_CUAD / "full_contract_pdf", titre), titre)
        segments_pdf = segmenter_pdf(document)
        pages_vides = sum(1 for p in document.pages if not document.texte[p.debut:p.fin].strip())

        # Traçabilité : texte exact, et le segment est entièrement dans sa page.
        tracable = all(
            document.texte[s.debut:s.fin] == s.texte
            and document.pages[s.page - 1].debut <= s.debut
            and s.fin <= document.pages[s.page - 1].fin
            for s in segments_pdf
        )

        contexte = textes[titre]
        resultats_contrat: dict[Niveau, tuple[int, int]] = {}
        for niveau in NIVEAUX:
            cible = normaliser(document.texte, niveau)
            trouves = total = 0
            for a in par_contrat.get(titre, []):
                passage = contexte[a.debut:a.fin]
                position = aligner(passage, cible, niveau, a.debut / max(len(contexte), 1))
                portees = ("toutes", "nos9") if a.categorie in FAMILLE_DE else ("toutes",)
                for portee in portees:
                    totaux[(niveau, portee)][1] += 1
                    totaux[(niveau, portee)][0] += position is not None
                total += 1
                trouves += position is not None
                if position is None and niveau == "etendue":
                    lignes_echecs.append({"titre": titre, "categorie": a.categorie,
                                          "debut_cuad": a.debut, "fin_cuad": a.fin, "texte": passage})
            resultats_contrat[niveau] = (trouves, total)

        e, t = resultats_contrat["espaces"]
        e2, _ = resultats_contrat["etendue"]
        print(f"{titre[:42]:42s} {len(document.pages):5d} {pages_vides:5d} {len(contexte):9d} "
              f"{len(document.texte):9d} {len(segmenter(titre, contexte)):8d} {len(segments_pdf):7d} "
              f"{'oui' if tracable else 'NON':>5s} {f'{e}/{t}':>10s} {f'{e2}/{t}':>13s}"
              f"   ({time.perf_counter() - debut_chrono:.1f} s)")

    print("\nTaux d'annotations retrouvées dans le texte PyMuPDF :")
    for niveau in NIVEAUX:
        for portee, nom in (("nos9", "nos 9 catégories"), ("toutes", "les 41 catégories")):
            ok, total = totaux[(niveau, portee)]
            print(f"  normalisation {niveau:8s} | {nom:17s} : {ok}/{total} = {ok / max(total, 1):.1%}")

    CHEMIN_ECHECS.parent.mkdir(parents=True, exist_ok=True)
    with open(CHEMIN_ECHECS, "w", encoding="utf-8") as sortie:
        for ligne in lignes_echecs:
            sortie.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    print(f"\n{len(lignes_echecs)} passages non retrouvés (niveau étendu) écrits dans "
          f"{CHEMIN_ECHECS.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
