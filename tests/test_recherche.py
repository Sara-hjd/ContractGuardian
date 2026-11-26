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
