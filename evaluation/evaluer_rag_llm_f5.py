"""Script : comparer la réponse extractive et le RAG avec LLM (LangGraph) sur les mêmes questions (F5).

Lancement, depuis la racine du projet, avec le .venv, la base démarrée et Ollama lancé :

    PYTHONPATH=src .venv/bin/python -u evaluation/evaluer_rag_llm_f5.py --seuil-extractif S [--modele qwen3:8b]
        [--recherche hybride_bm25] [--explicatif] [--seuil-nli 0.85]

Options de la séance 2 : ``--recherche`` (D-024 ; défaut hybride BM25), ``--explicatif`` (le LLM voit
aussi 3 passages du corpus explicatif, D-023) et ``--seuil-nli`` (seuil de la vérification NLI, D-025 ;
défaut 0,85). Chaque réponse enregistrée porte sa **configuration** (modèle, recherche, corpus
explicatif) : une reprise ne mélange jamais deux configurations.

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
from cg.recherche.hybride import RECHERCHE_PAR_DEFAUT, rechercher
from cg.recherche.llm import discuter
from cg.recherche.questions_cuad import questions
from cg.recherche.verification_nli import SEUIL_NLI_RAG
from cg.stockage.connexion import connecter

RACINE = Path(__file__).resolve().parents[1]
TAILLE_ECHANTILLON = 200
# Réponses déjà obtenues (reprise après un arrêt) ; contient des extraits de contrats : jamais commité.
CHEMIN_REPRISE = RACINE / "data" / "processed" / "rag_llm_reponses.jsonl"
NB_PASSAGES = 5
NB_EXPLICATIFS = 3  # D-023 : passages explicatifs montrés au LLM (fixé avant la mesure)


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
    parseur.add_argument("--recherche", default=RECHERCHE_PAR_DEFAUT, choices=("hybride", "hybride_bm25"))
    parseur.add_argument("--explicatif", action="store_true", help="montrer aussi le corpus explicatif (D-023)")
    parseur.add_argument("--seuil-nli", type=float, default=SEUIL_NLI_RAG)
    arguments = parseur.parse_args()
    configuration = f"{arguments.modele}|{arguments.recherche}|{'explicatif' if arguments.explicatif else 'contrat seul'}"

    jeu_de = lire_splits(RACINE / "data" / "splits" / "cuad_v1_splits.json")
    with connecter() as connexion, connexion.cursor() as curseur:
        curseur.execute("SELECT titre, id FROM contrats WHERE source = 'cuad'")
        contrats = dict(curseur.fetchall())
    validation = sorted(t for t in contrats if jeu_de.get(t) == "val")
    echantillon = random.Random(0).sample(questions(contrats, validation), TAILLE_ECHANTILLON)[:arguments.taille]
    print(f"{len(echantillon)} questions (avec réponse : {sum(q['avec_reponse'] for q in echantillon)}) ; "
          f"configuration : {configuration} ; seuil NLI : {arguments.seuil_nli}", flush=True)

    deja: dict[tuple[str, str, str], dict] = {}
    if CHEMIN_REPRISE.exists():
        for ligne in CHEMIN_REPRISE.read_text(encoding="utf-8").splitlines():
            r = json.loads(ligne)
            # Réponses d'avant la séance 2 : recherche « hybride », sans corpus explicatif.
            deja[(r.get("configuration", f"{r['modele']}|hybride|contrat seul"), r["titre"], r["categorie"])] = r
    print(f"Réponses LLM déjà enregistrées (reprise) : {sum(k[0] == configuration for k in deja)}", flush=True)

    encodeur = Encodeur()
    chercher_explicatif = None
    if arguments.explicatif:
        from cg.explicatif.recherche import rechercher_explicatif
    vecteurs = {r: encodeur.encoder_requete(r) for r in {q["requete"] for q in echantillon}}
    extractif, rag, raisons, durees = [], [], Counter(), []
    with connecter() as connexion:
        for n, q in enumerate(echantillon, start=1):
            trouves = rechercher(connexion, encodeur, q["contrat_id"], q["requete"], 10, arguments.recherche,
                                 vecteurs[q["requete"]])
            rep = repondre(trouves, arguments.seuil_extractif)
            extractif.append({"avec_reponse": q["avec_reponse"], "abstention": rep.abstention,
                              "juste": (not rep.abstention) and rep.citation.segment_id in q["or"]})
            cle = (configuration, q["titre"], q["categorie"])
            if cle not in deja:
                if arguments.explicatif:
                    chercher_explicatif = (lambda _q, c=connexion, v=vecteurs[q["requete"]], r=q["requete"]:
                                           rechercher_explicatif(c, encodeur, r, NB_EXPLICATIFS, v))
                graphe = construire_graphe(lambda _q, t=trouves: t[:NB_PASSAGES],
                                           lambda m: discuter(m, arguments.modele),
                                           chercher_explicatif=chercher_explicatif)
                debut = time.perf_counter()
                r = graphe.invoke({"question": q["requete"]})["resultat"]
                deja[cle] = {"modele": arguments.modele, "configuration": configuration,
                             "titre": q["titre"], "categorie": q["categorie"],
                             "explications": [e.source for e in r.explications],
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
            r = deja[(configuration, q["titre"], q["categorie"])]
            garde = False
            if not r["abstention"] and r.get("reponse"):
                curseur.execute("SELECT texte FROM segments WHERE id = ANY(%s)", (r["segments_cites"],))
                passages = [t for (t,) in curseur.fetchall()]
                p = probas_paires(modele_nli, tokeniseur_nli, [Paire("", "f5", 0, r["reponse"], t, 0) for t in passages],
                                  appareil, 256)[:, INDICE["Entailment"]]
                garde = bool((p >= arguments.seuil_nli).any())
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
    suffixe = f"{arguments.recherche}{'-explicatif' if arguments.explicatif else ''}-{taille}"
    commun = {"recherche": arguments.recherche, "corpus_explicatif": arguments.explicatif}
    for nom, m, params in ((f"extractif-{arguments.recherche}-{taille}", m_ext,
                            {"seuil": arguments.seuil_extractif, "recherche": arguments.recherche}),
                           (f"rag-{arguments.modele}-{suffixe}", m_rag,
                            {**commun, "modele": arguments.modele, "passages": NB_PASSAGES,
                             "passages_explicatifs": NB_EXPLICATIFS if arguments.explicatif else 0, "temps_moyen_s": round(float(np.mean(durees)), 1),
                             **{"issue_" + "".join(ch if ch.isascii() and (ch.isalnum() or ch in "_-") else "_" for ch in
                                           unicodedata.normalize("NFKD", k)): v for k, v in raisons.items()}})):
        with mlflow.start_run(run_name=nom):
            mlflow.log_params({"evaluation": f"{arguments.taille} questions de validation (graine 0)", **params})
            mlflow.log_metrics({k.replace(" ", "_").replace("/", "sur").replace("(", "").replace(")", ""): v
                                for k, v in m.items()})
    with mlflow.start_run(run_name=f"rag-{arguments.modele}-verification-nli{arguments.seuil_nli}-{suffixe}"):
        mlflow.log_params({"evaluation": f"{arguments.taille} questions de validation (graine 0)",
                           "seuil_nli": arguments.seuil_nli, **commun})
        mlflow.log_metrics({k.replace(" ", "_").replace("/", "sur").replace("(", "").replace(")", ""): v for k, v in m_nli.items()})


if __name__ == "__main__":
    main()
