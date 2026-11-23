"""Enregistrer et relire les contrats et leurs segments dans PostgreSQL (D-010).

Place dans le projet : la base de l'application garde, pour chaque contrat importé, son texte
complet, ses pages et ses segments avec leur provenance (règle 1). Les résultats d'analyse
(F2 et suivantes) pointeront vers ces segments.
"""

import hashlib
from pathlib import Path

import psycopg

from cg.ingestion.pdf import DocumentPdf
from cg.ingestion.segmentation import Segment


def empreinte_fichier(chemin: Path) -> str:
    """Empreinte SHA-256 d'un fichier (repère un même PDF importé deux fois).

    Args:
        chemin: Fichier à lire.

    Returns:
        L'empreinte en hexadécimal.
    """
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def enregistrer_document(
    connexion: psycopg.Connection,
    document: DocumentPdf,
    segments: list[Segment],
    source: str,
    mode_extraction: str,
    chemin_pdf: Path | None = None,
) -> int:
    """Enregistre un contrat, ses pages et ses segments, en une seule transaction.

    Si l'une des insertions échoue, rien n'est enregistré (pas de contrat à moitié importé).

    Args:
        connexion: Connexion ouverte.
        document: Texte complet et pages (``cg.ingestion.pdf.extraire_pdf``).
        segments: Segments du document, avec leur page.
        source: ``"cuad"`` ou ``"import"``.
        mode_extraction: Description de l'extraction, par exemple ``"pymupdf-1.28/blocs"``.
        chemin_pdf: Fichier PDF d'origine (pour son nom et son empreinte), si connu.

    Returns:
        L'identifiant du contrat dans la base.
    """
    with connexion.transaction(), connexion.cursor() as curseur:
        curseur.execute(
            """INSERT INTO contrats (titre, source, nom_fichier, empreinte_sha256,
                                     mode_extraction, texte_complet, nb_pages)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (document.titre, source,
             chemin_pdf.name if chemin_pdf else None,
             empreinte_fichier(chemin_pdf) if chemin_pdf else None,
             mode_extraction, document.texte, len(document.pages)),
        )
        contrat_id = int(curseur.fetchone()[0])
        curseur.executemany(
            "INSERT INTO pages (contrat_id, numero, debut, fin) VALUES (%s, %s, %s, %s)",
            [(contrat_id, p.numero, p.debut, p.fin) for p in document.pages],
        )
        curseur.executemany(
            "INSERT INTO segments (contrat_id, page, debut, fin, texte) VALUES (%s, %s, %s, %s, %s)",
            [(contrat_id, s.page, s.debut, s.fin, s.texte) for s in segments],
        )
    return contrat_id


def lire_segments(connexion: psycopg.Connection, contrat_id: int) -> list[Segment]:
    """Relit les segments d'un contrat, dans l'ordre du texte.

    Args:
        connexion: Connexion ouverte.
        contrat_id: Identifiant du contrat.

    Returns:
        Les segments, avec leur page et leurs positions.
    """
    with connexion.cursor() as curseur:
        curseur.execute(
            """SELECT c.titre, s.debut, s.fin, s.texte, s.page
               FROM segments s JOIN contrats c ON c.id = s.contrat_id
               WHERE s.contrat_id = %s ORDER BY s.debut""",
            (contrat_id,),
        )
        return [Segment(titre=t, debut=d, fin=f, texte=x, page=p) for t, d, f, x, p in curseur.fetchall()]


def compter_segments_non_tracables(connexion: psycopg.Connection, contrat_id: int) -> int:
    """Vérifie la traçabilité **dans la base** : texte du segment et page cohérents.

    En SQL, ``substring(texte from debut + 1 for fin - debut)`` correspond à
    ``texte[debut:fin]`` en Python (SQL compte à partir de 1).

    Args:
        connexion: Connexion ouverte.
        contrat_id: Identifiant du contrat.

    Returns:
        Le nombre de segments dont le texte ne correspond pas aux positions, ou qui sortent de
        leur page ; 0 si tout est traçable.
    """
    with connexion.cursor() as curseur:
        curseur.execute(
            """SELECT count(*)
               FROM segments s
               JOIN contrats c ON c.id = s.contrat_id
               JOIN pages p ON p.contrat_id = s.contrat_id AND p.numero = s.page
               WHERE s.contrat_id = %s
                 AND (substring(c.texte_complet FROM s.debut + 1 FOR s.fin - s.debut) <> s.texte
                      OR s.debut < p.debut OR s.fin > p.fin)""",
            (contrat_id,),
        )
        return int(curseur.fetchone()[0])


def supprimer_contrat(connexion: psycopg.Connection, contrat_id: int) -> None:
    """Supprime un contrat et, en cascade, ses pages, segments et résultats.

    Args:
        connexion: Connexion ouverte.
        contrat_id: Identifiant du contrat.
    """
    with connexion.transaction(), connexion.cursor() as curseur:
        curseur.execute("DELETE FROM contrats WHERE id = %s", (contrat_id,))
