"""Métriques de F4 : étiquette du document (3 classes) et évidences citées.

Place dans le projet : mêmes familles de mesures que l'article de ContractNLI, simplifiées :
- **étiquette** : exactitude et F1 de chaque classe, macro-F1 sur les trois classes (ici
  l'exactitude a un sens : les classes ne sont pas écrasées par une classe à 97 %) ;
- **évidences** : précision, rappel et F1 des phrases citées, sur les couples (document, hypothèse)
  dont l'étiquette vraie est « implique » ou « contredit ».
"""

import numpy as np

from cg.extraction.metriques import metriques_binaires
from cg.nli.paires import ETIQUETTES


def metriques_etiquettes(vraies: list[str], predites: list[str]) -> dict[str, float]:
    """Exactitude, F1 par classe et macro-F1 sur les trois classes.

    Args:
        vraies: Étiquettes vraies (une par couple document × hypothèse).
        predites: Étiquettes prédites, même ordre.

    Returns:
        ``exactitude``, ``f1_<classe>`` pour chaque classe et ``macro_f1``.
    """
    v, p = np.array(vraies), np.array(predites)
    resultat = {"exactitude": float((v == p).mean())}
    f1s = []
    for classe in ETIQUETTES:
        f1 = metriques_binaires(v == classe, p == classe)["f1"]
        resultat[f"f1_{classe}"] = f1
        f1s.append(f1)
    resultat["macro_f1"] = float(np.mean(f1s))
    return resultat


def metriques_evidences(vraies: list[set[int]], citees: list[set[int]]) -> dict[str, float]:
    """Précision, rappel et F1 des évidences (comptés sur l'ensemble des phrases).

    Args:
        vraies: Pour chaque couple dont l'étiquette vraie n'est pas « NotMentioned », les indices
            des phrases d'évidence.
        citees: Les indices cités par le système pour ces mêmes couples.

    Returns:
        ``precision``, ``rappel``, ``f1``.
    """
    vp = sum(len(v & c) for v, c in zip(vraies, citees))
    nb_cites = sum(len(c) for c in citees)
    nb_vrais = sum(len(v) for v in vraies)
    precision = vp / nb_cites if nb_cites else 0.0
    rappel = vp / nb_vrais if nb_vrais else 0.0
    f1 = 2 * precision * rappel / (precision + rappel) if precision + rappel else 0.0
    return {"precision": precision, "rappel": rappel, "f1": f1}
