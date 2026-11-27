"""Script : mesurer la fidélité des réponses du RAG et préparer l'annotation humaine (F5, D-026).

Lancement (après ``evaluer_rag_llm_f5.py`` sur les 200 questions de validation) :

    PYTHONPATH=src .venv/bin/python -u evaluation/mesurer_fidelite_f5.py --configuration "qwen3-vl:8b-instruct|hybride_bm25|explicatif"

Pour chaque réponse **vérifiée mot pour mot** de la configuration :
1. **éléments critiques** (niveau 2) : chaque nombre, durée, montant ou mois de la réponse est-il dans
   les passages cités ? (``cg.recherche.fidelite``) ;
2. **score NLI** (niveau 3, indicatif seulement : le même modèle filtre déjà les réponses).
Les résultats sont donnés séparément pour les réponses **gardées** et **rejetées** par la vérification NLI.

Niveau 1 (référence humaine) : le script tire **50 réponses** vérifiées (graine 0) et écrit
- ``data/annotations/f5_fidelite/reponses_v1.csv`` : **identifiants seulement** (commité, règle 5) ;
- ``data/processed/f5_fidelite_a_lire.md`` : question, réponse et passages cités (local, **jamais commité**).
Le tirage n'est fait qu'une fois (le fichier existant n'est pas remplacé). Après l'annotation : kappa avec
``python -m cg.annotation.accord … --grille f5``, puis référence de consensus (``reference.csv``).
"""

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np

from cg.recherche.fidelite import controler
from cg.recherche.verification_nli import SEUIL_NLI_RAG
from cg.stockage.connexion import connecter

RACINE = Path(__file__).resolve().parents[1]
REPONSES = RACINE / "data" / "processed" / "rag_llm_reponses.jsonl"
DOSSIER_ANNOTATIONS = RACINE / "data" / "annotations" / "f5_fidelite"
A_LIRE = RACINE / "data" / "processed" / "f5_fidelite_a_lire.md"
TAILLE_ANNOTATION = 50


def main() -> None:
    """Contrôles automatiques sur toutes les réponses vérifiées ; tirage de l'échantillon à annoter."""
    parseur = argparse.ArgumentParser(description="Fidélité des réponses du RAG (D-026).")
    parseur.add_argument("--configuration", required=True)
    parseur.add_argument("--seuil-nli", type=float, default=SEUIL_NLI_RAG)
    arguments = parseur.parse_args()
    lignes = [json.loads(l) for l in REPONSES.read_text(encoding="utf-8").splitlines()]
    reponses = [r for r in lignes if r.get("configuration") == arguments.configuration and not r["abstention"]]
    print(f"{len(reponses)} réponses vérifiées mot pour mot ({arguments.configuration})")

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from cg.extraction.transformer import choisir_appareil
    from cg.nli.modele import probas_paires
    from cg.nli.paires import INDICE, Paire
    dossier_nli = RACINE / "models" / "f4-nli-legal-bert-small"
    appareil = choisir_appareil()
    modele_nli = AutoModelForSequenceClassification.from_pretrained(dossier_nli).to(appareil)
    tokeniseur_nli = AutoTokenizer.from_pretrained(dossier_nli)

    resultats = []
    with connecter() as connexion, connexion.cursor() as c:
        for r in reponses:
            c.execute("SELECT texte, page FROM segments WHERE id = ANY(%s) ORDER BY id", (r["segments_cites"],))
            passages = c.fetchall()
            textes = [t for t, _ in passages]
            p = 0.0
            if r.get("reponse", "").strip() and textes:
                p = float(probas_paires(modele_nli, tokeniseur_nli, [Paire("", "f5", 0, r["reponse"], t, 0) for t in textes],
                                        appareil, 256)[:, INDICE["Entailment"]].max())
            controle = controler(r.get("reponse", ""), textes)
            resultats.append({**r, "passages": passages, "p_nli": p, "garde_nli": p >= arguments.seuil_nli,
                              "elements": sorted(controle.elements), "absents": sorted(controle.absents)})

    for nom, groupe in (("toutes les réponses vérifiées", resultats),
                        (f"gardées par le NLI (≥ {arguments.seuil_nli})", [x for x in resultats if x["garde_nli"]]),
                        ("rejetées par le NLI", [x for x in resultats if not x["garde_nli"]])):
        if not groupe:
            continue
        avec_elements = [x for x in groupe if x["elements"]]
        print(f"\n{nom} : {len(groupe)}")
        print(f"  avec au moins un élément critique : {len(avec_elements)}")
        if avec_elements:
            print(f"  dont TOUS les éléments sont dans les passages cités : "
                  f"{np.mean([not x['absents'] for x in avec_elements]):.3f}")
        print(f"  score NLI moyen (indicatif) : {np.mean([x['p_nli'] for x in groupe]):.3f}")
    douteuses = [x for x in resultats if x["absents"]]
    print(f"\nRéponses avec un élément critique absent des passages : {len(douteuses)}")

    # Niveau 1 : échantillon pour l'annotation humaine (tiré une seule fois).
    DOSSIER_ANNOTATIONS.mkdir(parents=True, exist_ok=True)
    references = DOSSIER_ANNOTATIONS / "reponses_v1.csv"
    if references.exists():
        print(f"\nÉchantillon déjà tiré : {references.relative_to(RACINE)} (non remplacé).")
        return
    echantillon = random.Random(0).sample(resultats, min(TAILLE_ANNOTATION, len(resultats)))
    with open(references, "w", encoding="utf-8", newline="") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(["id_reponse", "configuration", "titre", "categorie", "segments_cites"])
        for i, x in enumerate(echantillon, start=1):
            ecrivain.writerow([f"R{i:02d}", x["configuration"], x["titre"], x["categorie"],
                               "|".join(str(s) for s in x["segments_cites"])])
    modele = DOSSIER_ANNOTATIONS / "MODELE_annotations.csv"
    if not modele.exists():
        modele.write_text("id_reponse,annotateur,etiquette,date\n", encoding="utf-8")
    morceaux = ["# Fidélité des réponses du RAG — à lire pour annoter (D-026)\n",
                "*Fichier local, JAMAIS commité (contient du texte de contrats). Guide : "
                "`docs/annotation/GUIDE_F5_FIDELITE.md`.*\n"]
    for i, x in enumerate(echantillon, start=1):
        morceaux.append(f"\n---\n\n## R{i:02d}\n\n**Catégorie CUAD** : {x['categorie']}\n\n"
                        f"**Réponse du système** : {x.get('reponse', '')}\n\n**Passages cités** :\n")
        for texte, page in x["passages"]:
            morceaux.append(f"\n> (page {page}) " + " ".join(texte.split()) + "\n")
    A_LIRE.write_text("".join(morceaux), encoding="utf-8")
    print(f"\nÉchantillon : {len(echantillon)} réponses → {references.relative_to(RACINE)} ; texte : {A_LIRE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
