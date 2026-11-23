"""Script : importer un contrat PDF dans la base (extraction par blocs, D-008).

Lancement, depuis la racine du projet, avec le .venv et la base démarrée (docker compose up -d) :

    PYTHONPATH=src .venv/bin/python -m cg.stockage.ingerer_pdf chemin/vers/contrat.pdf [--titre T]

Extrait le texte page par page (PyMuPDF, mode « blocs »), segmente (règle v1), enregistre
contrat, pages et segments, puis vérifie la traçabilité directement dans la base.
"""

import argparse
from pathlib import Path

import pymupdf

from cg.ingestion.pdf import extraire_pdf, segmenter_pdf
from cg.stockage.connexion import connecter
from cg.stockage.depot import compter_segments_non_tracables, enregistrer_document


def main() -> None:
    """Lit les arguments, importe le PDF et affiche un résumé."""
    parseur = argparse.ArgumentParser(description="Importer un contrat PDF dans la base.")
    parseur.add_argument("pdf", type=Path, help="Chemin du fichier PDF.")
    parseur.add_argument("--titre", help="Identifiant du contrat (par défaut : nom du fichier).")
    parseur.add_argument("--source", default="import", choices=["import", "cuad"])
    arguments = parseur.parse_args()

    titre = arguments.titre or arguments.pdf.stem
    document = extraire_pdf(arguments.pdf, titre, mode="blocs")
    segments = segmenter_pdf(document)
    pages_vides = [p.numero for p in document.pages if not document.texte[p.debut:p.fin].strip()]

    with connecter() as connexion:
        contrat_id = enregistrer_document(
            connexion, document, segments, arguments.source,
            f"pymupdf-{pymupdf.VersionBind}/blocs", arguments.pdf,
        )
        non_tracables = compter_segments_non_tracables(connexion, contrat_id)

    print(f"Contrat importé : id={contrat_id}, « {titre} »")
    print(f"  pages : {len(document.pages)} (sans texte : {pages_vides or 'aucune'})")
    print(f"  segments : {len(segments)} ; non traçables dans la base : {non_tracables}")
    if pages_vides:
        print("  ⚠️ Des pages n'ont pas de texte (page blanche ou scan) : elles ne sont pas analysées.")


if __name__ == "__main__":
    main()
