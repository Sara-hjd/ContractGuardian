# Recherche par les mots : vrai BM25 contre texte intégral PostgreSQL (F5, D-024) — validation

*2026-11-26. 809 questions de **validation** avec réponse (41 questions CUAD × 61 contrats, celles qui
ont une réponse annotée). 10 premiers résultats. Rien n'est réglé (BM25 : k1 = 1,2, b = 0,75 fixés
d'avance). Test fermé. Script : `evaluation/evaluer_recherche_bm25.py` ; MLflow : `recherche-*-validation`.*

| Recherche | rappel@1 | rappel@3 | rappel@5 | rappel@10 | MRR |
|---|---|---|---|---|---|
| Mots : texte intégral PostgreSQL (`ts_rank_cd`) | 0,208 | 0,417 | 0,518 | 0,638 | 0,334 |
| **Mots : BM25** | 0,347 | 0,519 | 0,585 | 0,672 | 0,447 |
| Sens : embeddings (bge-small) | 0,313 | 0,468 | 0,543 | 0,642 | 0,411 |
| Hybride : PostgreSQL + embeddings (**actuel**) | 0,323 | 0,503 | 0,586 | 0,682 | 0,433 |
| **Hybride : BM25 + embeddings** | **0,368** | **0,532** | **0,602** | **0,696** | **0,469** |

## Comment lire ce tableau
- **rappel@k** : sur 100 questions, combien ont au moins un bon segment dans les k premiers résultats.
- **MRR** : moyenne de 1 / rang du premier bon segment (1 = toujours premier ; 0,5 = en moyenne 2e).
- Le RAG montre **5 passages** au LLM : c'est le **rappel@5** qui limite ce que le LLM peut trouver.

## Lecture
1. **BM25 seul bat nettement le texte intégral de PostgreSQL** (rappel@1 : 0,347 contre 0,208 ; MRR :
   0,447 contre 0,334), avec **exactement les mêmes mots** (lexèmes PostgreSQL) : seule la **formule**
   change. Raison : `ts_rank_cd` ne donne pas plus de poids aux mots **rares** (idf) et favorise les
   segments où les mots de la question sont proches ; BM25 pondère chaque mot par sa rareté dans le
   contrat (« indemnify » compte plus que « agreement ») et corrige la longueur du segment.
2. BM25 seul fait même **aussi bien que l'hybride actuel** au rang 5 (0,585 contre 0,586) et mieux aux
   premiers rangs.
3. **L'hybride BM25 + embeddings est le meilleur sur les cinq mesures** : +1,6 point de rappel@5,
   +4,5 points de rappel@1, +0,036 de MRR par rapport à l'hybride actuel.
4. Les écarts sont mesurés sur 809 questions de 61 contrats ; ils sont **modestes au rang 5 ou 10**,
   plus nets aux premiers rangs (ce qui compte pour l'extractif, qui ne cite qu'un segment).

## Conséquence proposée (D-024, à décider par Sara)
Remplacer le texte intégral par BM25 dans l'hybride (option a). **Attention** : changer la recherche
change les passages vus par le LLM et le seuil extractif (0,71) a été réglé avec l'hybride actuel ;
il faudrait alors refaire, sur le train, le réglage de l'extractif et la collecte de D-025 avant la
mesure finale sur la validation.
