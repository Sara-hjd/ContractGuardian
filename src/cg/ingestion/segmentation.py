"""Découpage d'un texte de contrat en segments, avec leurs positions (D-001, règle v1).

Ce module est le point de départ de la traçabilité (F7) : chaque segment garde les positions
exactes de début et de fin dans le texte source, de sorte que ``texte[debut:fin]`` redonne
toujours le texte du segment.

Règle de découpage v1 :
    1. Couper aux lignes vides (paragraphes).
    2. Retirer les espaces aux deux bords de chaque bloc, en décalant les positions ;
       supprimer les blocs vides.
    3. Recouper les blocs de plus de ``MAX_CARACTERES`` aux sauts de ligne simples, en
       regroupant les lignes ; une ligne seule trop longue est coupée au dernier espace.

Pour l'instant, le texte source est le champ ``context`` de CUAD (pas de numéro de page).
Les textes extraits de PDF par PyMuPDF (F1) réutiliseront la même structure ``Segment``.
"""

import re
from dataclasses import dataclass

# Un Transformer lit environ 512 tokens, soit à peu près 2 000 caractères d'anglais juridique.
# On garde une marge, car le découpage en tokens varie selon les mots.
MAX_CARACTERES: int = 1500

# Une ligne vide : un saut de ligne, éventuellement des espaces ou tabulations, puis un autre
# saut de ligne. Les textes CUAD contiennent souvent des lignes « vides » faites d'espaces.
_LIGNE_VIDE = re.compile(r"\n[^\S\n]*\n")


@dataclass(frozen=True)
class Segment:
    """Un morceau de contrat et sa provenance.

    Attributes:
        titre: Identifiant du contrat (pour CUAD : le champ ``title``).
        debut: Position du premier caractère du segment dans le texte source.
        fin: Position juste après le dernier caractère (convention Python des tranches).
        texte: Le texte du segment, égal à ``texte_source[debut:fin]``.
        page: Numéro de page, ou ``None`` quand le texte source n'a pas de pages (CUAD).
    """

    titre: str
    debut: int
    fin: int
    texte: str
    page: int | None = None


def _retirer_bords(texte: str, debut: int, fin: int) -> tuple[int, int]:
    """Resserre l'intervalle [debut, fin) pour exclure les espaces des deux bords.

    Args:
        texte: Texte source complet.
        debut: Début de l'intervalle.
        fin: Fin de l'intervalle (exclue).

    Returns:
        Le nouvel intervalle ; ``debut == fin`` s'il ne contenait que des espaces.
    """
    while debut < fin and texte[debut].isspace():
        debut += 1
    while fin > debut and texte[fin - 1].isspace():
        fin -= 1
    return debut, fin


def _blocs_paragraphes(texte: str) -> list[tuple[int, int]]:
    """Étapes 1 et 2 : intervalles des paragraphes séparés par des lignes vides.

    Args:
        texte: Texte source complet.

    Returns:
        Les intervalles (debut, fin) non vides, sans espaces aux bords, dans l'ordre du texte.
    """
    intervalles: list[tuple[int, int]] = []
    debut = 0
    for separateur in _LIGNE_VIDE.finditer(texte):
        intervalles.append((debut, separateur.start()))
        debut = separateur.end()
    intervalles.append((debut, len(texte)))

    blocs = [_retirer_bords(texte, d, f) for d, f in intervalles]
    return [(d, f) for d, f in blocs if f > d]


def _couper_ligne_longue(texte: str, debut: int, fin: int, maximum: int) -> list[tuple[int, int]]:
    """Coupe une ligne trop longue au dernier espace avant la limite.

    Args:
        texte: Texte source complet.
        debut: Début de la ligne.
        fin: Fin de la ligne (exclue).
        maximum: Longueur maximale d'un morceau.

    Returns:
        Les intervalles des morceaux, sans espaces aux bords.
    """
    morceaux: list[tuple[int, int]] = []
    while fin - debut > maximum:
        coupure = texte.rfind(" ", debut + 1, debut + maximum)
        if coupure == -1:  # aucun espace : coupure franche à la limite
            coupure = debut + maximum
        d, f = _retirer_bords(texte, debut, coupure)
        if f > d:
            morceaux.append((d, f))
        debut, fin = _retirer_bords(texte, coupure, fin)
    if fin > debut:
        morceaux.append((debut, fin))
    return morceaux


def _recouper_bloc(texte: str, debut: int, fin: int, maximum: int) -> list[tuple[int, int]]:
    """Étape 3 : recoupe un bloc trop long en regroupant ses lignes.

    Args:
        texte: Texte source complet.
        debut: Début du bloc.
        fin: Fin du bloc (exclue).
        maximum: Longueur maximale d'un segment.

    Returns:
        Les intervalles des morceaux, chacun d'au plus ``maximum`` caractères.
    """
    if fin - debut <= maximum:
        return [(debut, fin)]

    # Intervalles des lignes du bloc (sans espaces aux bords), lignes longues déjà coupées.
    lignes: list[tuple[int, int]] = []
    position = debut
    while position < fin:
        saut = texte.find("\n", position, fin)
        fin_ligne = fin if saut == -1 else saut
        d, f = _retirer_bords(texte, position, fin_ligne)
        if f > d:
            lignes.extend(_couper_ligne_longue(texte, d, f, maximum))
        position = fin_ligne + 1

    # Regroupement glouton : on ajoute des lignes tant que le morceau reste sous la limite.
    morceaux: list[tuple[int, int]] = []
    debut_courant, fin_courante = lignes[0]
    for d, f in lignes[1:]:
        if f - debut_courant <= maximum:
            fin_courante = f
        else:
            morceaux.append((debut_courant, fin_courante))
            debut_courant, fin_courante = d, f
    morceaux.append((debut_courant, fin_courante))
    return morceaux


def segmenter(titre: str, texte: str, maximum: int = MAX_CARACTERES) -> list[Segment]:
    """Découpe le texte d'un contrat en segments selon la règle v1.

    Args:
        titre: Identifiant du contrat, recopié dans chaque segment.
        texte: Texte complet du contrat (pour CUAD : le champ ``context``).
        maximum: Longueur maximale d'un segment, en caractères.

    Returns:
        Les segments dans l'ordre du texte. Ils ne se chevauchent pas, et pour chacun
        ``texte[segment.debut:segment.fin] == segment.texte``.

    Raises:
        ValueError: Si ``maximum`` n'est pas strictement positif.
    """
    if maximum <= 0:
        raise ValueError(f"maximum doit être strictement positif, reçu : {maximum}")

    segments: list[Segment] = []
    for debut_bloc, fin_bloc in _blocs_paragraphes(texte):
        for debut, fin in _recouper_bloc(texte, debut_bloc, fin_bloc, maximum):
            segments.append(Segment(titre=titre, debut=debut, fin=fin, texte=texte[debut:fin]))
    return segments


def fusionner_fragments(
    texte: str, segments: list[Segment], seuil: int, maximum: int = MAX_CARACTERES
) -> list[Segment]:
    """Rattache chaque segment trop court au segment suivant (option 3 de D-008, expérience).

    Un segment de moins de ``seuil`` caractères (titre, numéro, ligne isolée) est fusionné avec
    le segment qui le suit, si les deux sont sur la **même page** et si le résultat ne dépasse
    pas ``maximum``. Le segment fusionné couvre ``[debut du premier, fin du second)`` : il reste
    traçable (``texte[debut:fin] == segment.texte``).

    Args:
        texte: Texte complet sur lequel portent les positions des segments.
        segments: Segments dans l'ordre du texte, sans chevauchement.
        seuil: Longueur en dessous de laquelle un segment est rattaché au suivant ;
            0 = aucune fusion.
        maximum: Longueur maximale d'un segment fusionné.

    Returns:
        Les segments après fusion, dans l'ordre du texte.
    """
    resultat: list[Segment] = []
    en_attente: Segment | None = None  # fragment court qui attend d'être rattaché au suivant
    for segment in segments:
        if en_attente is not None:
            if en_attente.page == segment.page and segment.fin - en_attente.debut <= maximum:
                segment = Segment(titre=segment.titre, debut=en_attente.debut, fin=segment.fin,
                                  texte=texte[en_attente.debut:segment.fin], page=segment.page)
            else:
                resultat.append(en_attente)  # impossible à rattacher : on le garde tel quel
            en_attente = None
        if segment.fin - segment.debut < seuil:
            en_attente = segment
        else:
            resultat.append(segment)
    if en_attente is not None:
        resultat.append(en_attente)
    return resultat
