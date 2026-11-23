"""Questions de CUAD posées aux contrats de la base, avec leurs segments de réponse (F5).

Place dans le projet : jeu d'évaluation commun à la réponse extractive et au RAG avec LLM, pour
qu'ils soient comparés sur **exactement** les mêmes questions.

La requête est « <catégorie>. <description> » (la formule « Highlight the parts… » est retirée).
Une question **avec réponse** a des segments de réponse : annotations CUAD alignées sur le texte PDF
du contrat (D-007), projetées avec la règle de chevauchement habituelle. Une question **sans
réponse** (``is_impossible``) attend une abstention.
"""

import json
import re
from pathlib import Path

from cg.datasets.cuad import SEUIL_CHEVAUCHEMENT, chevauchement
from cg.ingestion.alignement import aligner, normaliser
from cg.stockage.connexion import connecter

RACINE = Path(__file__).resolve().parents[3]
CHEMIN_CUAD = RACINE / "data" / "raw" / "cuad" / "CUAD_v1" / "CUAD_v1.json"
_MOTIF = re.compile(r'related to "(?P<categorie>[^"]+)".*?Details:\s*(?P<details>.*)', re.S)


def requete(question_cuad: str) -> str:
    """Transforme une question CUAD en requête « catégorie. description ».

    Args:
        question_cuad: Question d'origine (« Highlight the parts (if any) of this contract related to … »).

    Returns:
        La requête courte.
    """
    m = _MOTIF.search(question_cuad)
    return f"{m['categorie']}. {m['details'].strip()}" if m else question_cuad


def questions(contrats: dict[str, int], titres: list[str]) -> list[dict]:
    """Questions des contrats demandés, avec les segments de réponse (alignés sur le texte PDF).

    Args:
        contrats: Titre -> identifiant du contrat dans la base.
        titres: Contrats à interroger.

    Returns:
        Une entrée par (contrat, catégorie) : requête, avec ou sans réponse, ids des segments de réponse.
    """
    with open(CHEMIN_CUAD, encoding="utf-8") as f:
        cuad = {c["title"]: c["paragraphs"][0] for c in json.load(f)["data"]}
    resultat = []
    with connecter() as connexion, connexion.cursor() as curseur:
        for titre in titres:
            cid = contrats[titre]
            curseur.execute("SELECT texte_complet FROM contrats WHERE id = %s", (cid,))
            cible = normaliser(curseur.fetchone()[0], "etendue")
            curseur.execute("SELECT id, debut, fin FROM segments WHERE contrat_id = %s", (cid,))
            segments = curseur.fetchall()
            contexte = cuad[titre]["context"]
            for qa in cuad[titre]["qas"]:
                categorie = qa["id"].rsplit("__", 1)[1]
                if qa["is_impossible"]:
                    resultat.append({"titre": titre, "contrat_id": cid, "categorie": categorie,
                                     "requete": requete(qa["question"]), "avec_reponse": False, "or": set()})
                    continue
                ids: set[int] = set()
                for r in qa["answers"]:
                    position = aligner(r["text"], cible, "etendue", r["answer_start"] / len(contexte))
                    if position is None:
                        continue  # D-007 : passage non retrouvé, exclu
                    d, fn = position
                    seuil = min(SEUIL_CHEVAUCHEMENT, fn - d)
                    ids |= {int(s) for s, sd, sf in segments if chevauchement(sd, sf, d, fn) >= seuil}
                if ids:  # question gardée seulement si au moins une réponse est retrouvée
                    resultat.append({"titre": titre, "contrat_id": cid, "categorie": categorie,
                                     "requete": requete(qa["question"]), "avec_reponse": True, "or": ids})
    return resultat
