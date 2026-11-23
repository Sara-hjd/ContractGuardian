# `src/cg/nli/` — inférence en langage naturel (F4)

Rôle : pour un contrat et une **hypothèse** (par exemple « Receiving Party shall not reverse
engineer… »), dire si le contrat l'**implique** (*Entailment*), la **contredit** (*Contradiction*)
ou **n'en parle pas** (*NotMentioned*), en **citant les phrases d'évidence** (positions exactes).
Données : ContractNLI (D-002), train et dev ; test fermé.

## Fichiers

| Fichier | Contenu |
|---|---|
| `paires.py` | Paires (hypothèse, phrase) ; échantillonnage d'entraînement (évidences + 2 neutres, dont une « difficile ») ; paires d'un document pour la prédiction. |
| `modele.py` | Entraînement à 3 classes (entropie croisée), probabilités des paires, `decider` : agrégation au niveau du document (seuil de confiance → sinon *NotMentioned*, abstention) et évidences citées. |
| `evaluation.py` | Exactitude, F1 par classe, macro-F1 ; précision / rappel / F1 des évidences. |

Entraînement et évaluation : `training/nli_contractnli.py` (D-014).

## Règles

- L'unité est la **phrase de ContractNLI** : chaque évidence citée a des positions exactes dans
  le texte du contrat (règle 1).
- *NotMentioned* joue le rôle d'**abstention** : sans phrase suffisamment probante, on n'affirme rien.
- Les seuils sont réglés sur le **dev** ; le test de ContractNLI n'est ouvert qu'avec une décision écrite.
