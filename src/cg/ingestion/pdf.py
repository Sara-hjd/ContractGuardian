"""Extraction du texte d'un contrat PDF avec PyMuPDF, page par page (F1).

Place dans le projet : c'est l'entrée de l'application. Un utilisateur fournit un PDF ; ce module
produit le texte complet et la position de chaque page dans ce texte, puis des segments (D-001)
qui portent leur **numéro de page** en plus de leurs positions (traçabilité, F7).

Choix v1 : les pages sont séparées par une ligne vide (``SEPARATEUR_PAGES``). Comme la
segmentation v1 coupe aux lignes vides, **aucun segment ne chevauche deux pages** : chaque
segment a un numéro de page exact. Contrepartie : une clause coupée par un saut de page donne
deux segments.
"""

import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from cg.ingestion.segmentation import MAX_CARACTERES, Segment, segmenter

SEPARATEUR_PAGES: str = "\n\n"


@dataclass(frozen=True)
class Page:
    """Une page et sa place dans le texte complet du document.

    Attributes:
        numero: Numéro de la page, à partir de 1 (comme dans un lecteur PDF).
        debut: Position du premier caractère de la page dans le texte complet.
        fin: Position juste après le dernier caractère de la page.
    """

    numero: int
    debut: int
    fin: int


@dataclass(frozen=True)
class DocumentPdf:
    """Le texte extrait d'un PDF et le découpage en pages.

    Attributes:
        titre: Identifiant du contrat.
        texte: Texte complet : les pages mises bout à bout, séparées par ``SEPARATEUR_PAGES``.
        pages: Les pages, dans l'ordre.
    """

    titre: str
    texte: str
    pages: list[Page]

    def page_de(self, position: int) -> int:
        """Numéro de la page qui contient une position du texte complet.

        Args:
            position: Position dans ``texte``.

        Returns:
            Le numéro de la page (à partir de 1).

        Raises:
            ValueError: Si la position tombe hors de toute page (dans un séparateur ou hors du texte).
        """
        for page in self.pages:
            if page.debut <= position < page.fin:
                return page.numero
        raise ValueError(f"Position {position} hors des pages de {self.titre}")


def extraire_pdf(chemin: Path, titre: str) -> DocumentPdf:
    """Extrait le texte d'un PDF, page par page.

    Args:
        chemin: Chemin du fichier PDF.
        titre: Identifiant du contrat, recopié dans le document.

    Returns:
        Le document : texte complet et positions de chaque page.
    """
    morceaux: list[str] = []
    pages: list[Page] = []
    position = 0
    with pymupdf.open(chemin) as document:
        for numero, page in enumerate(document, start=1):
            if numero > 1:
                morceaux.append(SEPARATEUR_PAGES)
                position += len(SEPARATEUR_PAGES)
            # « text » : texte brut dans l'ordre de lecture proposé par PyMuPDF.
            texte_page = page.get_text("text")
            morceaux.append(texte_page)
            pages.append(Page(numero=numero, debut=position, fin=position + len(texte_page)))
            position += len(texte_page)
    return DocumentPdf(titre=titre, texte="".join(morceaux), pages=pages)


def segmenter_pdf(document: DocumentPdf, maximum: int = MAX_CARACTERES) -> list[Segment]:
    """Segmente un document PDF (règle v1) et ajoute le numéro de page à chaque segment.

    Args:
        document: Document produit par ``extraire_pdf``.
        maximum: Longueur maximale d'un segment.

    Returns:
        Les segments, avec ``page`` renseigné ; ``document.texte[debut:fin] == texte``.
    """
    return [
        Segment(titre=s.titre, debut=s.debut, fin=s.fin, texte=s.texte, page=document.page_de(s.debut))
        for s in segmenter(document.titre, document.texte, maximum)
    ]


def _cle_titre(titre: str) -> str:
    """Forme normalisée d'un titre ou d'un nom de fichier, pour les comparer.

    Args:
        titre: Titre CUAD ou nom de fichier sans extension.

    Returns:
        Le titre en Unicode composé (NFC), sans espaces ni tirets aux bords.
    """
    return unicodedata.normalize("NFC", titre).strip().rstrip("-_ ").strip()


def trouver_pdf(dossier_pdf: Path, titre: str) -> Path:
    """Retrouve le PDF CUAD d'un contrat à partir de son titre.

    Le nom du fichier est le titre dans 505 cas sur 510 ; sinon il diffère par un espace ou un
    tiret final, l'encodage d'une lettre accentuée, ou un suffixe ajouté au nom.

    Args:
        dossier_pdf: Dossier ``full_contract_pdf/`` de CUAD (parcouru récursivement).
        titre: Titre du contrat dans ``CUAD_v1.json``.

    Returns:
        Le chemin du PDF.

    Raises:
        FileNotFoundError: Si aucun PDF, ou plusieurs, correspondent au titre.
    """
    fichiers = [p for p in dossier_pdf.rglob("*") if p.suffix.lower() == ".pdf"]
    exacts = [p for p in fichiers if p.stem == titre]
    if len(exacts) == 1:
        return exacts[0]
    cle = _cle_titre(titre)
    normalises = [p for p in fichiers if _cle_titre(p.stem) == cle]
    if len(normalises) == 1:
        return normalises[0]
    prefixes = [p for p in fichiers if _cle_titre(p.stem).startswith(cle)]
    if len(prefixes) == 1:
        return prefixes[0]
    raise FileNotFoundError(f"{len(prefixes)} PDF correspondent au titre : {titre}")
