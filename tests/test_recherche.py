"""Tests de F5 : réponse extractive, format pgvector, recherche hybride dans la base.

Le test d'intégration crée un petit contrat avec des vecteurs écrits à la main (aucun modèle
téléchargé) et le supprime à la fin. Il est ignoré si la base ne répond pas.
"""

import uuid

import numpy as np
import pytest

from cg.recherche.embeddings import vers_pgvector
from cg.recherche.extractive import repondre
from cg.recherche.hybride import Resultat


def resultat(similarite: float) -> Resultat:
    """Un résultat de recherche fictif."""
    return Resultat(segment_id=1, page=1, debut=0, fin=10, texte="0123456789", similarite=similarite)


def test_repondre_ou_s_abstenir() -> None:
    """Sous le seuil : abstention ; au-dessus : le segment est cité tel quel."""
    assert repondre([], 0.5).abstention
    assert repondre([resultat(0.4)], 0.5).abstention
    reponse = repondre([resultat(0.7)], 0.5)
    assert not reponse.abstention and reponse.citation.texte == "0123456789"


def test_vers_pgvector() -> None:
    """Format texte attendu par pgvector."""
    assert vers_pgvector(np.array([0.5, -0.25])) == "[0.500000,-0.250000]"


class FauxEncodeur:
    """Remplace le modèle d'embeddings : renvoie toujours le même vecteur de question."""

    def encoder_requete(self, question: str) -> np.ndarray:
        """Vecteur fixe, proche du segment sur la responsabilité."""
        v = np.zeros(384)
        v[0] = 1.0
        return v


def test_recherche_hybride_dans_la_base() -> None:
    """Mots et sens retrouvent le bon segment ; la provenance est conservée."""
    psycopg = pytest.importorskip("psycopg")
    from cg.recherche.hybride import rechercher
    from cg.stockage.connexion import connecter

    try:
        connexion = connecter()
    except (KeyError, psycopg.OperationalError) as erreur:
        pytest.skip(f"Base indisponible : {erreur}")
    with connexion:
        with connexion.cursor() as c:
            c.execute("SELECT count(*) FROM information_schema.columns WHERE table_name = 'segments' AND column_name = 'embedding'")
            if c.fetchone()[0] == 0:
                pytest.skip("Migration db/init/002_recherche.sql non appliquée.")
        texte = "Liability is capped at fees paid.\n\nThe term is two years."
        with connexion.transaction(), connexion.cursor() as c:
            c.execute("INSERT INTO contrats (titre, source, mode_extraction, texte_complet, nb_pages) "
                      "VALUES (%s, 'import', 'test', %s, 1) RETURNING id", (f"test-{uuid.uuid4()}", texte))
            cid = c.fetchone()[0]
            c.execute("INSERT INTO pages VALUES (%s, 1, 0, %s)", (cid, len(texte)))
            proche, loin = np.zeros(384), np.zeros(384)
            proche[0], loin[1] = 1.0, 1.0
            for (d, f), v in (((0, 33), proche), ((35, len(texte)), loin)):
                c.execute("INSERT INTO segments (contrat_id, page, debut, fin, texte, embedding) "
                          "VALUES (%s, 1, %s, %s, %s, %s::vector)", (cid, d, f, texte[d:f], vers_pgvector(v)))
        try:
            for mode in ("mots", "sens", "hybride"):
                trouves = rechercher(connexion, FauxEncodeur(), cid, "liability cap", 2, mode)
                assert trouves[0].texte == "Liability is capped at fees paid."
                assert texte[trouves[0].debut:trouves[0].fin] == trouves[0].texte
            assert rechercher(connexion, FauxEncodeur(), cid, "liability cap", 2, "sens")[0].similarite == pytest.approx(1.0)
        finally:
            with connexion.transaction(), connexion.cursor() as c:
                c.execute("DELETE FROM contrats WHERE id = %s", (cid,))


def test_graphe_rag_verifie_les_citations() -> None:
    """Graphe LangGraph avec un faux LLM : citation exacte → réponse ; citation inventée → abstention."""
    pytest.importorskip("langgraph")
    from cg.recherche.graphe import construire_graphe

    passage = Resultat(segment_id=7, page=3, debut=100, fin=150,
                       texte="Either party may terminate this\nAgreement upon 30 days notice.")

    def faux_llm(extrait: str):
        return lambda messages: ('{"abstention": false, "reponse": "Yes.", "citations": '
                                 '[{"passage": 1, "extrait": "%s"}]}' % extrait)

    juste = construire_graphe(lambda q: [passage], faux_llm("may terminate this Agreement upon 30 days"))
    r = juste.invoke({"question": "Can a party terminate?"})["resultat"]
    assert not r.abstention
    c = r.citations[0]
    assert (c.page, c.segment_id) == (3, 7)
    assert " ".join(c.extrait.split()) == "may terminate this Agreement upon 30 days"
    assert c.debut == 100 + passage.texte.index("may")  # positions dans le contrat

    inventee = construire_graphe(lambda q: [passage], faux_llm("may terminate at any time without notice"))
    assert inventee.invoke({"question": "?"})["resultat"].raison == "citation non retrouvée mot pour mot"
    vide = construire_graphe(lambda q: [], faux_llm("x"))
    assert vide.invoke({"question": "?"})["resultat"].raison == "aucun passage trouvé"
    abstient = construire_graphe(lambda q: [passage], lambda m: '{"abstention": true}')
    assert abstient.invoke({"question": "?"})["resultat"].abstention


def test_graphe_rag_verification_nli() -> None:
    """D-022 : une réponse aux citations exactes est gardée seulement si le passage cité l'implique."""
    pytest.importorskip("langgraph")
    from cg.recherche.graphe import construire_graphe

    passage = Resultat(segment_id=7, page=3, debut=100, fin=150,
                       texte="Either party may terminate this Agreement upon 30 days notice.")
    llm = lambda m: ('{"abstention": false, "reponse": "Yes, with 30 days notice.", "citations": '
                     '[{"passage": 1, "extrait": "may terminate this Agreement upon 30 days"}]}')
    vus: list[tuple[str, list[str]]] = []

    def oui(reponse: str, textes: list[str]) -> bool:
        vus.append((reponse, textes))
        return True

    r = construire_graphe(lambda q: [passage], llm, oui).invoke({"question": "?"})["resultat"]
    assert not r.abstention
    assert vus == [("Yes, with 30 days notice.", [passage.texte])]  # seuls les passages cités sont vérifiés
    non = construire_graphe(lambda q: [passage], llm, lambda rep, t: False).invoke({"question": "?"})["resultat"]
    assert non.abstention and "NLI" in non.raison
    # Sans vérification NLI (impliquer=None), le comportement est inchangé.
    assert not construire_graphe(lambda q: [passage], llm).invoke({"question": "?"})["resultat"].abstention


def test_bm25_formule() -> None:
    """BM25 (D-024) : un mot rare pèse plus qu'un mot fréquent ; un segment long est pénalisé."""
    from collections import Counter

    from cg.recherche.bm25 import IndexBM25

    index = IndexBM25.construire({
        1: Counter({"termin": 1, "agreement": 1}),
        2: Counter({"agreement": 2}),
        3: Counter({"agreement": 1, "parti": 1}),
        4: Counter({"termin": 1, "agreement": 1, "parti": 3, "notic": 3}),
    })
    assert index.idf("termin") > index.idf("agreement")  # « termin » est dans 2 segments sur 4, « agreement » dans 4
    classement = index.classer(["termin", "agreement"], 10)
    assert classement[0][0] == 1  # même mots que le 4, mais plus court
    assert {sid for sid, _ in classement} == {1, 2, 3, 4}
    assert index.classer(["inconnu"], 10) == []


def test_graphe_rag_corpus_explicatif() -> None:
    """D-023 : un extrait explicatif exact est rendu avec son attribution ; inventé → abstention ;
    une réponse qui ne cite que l'explicatif (pas le contrat) → abstention."""
    pytest.importorskip("langgraph")
    from cg.explicatif.recherche import ResultatExplicatif
    from cg.recherche.graphe import construire_graphe

    passage = Resultat(segment_id=7, page=3, debut=100, fin=150,
                       texte="Either party may terminate this Agreement upon 30 days notice.")
    explicatif = ResultatExplicatif(
        segment_id=90, source="Termination for convenience", url="https://en.wikipedia.org/wiki/Termination_for_convenience",
        licence="CC BY-SA 4.0", attribution="Wikipedia contributors…", date_version="2025-07-13", page=None,
        section="Use", debut=200, fin=280, texte="A termination for convenience ends a contract without any breach.")
    vus: list[list[dict]] = []

    def llm(extrait_e: str, citations: str = '[{"passage": 1, "extrait": "may terminate this Agreement upon 30 days"}]'):
        def generer(messages):
            vus.append(messages)
            return ('{"abstention": false, "reponse": "Yes.", "citations": %s, '
                    '"explications": [{"document": 1, "extrait": "%s"}]}' % (citations, extrait_e))
        return generer

    graphe = construire_graphe(lambda q: [passage], llm("ends a contract without any breach"),
                               chercher_explicatif=lambda q: [explicatif])
    r = graphe.invoke({"question": "?"})["resultat"]
    assert not r.abstention and r.explications[0].licence == "CC BY-SA 4.0"
    assert r.explications[0].debut == 200 + explicatif.texte.index("ends")
    assert "[E1] (Termination for convenience)" in vus[-1][1]["content"]
    invente = construire_graphe(lambda q: [passage], llm("ends a contract at any time for free"),
                                chercher_explicatif=lambda q: [explicatif]).invoke({"question": "?"})["resultat"]
    assert invente.abstention and "explicative" in invente.raison
    sans_contrat = construire_graphe(lambda q: [passage], llm("ends a contract without any breach", "[]"),
                                     chercher_explicatif=lambda q: [explicatif]).invoke({"question": "?"})["resultat"]
    assert sans_contrat.abstention and sans_contrat.raison == "réponse sans citation"
    # Sans corpus explicatif, le prompt est inchangé (intitulé « Passages: »).
    construire_graphe(lambda q: [passage], llm("x" * 20)).invoke({"question": "?"})
    assert "\nPassages:\n" in vus[-1][1]["content"] and "Explanatory" not in vus[-1][1]["content"]
