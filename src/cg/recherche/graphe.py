"""RAG avec LangGraph : chercher → générer → vérifier la preuve → répondre ou s'abstenir (F5, D-017).

Place dans le projet : réponse **générative** à une question sur un contrat, construite au-dessus de
la recherche hybride (D-015) et du LLM local (D-016), et comparée à la réponse extractive.

Le graphe (LangGraph) a trois étapes :
1. **chercher** : recherche hybride dans le contrat (5 meilleurs segments) ;
2. **générer** : le LLM reçoit la question et **seulement** ces passages numérotés ; il doit répondre
   en JSON, avec des citations copiées mot pour mot, ou s'abstenir ;
3. **vérifier** : chaque citation doit exister **mot pour mot** dans le passage cité (seuls les
   espaces et sauts de ligne sont normalisés). Une seule citation fausse → **abstention**. Chaque
   citation vérifiée reçoit ses positions exactes dans le contrat (règle 1). Si une fonction
   ``impliquer`` est fournie (vérification NLI, D-022, ``cg.recherche.verification_nli``), la réponse
   n'est gardée que si au moins un passage cité l'**implique** ; sinon, **abstention**.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypedDict

from langgraph.graph import END, StateGraph

from cg.ingestion.alignement import aligner, normaliser
from cg.recherche.hybride import Resultat

LONGUEUR_MIN_CITATION: int = 15  # une citation de 2 ou 3 mots (« the Company ») ne prouve rien

CONSIGNES = (
    "You help a reader find information in ONE contract. Use ONLY the numbered passages below. "
    "Never use outside knowledge and never give legal advice. "
    "If the passages do not answer the question, reply exactly: {\"abstention\": true}. "
    "Otherwise reply in JSON: {\"abstention\": false, \"reponse\": \"<one short sentence>\", "
    "\"citations\": [{\"passage\": <passage number>, \"extrait\": \"<words copied EXACTLY from that passage>\"}]}. "
    "Every extrait must be copied word for word from the passage (no paraphrase, no ellipsis)."
)


@dataclass(frozen=True)
class Citation:
    """Une citation vérifiée, avec sa provenance exacte.

    Attributes:
        segment_id: Segment cité.
        page: Page du segment.
        debut: Position de début de l'extrait dans le texte complet du contrat.
        fin: Position de fin de l'extrait.
        extrait: Texte de l'extrait, tel qu'il figure dans le contrat.
    """

    segment_id: int
    page: int
    debut: int
    fin: int
    extrait: str


@dataclass
class ReponseRag:
    """Réponse générative, ou abstention, avec la raison.

    Attributes:
        abstention: Vrai si le système ne répond pas.
        raison: Pourquoi on s'abstient (aucun passage, choix du LLM, citation non vérifiée…).
        reponse: Phrase de réponse du LLM (vide en cas d'abstention).
        citations: Citations vérifiées (vide en cas d'abstention).
    """

    abstention: bool
    raison: str = ""
    reponse: str = ""
    citations: list[Citation] = field(default_factory=list)


class Etat(TypedDict, total=False):
    """État partagé entre les étapes du graphe."""

    question: str
    passages: list[Resultat]
    sortie_llm: str
    resultat: ReponseRag


def verifier_citation(passage: Resultat, extrait: str) -> Citation | None:
    """Vérifie qu'un extrait existe mot pour mot dans le passage, et calcule ses positions.

    Args:
        passage: Le segment cité.
        extrait: Le texte que le LLM affirme citer.

    Returns:
        La citation avec ses positions dans le contrat, ou ``None`` si l'extrait est introuvable
        ou trop court pour prouver quoi que ce soit.
    """
    if len(" ".join(extrait.split())) < LONGUEUR_MIN_CITATION:
        return None
    position = aligner(extrait, normaliser(passage.texte, "espaces"), "espaces")
    if position is None:
        return None
    d, f = position
    return Citation(segment_id=passage.segment_id, page=passage.page, debut=passage.debut + d,
                    fin=passage.debut + f, extrait=passage.texte[d:f])


def analyser_sortie(sortie: str, passages: list[Resultat]) -> ReponseRag:
    """Transforme la réponse JSON du LLM en réponse vérifiée, ou en abstention.

    Args:
        sortie: Texte renvoyé par le LLM.
        passages: Passages qui lui ont été montrés, dans l'ordre de leur numéro (1, 2, …).

    Returns:
        La réponse avec citations vérifiées, ou une abstention motivée.
    """
    try:
        donnees = json.loads(sortie)
    except json.JSONDecodeError:
        return ReponseRag(abstention=True, raison="réponse du LLM illisible (pas du JSON)")
    if not isinstance(donnees, dict) or donnees.get("abstention", True):
        return ReponseRag(abstention=True, raison="le LLM s'abstient")
    citations_brutes = donnees.get("citations") or []
    if not citations_brutes:
        return ReponseRag(abstention=True, raison="réponse sans citation")
    citations: list[Citation] = []
    for c in citations_brutes:
        try:
            numero = int(c.get("passage"))
            extrait = str(c.get("extrait", ""))
        except (TypeError, ValueError, AttributeError):
            return ReponseRag(abstention=True, raison="citation mal formée")
        if not 1 <= numero <= len(passages):
            return ReponseRag(abstention=True, raison="citation d'un passage inexistant")
        verifiee = verifier_citation(passages[numero - 1], extrait)
        if verifiee is None:
            return ReponseRag(abstention=True, raison="citation non retrouvée mot pour mot")
        citations.append(verifiee)
    return ReponseRag(abstention=False, reponse=str(donnees.get("reponse", "")), citations=citations)


def construire_graphe(
    chercher: Callable[[str], list[Resultat]],
    generer: Callable[[list[dict[str, str]]], str],
    impliquer: Callable[[str, list[str]], bool] | None = None,
):
    """Assemble le graphe LangGraph.

    Args:
        chercher: Fonction question → passages (par exemple la recherche hybride dans un contrat).
        generer: Fonction messages → texte du LLM (par exemple ``cg.recherche.llm.discuter``).
        impliquer: Vérification NLI facultative ``(reponse, textes des passages cités) -> bool``
            (D-022). ``None`` : vérification mot pour mot seulement.

    Returns:
        Le graphe compilé ; ``graphe.invoke({"question": …})["resultat"]`` donne la réponse.
    """

    def etape_chercher(etat: Etat) -> Etat:
        return {"passages": chercher(etat["question"])}

    def apres_recherche(etat: Etat) -> str:
        return "generer" if etat["passages"] else "rien_trouve"

    def etape_rien_trouve(etat: Etat) -> Etat:
        return {"resultat": ReponseRag(abstention=True, raison="aucun passage trouvé")}

    def etape_generer(etat: Etat) -> Etat:
        texte = "\n\n".join(f"[{i}] {p.texte}" for i, p in enumerate(etat["passages"], start=1))
        messages = [{"role": "system", "content": CONSIGNES},
                    {"role": "user", "content": f"Question: {etat['question']}\n\nPassages:\n{texte}"}]
        return {"sortie_llm": generer(messages)}

    def etape_verifier(etat: Etat) -> Etat:
        resultat = analyser_sortie(etat["sortie_llm"], etat["passages"])
        if impliquer is not None and not resultat.abstention:
            cites = {c.segment_id for c in resultat.citations}
            textes = [p.texte for p in etat["passages"] if p.segment_id in cites]
            if not impliquer(resultat.reponse, textes):
                resultat = ReponseRag(abstention=True, raison="réponse non impliquée par les passages cités (NLI)")
        return {"resultat": resultat}

    graphe = StateGraph(Etat)
    graphe.add_node("chercher", etape_chercher)
    graphe.add_node("rien_trouve", etape_rien_trouve)
    graphe.add_node("generer", etape_generer)
    graphe.add_node("verifier", etape_verifier)
    graphe.set_entry_point("chercher")
    graphe.add_conditional_edges("chercher", apres_recherche, {"generer": "generer", "rien_trouve": "rien_trouve"})
    graphe.add_edge("generer", "verifier")
    graphe.add_edge("verifier", END)
    graphe.add_edge("rien_trouve", END)
    return graphe.compile()
