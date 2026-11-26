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

La fusion fait mieux que chacune des deux recherches : elles se complètent. **Recall@5** (métrique
du cahier des charges) : **0,586** en hybride, contre 0,518 (mots) et 0,543 (sens).

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

## RAG + LLM local (LangGraph)

- Graphe en place (chercher → générer → vérifier mot pour mot → répondre ou s'abstenir), testé
  avec un faux LLM et essayé avec `qwen3-vl:8b` (réponse citée et vérifiée ; abstention correcte).
- L'évaluation sur 200 questions de validation (graine 0) a échoué 3 fois : chargement du modèle
  sous forte charge mémoire, puis **mise en veille du Mac** pendant le calcul (journal système :
  *Sleep / Deep Idle* jusqu'au réveil par l'utilisatrice). Script désormais **reprenable**.
- **À faire (séance 5/5)** : relancer Mac ouvert et branché (`caffeinate -i` ne suffit pas écran fermé).

## Évaluation INDICATIVE du RAG + LLM (2026-11-24, 20 questions)

*`qwen3-vl:8b` (variante « thinking » : réflexion obligatoire ; réglages recommandés par Qwen :
température 0,6, top_p 0,95, top_k 20, graine 0 ; D-016). 20 premières questions de l'échantillon
de validation (graine 0) : 7 avec réponse, 13 sans réponse. **Trop peu de questions pour conclure** :
la mesure de référence (200 questions, `qwen3-vl:8b-instruct`) reste à faire.*

| Système | Exactitude équilibrée | Bonnes réponses (sur 7) | Bonnes abstentions (sur 13) | Réponses fausses / données |
|---|---|---|---|---|
| Extractif (seuil 0,71) | 0,423 | 0 | 11 | 2 sur 2 |
| **RAG + LLM** | **0,643** | **2** | **13** | **0 sur 2** |
| RAG + LLM + vérification NLI (piste D-017) | 0,643 | 2 | 13 | 0 sur 2 |

- Issues du RAG : 2 réponses vérifiées, 12 abstentions du LLM, 5 sorties illisibles (JSON invalide),
  1 citation non retrouvée mot pour mot (abstention). Temps moyen : **82 s par question**.
- **Lecture** : sur ces 20 questions, le LLM **ne s'est jamais trompé** quand il a répondu, et s'est
  abstenu à chaque question sans réponse ; mais il ne trouve que 2 réponses sur 7, et 1 sortie sur 4
  est inutilisable. La **vérification NLI** n'a rien changé ici (les 2 réponses vérifiées sont
  « impliquées » par leur passage) : trop peu de cas pour juger.

## Évaluation de RÉFÉRENCE du RAG + LLM (2026-11-26, 200 questions)

*`qwen3-vl:8b-instruct` (Ollama `70e58e37beb1`, Apache 2.0) : variante **sans réflexion** (vérifié :
aucun champ `thinking`). Réglages inchangés (température 0,6, top_p 0,95, top_k 20, graine 0, 5 passages).
Les 200 questions de validation (graine 0) : **70 avec réponse, 130 sans réponse**. Extractif au seuil
0,71 (D-017). MLflow : `rag-qwen3-vl:8b-instruct-echantillon200` et `…-verification-nli-echantillon200`.*

| Système | Exactitude équilibrée | Bonnes réponses (sur 70) | Bonnes abstentions (sur 130) | Réponses fausses / données |
|---|---|---|---|---|
| Extractif (seuil 0,71) | 0,477 | 6 | 113 | 24 sur 30 (0,80) |
| RAG + LLM | 0,529 | **31** | 80 | 71 sur 102 (0,70) |
| **RAG + LLM + vérification NLI** (piste D-017) | **0,561** | 22 | **105** | 35 sur 57 (0,61) |

- **Vitesse** : **8,1 s par question** (contre 82 s avec `qwen3-vl:8b`), soit 27 min pour 200 questions.
- **Issues du RAG** (200) : 102 réponses vérifiées ; 61 abstentions du LLM ; 17 citations mal formées ;
  14 citations non retrouvées mot pour mot ; 5 réponses sans citation ; 1 passage inexistant.
  Les sorties inutilisables tombent à **8,5 %** (25 % avec le modèle « thinking »).
- **Mêmes 20 premières questions** que l'évaluation indicative : instruct **0,742** (5 sur 7 ; 10 sur 13)
  contre 0,643 pour `qwen3-vl:8b` (2 sur 7 ; 13 sur 13). Sur 200 questions, le chiffre tombe à 0,529 :
  **20 questions ne suffisaient pas** pour conclure (c'est pourquoi elles étaient « indicatives »).

### Analyse des 71 réponses comptées fausses (RAG + LLM)

- **50** portent sur des questions **sans réponse annotée** dans CUAD : le LLM a cité un passage alors
  que l'annotation est vide. Catégories les plus fréquentes : Third Party Beneficiary (5), Price
  Restrictions (4), Insurance (4), Exclusivity (3), Competitive Restriction Exception (3), Effective
  Date (3). **Limite de la mesure** : les annotations CUAD ne sont pas exhaustives et la question
  posée est générique ; une partie de ces citations peut être une lecture **défendable** d'un passage
  voisin du sujet. La mesure reste stricte : sans segment annoté cité, c'est faux.
- **21** portent sur des questions **avec réponse** mais citent un autre segment : 4 sont à 2 segments
  ou moins d'un segment annoté, 5 sont sur la même page.

### Lecture

1. Le modèle instruct **trouve 4 à 5 fois plus de réponses** que l'extractif (31 contre 6 sur 70) et
   est **10 fois plus rapide** que le modèle « thinking » : il devient utilisable dans l'application.
2. **Mais il s'abstient trop peu** : 50 réponses sur 130 questions sans réponse. Pour un outil qui doit
   « citer ou s'abstenir », c'est le point faible principal.
3. La **vérification NLI** (garder une réponse seulement si le passage cité l'« implique » selon F4,
   seuil 0,5 fixé d'avance) est **la meilleure variante** : +25 bonnes abstentions, −36 réponses
   fausses, au prix de 9 bonnes réponses. Elle reste **insuffisante** : 61 % des réponses données ne
   citent pas le segment annoté.
4. Toutes ces mesures sont sur la **validation** (réglage autorisé) ; le test reste fermé.
5. Pistes, **avant le gel** (séance 2, 🔒) : seuil d'abstention par **courbe couverture / erreur**,
   mesure de la **fidélité**, Recall@3 et MRR. Les choix proposés sont dans **D-022** (en attente de Sara).
