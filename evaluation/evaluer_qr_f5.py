"""Script : évaluer la recherche hybride et la réponse extractive avec abstention (F5).

Lancement, depuis la racine du projet, avec le .venv et la base démarrée (vecteurs calculés) :

    PYTHONPATH=src .venv/bin/python -u evaluation/evaluer_qr_f5.py

Questions : les 41 questions de CUAD (une par catégorie), posées à chaque contrat. La requête est
« <catégorie>. <description> » (la formule « Highlight the parts… » est retirée). Bonne réponse :
- question **avec réponse** : le segment cité fait partie des segments de réponse (annotations CUAD
  alignées sur le texte PDF, D-007 ; règle de chevauchement habituelle) ;
- question **sans réponse** (``is_impossible``) : le système **s'abstient**.

Protocole (fixé avant de lancer) :
- le seuil d'abstention est **réglé sur 60 contrats du train** (tirés avec la graine 0), pour
  maximiser l'exactitude (bonne réponse ou bonne abstention) ;
- les mesures sont rapportées sur les **61 contrats de validation** ; le test reste fermé.
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd

from cg.datasets.splits import lire_splits
from cg.recherche.embeddings import Encodeur
from cg.recherche.extractive import repondre
from cg.recherche.hybride import rechercher
from cg.recherche.questions_cuad import questions
from cg.stockage.connexion import connecter

RACINE = Path(__file__).resolve().parents[1]
SEUILS = np.round(np.arange(0.30, 0.951, 0.01), 2)
MODES = ("mots", "sens", "hybride")
K = (1, 5, 10)


def main() -> None:
    """Construit les questions, mesure la recherche, règle l'abstention sur le train, évalue sur la validation."""
    jeu_de = lire_splits(RACINE / "data" / "splits" / "cuad_v1_splits.json")
    with connecter() as connexion, connexion.cursor() as curseur:
        curseur.execute("SELECT titre, id FROM contrats WHERE source = 'cuad'")
        contrats = dict(curseur.fetchall())
    train = sorted(t for t in contrats if jeu_de.get(t) == "train")
    reglage = random.Random(0).sample(train, 60)
    validation = sorted(t for t in contrats if jeu_de.get(t) == "val")
    q_reglage, q_val = questions(contrats, reglage), questions(contrats, validation)
    print(f"Questions : réglage {len(q_reglage)} (60 contrats du train), validation {len(q_val)} (61 contrats) ; "
          f"avec réponse en validation : {sum(q['avec_reponse'] for q in q_val)}")

    encodeur = Encodeur()
    vecteurs = {r: encodeur.encoder_requete(r) for r in {q["requete"] for q in q_reglage + q_val}}
    resultats: dict[tuple[str, int], dict[str, list]] = {}
    with connecter() as connexion:
        for nom, qs in (("reglage", q_reglage), ("val", q_val)):
            for i, q in enumerate(qs):
                resultats[(nom, i)] = {m: rechercher(connexion, encodeur, q["contrat_id"], q["requete"], 10, m,
                                                     vecteurs[q["requete"]]) for m in MODES}

    # 1. Recherche : rappel@k sur les questions avec réponse (validation).
    lignes = []
    for m in MODES:
        ligne = {"recherche": m}
        avec = [i for i, q in enumerate(q_val) if q["avec_reponse"]]
        for k in K:
            ligne[f"rappel@{k}"] = round(float(np.mean(
                [any(r.segment_id in q_val[i]["or"] for r in resultats[("val", i)][m][:k]) for i in avec])), 3)
        lignes.append(ligne)
    print("\nRecherche (validation, questions avec réponse) :")
    print(pd.DataFrame(lignes).to_string(index=False))

    # 2. Réponse extractive avec abstention (recherche hybride).
    def mesurer(nom: str, qs: list[dict], seuil: float) -> dict[str, float]:
        bonnes = repondu = fausses = abst_ok = sans = avec_ok = avec = 0
        for i, q in enumerate(qs):
            rep = repondre(resultats[(nom, i)]["hybride"], seuil)
            if q["avec_reponse"]:
                avec += 1
                juste = (not rep.abstention) and rep.citation.segment_id in q["or"]
                avec_ok += juste
                bonnes += juste
            else:
                sans += 1
                abst_ok += rep.abstention
                bonnes += rep.abstention
            if not rep.abstention:
                repondu += 1
                fausses += not (q["avec_reponse"] and rep.citation.segment_id in q["or"])
        return {"exactitude": bonnes / len(qs),
                "exactitude équilibrée": (avec_ok / max(avec, 1) + abst_ok / max(sans, 1)) / 2,
                "bonnes réponses (avec réponse)": avec_ok / max(avec, 1),
                "bonnes abstentions (sans réponse)": abst_ok / max(sans, 1),
                "réponses fausses / réponses données": fausses / max(repondu, 1), "taux de réponse": repondu / len(qs)}

    # Critère de réglage : l'exactitude simple récompense l'abstention systématique (2/3 des questions
    # n'ont pas de réponse) ; l'exactitude équilibrée (moyenne bonnes réponses / bonnes abstentions)
    # vaut 0,5 pour un système qui s'abstient toujours. Les deux sont montrés (D-017).
    seuils = {critere: float(max(SEUILS, key=lambda s, c=critere: mesurer("reglage", q_reglage, float(s))[c]))
              for critere in ("exactitude", "exactitude équilibrée")}
    for critere, seuil in seuils.items():
        print(f"\nSeuil réglé sur les 60 contrats du train (critère : {critere}) : similarité ≥ {seuil}")
        print("Validation :", {k: round(v, 3) for k, v in mesurer("val", q_val, seuil).items()})
    print("\nRéférences (validation) :")
    print("  jamais d'abstention :", {k: round(v, 3) for k, v in mesurer("val", q_val, -1.0).items()})
    print("  toujours s'abstenir :", {k: round(v, 3) for k, v in mesurer("val", q_val, 2.0).items()})


if __name__ == "__main__":
    main()
