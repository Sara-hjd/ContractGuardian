# Questions-réponses (F5) — recherche hybride et réponse extractive, validation

*2026-11-23. Embeddings `BAAI/bge-small-en-v1.5` (D-015) ; base PostgreSQL + pgvector (D-010).
Scripts : `evaluation/evaluer_qr_f5.py`, `evaluation/evaluer_rag_llm_f5.py`. Test fermé.*

## Jeu d'évaluation

- Les **41 questions de CUAD** (une par catégorie), posées à chaque contrat ; requête =
  « catégorie. description ».
- **Réglage** : 60 contrats du **train** (graine 0) → 2 449 questions. **Mesure** : les 61 contrats
  de **validation** → 2 492 questions, dont **809 avec réponse** (segments de réponse = annotations
  CUAD alignées sur le texte PDF, D-007) et 1 683 **sans réponse** (il faut s'abstenir).

## Recherche (validation, 809 questions avec réponse)

| Recherche | rappel@1 | rappel@5 | rappel@10 |
|---|---|---|---|
| Par les mots (texte intégral PostgreSQL) | 0,208 | 0,518 | 0,638 |
| Par le sens (bge-small + pgvector) | 0,313 | 0,543 | 0,642 |
| **Hybride (fusion RRF)** | **0,323** | **0,586** | **0,682** |

La fusion fait mieux que chacune des deux recherches : elles se complètent.

## Réponse extractive avec abstention (validation)

| Réglage du seuil (sur le train) | Exactitude | **Exactitude équilibrée** | Bonnes réponses | Bonnes abstentions | Réponses fausses / données | Taux de réponse |
|---|---|---|---|---|---|---|
| Exactitude (seuil 0,76) | 0,676 | 0,507 | 0,025 | 0,989 | 0,623 | 2,1 % |
| **Exactitude équilibrée (seuil 0,71)** | 0,661 | **0,521** | 0,120 | 0,922 | 0,688 | 12,5 % |
| Référence : toujours s'abstenir | 0,675 | 0,500 | 0 | 1 | — | 0 % |
| Référence : jamais s'abstenir | 0,105 | 0,161 | 0,323 | 0 | 0,895 | 100 % |

## Lecture

1. **L'exactitude simple est un mauvais critère ici** : 2/3 des questions n'ont pas de réponse, et
   « toujours s'abstenir » obtient déjà 0,675. Le premier réglage (sur l'exactitude) a donc
   presque toujours abstenu. **Erreur de méthode de Claude**, visible avant tout calcul ; corrigée
   en réglant sur l'**exactitude équilibrée** (0,5 pour « toujours s'abstenir »), *après* avoir vu ce
   résultat (à faire valider : D-017).
2. **La similarité cosinus ne suffit pas pour décider s'il faut répondre** : même bien réglée,
   l'extraction ne dépasse « toujours s'abstenir » que de 2 points, et 69 % de ses réponses sont
   fausses. C'est précisément ce que le LLM doit améliorer en **lisant** les passages.
3. Une bonne réponse exige ici de citer **un** segment annoté par CUAD parmi ~200 : mesure stricte
   (un segment voisin, pertinent mais non annoté, compte comme faux).

## RAG + LLM local (LangGraph) — évaluation complète reportée

- Graphe en place (chercher → générer → vérifier mot pour mot → répondre ou s'abstenir), testé
  avec un faux LLM et essayé avec `qwen3-vl:8b` (réponse citée et vérifiée ; abstention correcte).
- L'évaluation sur 200 questions de validation (graine 0) a échoué 3 fois : chargement du modèle
  sous forte charge mémoire, puis **mise en veille du Mac** pendant le calcul (journal système :
  *Sleep / Deep Idle* jusqu'au réveil par l'utilisatrice). Script désormais **reprenable**.
- **À faire (séance 5/5)** : relancer Mac ouvert et branché (`caffeinate -i` ne suffit pas écran fermé).
