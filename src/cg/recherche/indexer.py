"""Script : calculer et enregistrer les vecteurs (embeddings) des segments de la base (F5).

Lancement, depuis la racine du projet, avec le .venv et la base démarrée :

    PYTHONPATH=src .venv/bin/python -u -m cg.recherche.indexer

Ne traite que les segments sans vecteur : on peut le relancer sans refaire le travail déjà fait.
"""

import time

from cg.recherche.embeddings import Encodeur, vers_pgvector
from cg.stockage.connexion import connecter

TAILLE_PAQUET = 2048


def main() -> None:
    """Encode les segments sans vecteur, par paquets, et les enregistre."""
    encodeur = Encodeur()
    debut = time.perf_counter()
    total = 0
    with connecter() as connexion:
        while True:
            with connexion.cursor() as curseur:
                curseur.execute("SELECT id, texte FROM segments WHERE embedding IS NULL ORDER BY id LIMIT %s",
                                (TAILLE_PAQUET,))
                lignes = curseur.fetchall()
            if not lignes:
                break
            vecteurs = encodeur.encoder([t for _, t in lignes])
            with connexion.transaction(), connexion.cursor() as curseur:
                curseur.executemany("UPDATE segments SET embedding = %s::vector WHERE id = %s",
                                    [(vers_pgvector(v), i) for (i, _), v in zip(lignes, vecteurs)])
            total += len(lignes)
            print(f"  {total} segments encodés ({time.perf_counter() - debut:.0f} s)", flush=True)
    print(f"Terminé : {total} segments en {time.perf_counter() - debut:.0f} s")


if __name__ == "__main__":
    main()
