"""Outil : retrouver la page et les positions d'un extrait dans un contrat de la base (questions F5).

Place dans le projet : les fichiers d'annotation ne contiennent jamais de texte de contrat (D-003).
Pour indiquer où se trouve la réponse à une question, l'annotateur colle ici l'extrait (copié depuis
le contrat) ; l'outil renvoie **page, début, fin** à recopier dans le fichier d'annotation.

Lancement (base démarrée) :

    PYTHONPATH=src .venv/bin/python -m cg.annotation.positions --titre "TITRE CUAD" --extrait "texte copié"
"""

import argparse

from cg.ingestion.alignement import aligner, normaliser
from cg.stockage.connexion import connecter


def main() -> None:
    """Cherche l'extrait (correspondance exacte après normalisation, D-007) et affiche ses positions."""
    parseur = argparse.ArgumentParser(description="Positions d'un extrait dans un contrat de la base.")
    parseur.add_argument("--titre", required=True)
    parseur.add_argument("--extrait", required=True)
    arguments = parseur.parse_args()
    with connecter() as connexion, connexion.cursor() as curseur:
        curseur.execute("SELECT id, texte_complet FROM contrats WHERE titre = %s", (arguments.titre,))
        ligne = curseur.fetchone()
        if ligne is None:
            raise SystemExit("Contrat introuvable dans la base (vérifier le titre exact).")
        contrat_id, texte = ligne
        position = aligner(arguments.extrait, normaliser(texte, "etendue"), "etendue")
        if position is None:
            raise SystemExit("Extrait introuvable mot pour mot : recopier un passage plus court et exact.")
        debut, fin = position
        curseur.execute("SELECT numero FROM pages WHERE contrat_id = %s AND debut <= %s AND %s < fin",
                        (contrat_id, debut, debut))
        page = curseur.fetchone()
    print(f"page={page[0] if page else '?'} debut={debut} fin={fin}")


if __name__ == "__main__":
    main()
