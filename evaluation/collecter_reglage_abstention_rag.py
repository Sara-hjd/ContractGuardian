"""Script : collecter les réponses du RAG sur les questions de réglage du train (F5, D-025, étape 1).

Lancement, depuis la racine du projet, avec le .venv, la base et Ollama démarrés :

    PYTHONPATH=src .venv/bin/python -u evaluation/collecter_reglage_abstention_rag.py [--recherche hybride_bm25]

Ce script **ne choisit aucun seuil** : il enregistre, pour chacune des 200 questions de réglage, la
réponse du RAG (vérification mot pour mot seulement), si elle est juste, et la probabilité « implique »
du modèle NLI de F4 (maximum sur les passages cités). Le seuil sera choisi ensuite, avec le critère de
D-025 accepté par Sara (``evaluation/regler_seuil_abstention_rag.py``).

Questions : celles des **60 contrats du train** de ``evaluer_qr_f5.py`` (graine 0), dont 200 sont
tirées avec la graine 0. Ni la validation ni le test ne sont utilisés ici.
Sortie (reprenable, jamais commitée) : ``data/processed/rag_reglage_train.jsonl`` (recherche hybride
actuelle) ou ``data/processed/rag_reglage_train_<recherche>.jsonl`` (autre recherche, D-024).
"""

import argparse
import json
import random
import time
from pathlib import Path

from cg import config
from cg.datasets.splits import lire_splits
from cg.recherche.embeddings import Encodeur
from cg.recherche.graphe import construire_graphe
from cg.recherche.hybride import rechercher
from cg.recherche.llm import discuter
from cg.recherche.questions_cuad import questions
from cg.stockage.connexion import connecter

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "processed" / "rag_reglage_train.jsonl"
TAILLE = 200
NB_PASSAGES = 5


def questions_reglage(contrats: dict[str, int]) -> list[dict]:
    """Les 200 questions de réglage : 60 contrats du train (graine 0), puis 200 questions (graine 0).

    Args:
        contrats: Titre -> identifiant du contrat dans la base.

    Returns:
        Les questions, dans un ordre reproductible.
    """
    jeu_de = lire_splits(RACINE / "data" / "splits" / "cuad_v1_splits.json")
    train = sorted(t for t in contrats if jeu_de.get(t) == "train")
    reglage = random.Random(0).sample(train, 60)  # mêmes 60 contrats que evaluer_qr_f5.py
    assert all(jeu_de[t] == "train" for t in reglage)
    return random.Random(0).sample(questions(contrats, reglage), TAILLE)


def main() -> None:
    """Interroge le RAG sur les questions de réglage et enregistre réponses, justesse et probabilité NLI."""
    parseur = argparse.ArgumentParser(description="Collecte des réponses du RAG sur le train (D-025).")
    parseur.add_argument("--recherche", default="hybride", choices=("hybride", "hybride_bm25"))
    recherche = parseur.parse_args().recherche
    sortie = SORTIE if recherche == "hybride" else SORTIE.with_name(f"rag_reglage_train_{recherche}.jsonl")
    with connecter() as connexion, connexion.cursor() as curseur:
        curseur.execute("SELECT titre, id FROM contrats WHERE source = 'cuad'")
        contrats = dict(curseur.fetchall())
    echantillon = questions_reglage(contrats)
    print(f"{len(echantillon)} questions de réglage (train) ; avec réponse : "
          f"{sum(q['avec_reponse'] for q in echantillon)} ; modèle : {config.LLM_MODELE}", flush=True)

    deja = set()
    if sortie.exists():
        deja = {(r["titre"], r["categorie"]) for r in map(json.loads, sortie.read_text(encoding="utf-8").splitlines())}
    print(f"Déjà collectées (reprise) : {len(deja)}", flush=True)

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from cg.extraction.transformer import choisir_appareil
    from cg.nli.modele import probas_paires
    from cg.nli.paires import INDICE, Paire
    dossier_nli = RACINE / "models" / "f4-nli-legal-bert-small"
    appareil = choisir_appareil()
    modele_nli = AutoModelForSequenceClassification.from_pretrained(dossier_nli).to(appareil)
    tokeniseur_nli = AutoTokenizer.from_pretrained(dossier_nli)

    encodeur = Encodeur()
    with connecter() as connexion:
        for n, q in enumerate(echantillon, start=1):
            if (q["titre"], q["categorie"]) in deja:
                continue
            trouves = rechercher(connexion, encodeur, q["contrat_id"], q["requete"], 10, recherche)
            graphe = construire_graphe(lambda _q, t=trouves: t[:NB_PASSAGES], discuter)  # sans NLI
            debut = time.perf_counter()
            r = graphe.invoke({"question": q["requete"]})["resultat"]
            duree = time.perf_counter() - debut
            cites = [c.segment_id for c in r.citations]
            p_nli = None
            if not r.abstention:
                textes = [p.texte for p in trouves[:NB_PASSAGES] if p.segment_id in set(cites)]
                if r.reponse.strip() and textes:
                    probas = probas_paires(modele_nli, tokeniseur_nli,
                                           [Paire("", "f5", 0, r.reponse, t, 0) for t in textes], appareil, 256)
                    p_nli = float(probas[:, INDICE["Entailment"]].max())
                else:
                    p_nli = 0.0  # réponse vide : non vérifiable
            ligne = {"modele": config.LLM_MODELE, "recherche": recherche, "titre": q["titre"], "categorie": q["categorie"],
                     "avec_reponse": q["avec_reponse"], "abstention": r.abstention,
                     "raison": r.raison or "réponse vérifiée", "segments_cites": cites,
                     "juste": (not r.abstention) and any(s in q["or"] for s in cites),
                     "p_nli": p_nli, "duree": duree}
            with open(sortie, "a", encoding="utf-8") as f:
                f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
            if n % 20 == 0:
                print(f"  {n} questions", flush=True)
    print("Collecte terminée (aucun seuil choisi).", flush=True)


if __name__ == "__main__":
    main()
