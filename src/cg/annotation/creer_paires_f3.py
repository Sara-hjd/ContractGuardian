"""Script : créer les paires de clauses candidates de F3, à annoter par Sara et Ilyas.

Lancement, depuis la racine du projet, avec le .venv :

    PYTHONPATH=src .venv/bin/python -m cg.annotation.creer_paires_f3

Une paire = deux segments **d'un même contrat** qui pourraient être en tension (quatre types).
Les segments viennent des contrats de **validation** (test fermé), étiquetés par les annotations
CUAD alignées sur le texte PDF (D-007, D-008) ; le choix ne dépend donc d'aucun modèle.

Échantillonnage fixé avant le tirage : 12 paires par type (48 au total), au plus 2 paires par
contrat et par type, graine 0 ; si un type a moins de 12 paires, on les garde toutes.

Sorties :
- ``data/annotations/f3_paires/paires_v1.csv`` : **références seulement** (contrat, page, positions,
  catégories CUAD), versionné (D-003) ;
- ``data/processed/f3_paires_a_lire.md`` : le **texte** des deux clauses, pour lire et annoter
  (contient du texte de contrat : **jamais commité**).
"""

import csv
import itertools
import random
from pathlib import Path

from cg.datasets.segments import charger_segments

RACINE = Path(__file__).resolve().parents[3]
CHEMIN_SEGMENTS = RACINE / "data" / "processed" / "cuad_pdf_segments_fusion0.jsonl"
CHEMIN_PAIRES = RACINE / "data" / "annotations" / "f3_paires" / "paires_v1.csv"
CHEMIN_LECTURE = RACINE / "data" / "processed" / "f3_paires_a_lire.md"
PAR_TYPE, PAR_CONTRAT, GRAINE = 12, 2, 0

TYPES: dict[str, tuple[set[str], set[str], str]] = {
    "T1": ({"Expiration Date"}, {"Renewal Term", "Notice Period To Terminate Renewal"},
           "durée : fin du contrat ↔ renouvellement ou préavis de non-renouvellement"),
    "T2": ({"Expiration Date", "Renewal Term"}, {"Termination For Convenience"},
           "durée ↔ résiliation sans motif"),
    "T3": ({"Cap On Liability"}, {"Uncapped Liability"},
           "plafond de responsabilité ↔ responsabilité non plafonnée"),
    "T4": ({"Termination For Convenience"}, {"Post-Termination Services"},
           "résiliation sans motif ↔ obligations après la fin du contrat"),
}
COLONNES = ["id_paire", "type", "titre", "page_a", "debut_a", "fin_a", "categories_a",
            "page_b", "debut_b", "fin_b", "categories_b"]


def main() -> None:
    """Énumère les paires possibles, tire l'échantillon, écrit les références et le fichier de lecture."""
    val = charger_segments(CHEMIN_SEGMENTS, {"val"})
    val = val[val["categories"].map(len) > 0]
    hasard = random.Random(GRAINE)
    choisies: list[dict] = []
    for code, (cats_a, cats_b, _) in TYPES.items():
        candidates: dict[str, list] = {}
        for titre, g in sorted(val.groupby("titre"), key=lambda x: x[0]):
            for a, b in itertools.permutations(list(g.itertuples()), 2):
                if set(a.categories) & cats_a and set(b.categories) & cats_b and (a.debut, a.fin) != (b.debut, b.fin):
                    candidates.setdefault(titre, []).append((a, b))
        retenues = []
        for titre in sorted(candidates):
            retenues += [(titre, p) for p in hasard.sample(candidates[titre], min(PAR_CONTRAT, len(candidates[titre])))]
        retenues = hasard.sample(retenues, min(PAR_TYPE, len(retenues)))
        for titre, (a, b) in sorted(retenues, key=lambda x: (x[0], x[1][0].debut)):
            choisies.append({"type": code, "titre": titre, "a": a, "b": b})

    CHEMIN_PAIRES.parent.mkdir(parents=True, exist_ok=True)
    with open(CHEMIN_PAIRES, "w", encoding="utf-8", newline="") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(COLONNES)
        for i, p in enumerate(choisies, start=1):
            a, b = p["a"], p["b"]
            ecrivain.writerow([f"P{i:02d}", p["type"], p["titre"], a.page, a.debut, a.fin, "|".join(a.categories),
                               b.page, b.debut, b.fin, "|".join(b.categories)])
    with open(CHEMIN_LECTURE, "w", encoding="utf-8") as f:
        f.write("# Paires F3 à lire (texte de contrats : NE PAS COMMITER, NE PAS COPIER dans les annotations)\n\n")
        for i, p in enumerate(choisies, start=1):
            a, b = p["a"], p["b"]
            f.write(f"## P{i:02d} — {p['type']} ({TYPES[p['type']][2]})\n\nContrat : {p['titre']}\n\n"
                    f"**Clause A** (page {a.page}, positions {a.debut}–{a.fin}, CUAD : {', '.join(a.categories)}) :\n\n"
                    f"> {' '.join(a.texte.split())}\n\n"
                    f"**Clause B** (page {b.page}, positions {b.debut}–{b.fin}, CUAD : {', '.join(b.categories)}) :\n\n"
                    f"> {' '.join(b.texte.split())}\n\n---\n\n")
    compte = {c: sum(p["type"] == c for p in choisies) for c in TYPES}
    print(f"{len(choisies)} paires ({compte}) ; contrats : {len({p['titre'] for p in choisies})}")
    print(f"Références : {CHEMIN_PAIRES.relative_to(RACINE)} ; lecture (non commité) : {CHEMIN_LECTURE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
