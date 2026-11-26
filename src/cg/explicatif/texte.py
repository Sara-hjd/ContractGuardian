"""Conversion des sources téléchargées en texte découpé en segments, avec provenance (F5, D-023).

Place dans le projet : deuxième étape du corpus explicatif, entre le téléchargement
(``cg.explicatif.collecte``) et l'indexation (``cg.explicatif.indexer``). Chaque source devient un
texte unique ; chaque segment garde, comme pour les contrats (règle 1) :
- ses **positions** de début et de fin dans ce texte ;
- sa **page** pour les PDF (``None`` pour une page web, qui n'a pas de pages) ;
- sa **section** (dernier titre rencontré avant le segment), pour pouvoir citer « Section X ».

Les parties sans contenu explicatif des articles Wikipédia (« References », « See also »…) sont retirées.
"""

import bisect
import json
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup

from cg.explicatif.sources import Source
from cg.ingestion.pdf import extraire_pdf
from cg.ingestion.segmentation import MAX_CARACTERES, segmenter

SECTIONS_IGNOREES = {"see also", "references", "further reading", "external links", "notes", "bibliography",
                     "sources", "citations", "footnotes"}
BALISES_TITRE = ("h1", "h2", "h3", "h4", "h5")
BALISES_TEXTE = BALISES_TITRE + ("p", "li", "dt", "dd", "td", "th", "pre", "blockquote")


@dataclass
class DocumentExplicatif:
    """Le texte d'une source et sa structure.

    Attributes:
        cle: Clé de la source.
        texte: Texte complet (paragraphes séparés par une ligne vide).
        titres: Positions et intitulés des titres de section, dans l'ordre.
        pages: Pour un PDF, (début, fin, numéro) de chaque page dans ``texte`` ; vide sinon.
    """

    cle: str
    texte: str
    titres: list[tuple[int, str]] = field(default_factory=list)
    pages: list[tuple[int, int, int]] = field(default_factory=list)

    def section_de(self, position: int) -> str | None:
        """Intitulé du dernier titre placé avant la position (``None`` s'il n'y en a pas)."""
        i = bisect.bisect_right([p for p, _ in self.titres], position) - 1
        return self.titres[i][1] if i >= 0 else None

    def page_de(self, position: int) -> int | None:
        """Numéro de la page qui contient la position (``None`` pour une page web)."""
        for debut, fin, numero in self.pages:
            if debut <= position < fin:
                return numero
        return None


@dataclass(frozen=True)
class SegmentExplicatif:
    """Un passage d'une source explicative, avec sa provenance.

    Attributes:
        cle_source: Clé de la source.
        debut: Position de début dans le texte de la source.
        fin: Position de fin.
        texte: Texte du passage (``document.texte[debut:fin]``).
        page: Page (PDF) ou ``None``.
        section: Titre de la section, ou ``None``.
    """

    cle_source: str
    debut: int
    fin: int
    texte: str
    page: int | None
    section: str | None


def _assembler(cle: str, paragraphes: list[tuple[str, bool]]) -> DocumentExplicatif:
    """Assemble des paragraphes (texte, est_un_titre) en un document."""
    morceaux, titres, position = [], [], 0
    for texte, est_titre in paragraphes:
        texte = " ".join(texte.split())
        if not texte:
            continue
        if morceaux:
            morceaux.append("\n\n")
            position += 2
        if est_titre:
            titres.append((position, texte))
        morceaux.append(texte)
        position += len(texte)
    return DocumentExplicatif(cle, "".join(morceaux), titres)


def _depuis_wikipedia(cle: str, brut: str) -> DocumentExplicatif:
    """Texte brut de l'API Wikipédia : les lignes « == Titre == » sont des titres de section."""
    extrait = json.loads(brut)["query"]["pages"][0]["extract"]
    paragraphes, ignorer = [], False
    for ligne in extrait.split("\n"):
        ligne = ligne.strip()
        if ligne.startswith("==") and ligne.endswith("=="):
            intitule = ligne.strip("= ").strip()
            ignorer = intitule.lower() in SECTIONS_IGNOREES or (ignorer and ligne.startswith("==="))
            if not ignorer:
                paragraphes.append((intitule, True))
        elif ligne and not ignorer:
            paragraphes.append((ligne, False))
    return _assembler(cle, paragraphes)


def _depuis_html(cle: str, html: str) -> DocumentExplicatif:
    """Paragraphes, éléments de liste et titres d'un fragment HTML, dans l'ordre de lecture."""
    soupe = BeautifulSoup(html, "html.parser")
    racine = soupe.find("article") or soupe
    paragraphes = []
    for element in racine.find_all(BALISES_TEXTE):
        # On ne garde que les éléments « feuilles » (sans autre bloc de texte dedans), pour ne pas
        # recopier deux fois le même texte (un <li> qui contient un <p>…).
        if element.name not in BALISES_TITRE and element.find(BALISES_TEXTE):
            continue
        paragraphes.append((element.get_text(" ", strip=True), element.name in BALISES_TITRE))
    return _assembler(cle, paragraphes)


def _depuis_pdf(cle: str, chemin: Path) -> DocumentExplicatif:
    """Texte d'un PDF par blocs (comme les contrats, D-008), avec la position de chaque page."""
    document = extraire_pdf(chemin, cle, mode="blocs")
    return DocumentExplicatif(cle, document.texte, [], [(p.debut, p.fin, p.numero) for p in document.pages])


def lire_source(source: Source, dossier: Path) -> DocumentExplicatif:
    """Lit le fichier téléchargé d'une source et le convertit en document.

    Args:
        source: La source (``cg.explicatif.sources``).
        dossier: Dossier des fichiers téléchargés (``data/raw/explicatif``).

    Returns:
        Le document (texte, titres, pages).
    """
    if source.type == "wikipedia":
        return _depuis_wikipedia(source.cle, (dossier / f"{source.cle}.json").read_text(encoding="utf-8"))
    if source.type == "govuk":
        corps = json.loads((dossier / f"{source.cle}.json").read_text(encoding="utf-8"))["details"]["body"]
        return _depuis_html(source.cle, corps)
    if source.type == "far":
        return _depuis_html(source.cle, (dossier / f"{source.cle}.html").read_text(encoding="utf-8"))
    return _depuis_pdf(source.cle, dossier / f"{source.cle}.pdf")


def segmenter_source(document: DocumentExplicatif, maximum: int = MAX_CARACTERES) -> list[SegmentExplicatif]:
    """Découpe un document en segments (même règle que les contrats), avec page et section.

    Args:
        document: Document produit par ``lire_source``.
        maximum: Longueur maximale d'un segment.

    Returns:
        Les segments ; pour chacun, ``document.texte[debut:fin] == texte``.
    """
    return [SegmentExplicatif(document.cle, s.debut, s.fin, s.texte, document.page_de(s.debut),
                              document.section_de(s.debut))
            for s in segmenter(document.cle, document.texte, maximum)]
