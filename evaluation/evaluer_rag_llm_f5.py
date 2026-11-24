"""Script : comparer la réponse extractive et le RAG avec LLM (LangGraph) sur les mêmes questions (F5).

Lancement, depuis la racine du projet, avec le .venv, la base démarrée et Ollama lancé :

    PYTHONPATH=src .venv/bin/python -u evaluation/evaluer_rag_llm_f5.py --seuil-extractif S [--modele qwen3:8b]

- Questions : **200 questions de validation** tirées avec la graine 0 (fixé avant de lancer) parmi les
  questions CUAD des 61 contrats de validation (``cg.recherche.questions_cuad``). Test fermé.
- Extractif : seuil d'abstention ``S`` réglé sur 60 contrats du train (``evaluation/evaluer_qr_f5.py``).
- RAG : graphe chercher (5 passages, recherche hybride) → générer (LLM, ``CG_LLM_MODELE`` ou
  ``--modele``) → vérifier (citations mot pour mot, sinon abstention).
- Bonne réponse : citation (extractif : le segment ; RAG : au moins un segment cité) parmi les
  segments de réponse ; question sans réponse : abstention.
"""

import argparse
import json
import unicodedata
import random
import time
from collections import Counter
from pathlib import Path

import mlflow
import numpy as np

from cg import config
from cg.datasets.splits import lire_splits
from cg.recherche.embeddings import Encodeur
from cg.recherche.extractive import repondre
from cg.recherche.graphe import construire_graphe
from cg.recherche.hybride import rechercher
from cg.recherche.llm import discuter
from cg.recherche.questions_cuad import questions
from cg.stockage.connexion import connecter

RACINE = Path(__file__).resolve().parents[1]
TAILLE_ECHANTILLON = 200
# Réponses déjà obtenues (reprise après un arrêt) ; contient des extraits de contrats : jamais commité.
CHEMIN_REPRISE = RACINE / "data" / "processed" / "rag_llm_reponses.jsonl"
NB_PASSAGES = 5


def mesures(lignes: list[dict]) -> dict[str, float]:
    """Mesures communes : exactitude, bonnes réponses, bonnes abstentions, réponses fausses.

    Args:
        lignes: Une entrée par question : ``avec_reponse``, ``abstention``, ``juste`` (citation correcte).

    Returns:
        Les mesures.
    """
    avec = [l for l in lignes if l["avec_reponse"]]
    sans = [l for l in lignes if not l["avec_reponse"]]
    repondues = [l for l in lignes if not l["abstention"]]
    bonnes = sum(l["juste"] for l in avec) + sum(l["abstention"] for l in sans)
    return {"exactitude": bonnes / len(lignes),
            "exactitude equilibree": (sum(l["juste"] for l in avec) / max(len(avec), 1)
                                      + sum(l["abstention"] for l in sans) / max(len(sans), 1)) / 2,
            "bonnes reponses (avec reponse)": sum(l["juste"] for l in avec) / max(len(avec), 1),
            "bonnes abstentions (sans reponse)": sum(l["abstention"] for l in sans) / max(len(sans), 1),
            "reponses fausses / reponses donnees": sum(not l["juste"] for l in repondues) / max(len(repondues), 1),
            "taux de reponse": len(repondues) / len(lignes)}


def main() -> None:
    """Construit l'échantillon, fait répondre les deux systèmes, compare, journalise."""
    parseur = argparse.ArgumentParser(description="Extractif contre RAG avec LLM (F5).")
    parseur.add_argument("--seuil-extractif", type=float, required=True)
    parseur.add_argument("--modele", default=config.LLM_MODELE)
    parseur.add_argument("--taille", type=int, default=TAILLE_ECHANTILLON,
                         help="N premières questions de l'échantillon (graine 0) : évaluation indicative si N < 200.")
    arguments = parseur.parse_args()

    jeu_de = lire_splits(RACINE / "data" / "splits" / "cuad_v1_splits.json")
    with connecter() as connexion, connexion.cursor() as curseur:
        curseur.execute("SELECT titre, id FROM contrats WHERE source = 'cuad'")
        contrats = dict(curseur.fetchall())
    validation = sorted(t for t in contrats if jeu_de.get(t) == "val")
    echantillon = random.Random(0).sample(questions(contrats, validation), TAILLE_ECHANTILLON)[:arguments.taille]
    print(f"{len(echantillon)} questions (avec réponse : {sum(q['avec_reponse'] for q in echantillon)}) ; "
          f"modèle : {arguments.modele}", flush=True)

    deja: dict[tuple[str, str, str], dict] = {}
    if CHEMIN_REPRISE.exists():
        for ligne in CHEMIN_REPRISE.read_text(encoding="utf-8").splitlines():
            r = json.loads(ligne)
            deja[(r["modele"], r["titre"], r["categorie"])] = r
    print(f"Réponses LLM déjà enregistrées (reprise) : {sum(k[0] == arguments.modele for k in deja)}", flush=True)

    encodeur = Encodeur()
    vecteurs = {r: encodeur.encoder_requete(r) for r in {q["requete"] for q in echantillon}}
    extractif, rag, raisons, durees = [], [], Counter(), []
    with connecter() as connexion:
        for n, q in enumerate(echantillon, start=1):
            trouves = rechercher(connexion, encodeur, q["contrat_id"], q["requete"], 10, "hybride", vecteurs[q["requete"]])
            rep = repondre(trouves, arguments.seuil_extractif)
            extractif.append({"avec_reponse": q["avec_reponse"], "abstention": rep.abstention,
                              "juste": (not rep.abstention) and rep.citation.segment_id in q["or"]})
            cle = (arguments.modele, q["titre"], q["categorie"])
            if cle not in deja:
                graphe = construire_graphe(lambda _q, t=trouves: t[:NB_PASSAGES],
                                           lambda m: discuter(m, arguments.modele))
                debut = time.perf_counter()
                r = graphe.invoke({"question": q["requete"]})["resultat"]
                deja[cle] = {"modele": arguments.modele, "titre": q["titre"], "categorie": q["categorie"],
                             "abstention": r.abstention, "raison": r.raison or "réponse vérifiée",
                             "segments_cites": [c.segment_id for c in r.citations],
                             "reponse": r.reponse,
                             "duree": time.perf_counter() - debut}
                with open(CHEMIN_REPRISE, "a", encoding="utf-8") as sortie:
                    sortie.write(json.dumps(deja[cle], ensure_ascii=False) + "\n")
            r = deja[cle]
            durees.append(r["duree"])
            raisons[r["raison"]] += 1
            rag.append({"avec_reponse": q["avec_reponse"], "abstention": r["abstention"],
                        "juste": (not r["abstention"]) and any(s in q["or"] for s in r["segments_cites"])})
            if n % 20 == 0:
                print(f"  {n} questions ({np.mean(durees):.1f} s par question en moyenne)", flush=True)

    # Piste NLI (D-017) : garder une réponse vérifiée seulement si le passage cité « implique » la phrase
    # de réponse selon le modèle de F4 (seuil 0,5 fixé d'avance) ; sinon abstention.
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from cg.extraction.transformer import choisir_appareil
    from cg.nli.modele import probas_paires
    from cg.nli.paires import INDICE, Paire
    dossier_nli = RACINE / "models" / "f4-nli-legal-bert-small"
    appareil = choisir_appareil()
    modele_nli = AutoModelForSequenceClassification.from_pretrained(dossier_nli).to(appareil)
    tokeniseur_nli = AutoTokenizer.from_pretrained(dossier_nli)
    rag_nli = []
    with connecter() as connexion, connexion.cursor() as curseur:
        for q, ligne in zip(echantillon, rag):
            r = deja[(arguments.modele, q["titre"], q["categorie"])]
            garde = False
            if not r["abstention"] and r.get("reponse"):
                curseur.execute("SELECT texte FROM segments WHERE id = ANY(%s)", (r["segments_cites"],))
                passages = [t for (t,) in curseur.fetchall()]
                p = probas_paires(modele_nli, tokeniseur_nli, [Paire("", "f5", 0, r["reponse"], t, 0) for t in passages],
                                  appareil, 256)[:, INDICE["Entailment"]]
                garde = bool((p >= 0.5).any())
            rag_nli.append({"avec_reponse": q["avec_reponse"], "abstention": not garde, "juste": garde and ligne["juste"]})
    m_ext, m_rag, m_nli = mesures(extractif), mesures(rag), mesures(rag_nli)
    print("RAG + LLM + vérification NLI :", {k: round(v, 3) for k, v in m_nli.items()})
    print("\nExtractif :", {k: round(v, 3) for k, v in m_ext.items()})
    print("RAG + LLM  :", {k: round(v, 3) for k, v in m_rag.items()})
    print("Issues du RAG :", dict(raisons))
    print(f"Temps moyen par question (RAG) : {np.mean(durees):.1f} s")

    mlflow.set_tracking_uri(f"sqlite:///{RACINE / 'mlflow.db'}")
    mlflow.set_experiment("F5-questions-reponses")
    taille = f"echantillon{arguments.taille}"
    for nom, m, params in ((f"extractif-{taille}", m_ext, {"seuil": arguments.seuil_extractif}),
                           (f"rag-{arguments.modele}-{taille}", m_rag,
                            {"modele": arguments.modele, "passages": NB_PASSAGES, "temps_moyen_s": round(float(np.mean(durees)), 1),
                             **{"issue_" + "".join(ch if ch.isascii() and (ch.isalnum() or ch in "_-") else "_" for ch in
                                           unicodedata.normalize("NFKD", k)): v for k, v in raisons.items()}})):
        with mlflow.start_run(run_name=nom):
            mlflow.log_params({"evaluation": f"{arguments.taille} questions de validation (graine 0)", **params})
            mlflow.log_metrics({k.replace(" ", "_").replace("/", "sur").replace("(", "").replace(")", ""): v
                                for k, v in m.items()})
    with mlflow.start_run(run_name=f"rag-{arguments.modele}-verification-nli-{taille}"):
        mlflow.log_params({"evaluation": f"{arguments.taille} questions de validation (graine 0)", "seuil_nli": 0.5})
        mlflow.log_metrics({k.replace(" ", "_").replace("/", "sur").replace("(", "").replace(")", ""): v for k, v in m_nli.items()})


if __name__ == "__main__":
    main()
