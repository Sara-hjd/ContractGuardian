"""Configuration de ContractGuardian : paramètres modifiables sans toucher au code.

Place dans le projet : un seul endroit pour les choix qui peuvent changer (par exemple le LLM local,
D-016). Chaque paramètre a une valeur par défaut et peut être remplacé par une variable
d'environnement (ou par une ligne du fichier ``.env``, lu par ``cg.stockage.connexion``).
"""

import os
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]


def parametre(nom: str, defaut: str) -> str:
    """Valeur d'un paramètre : variable d'environnement, sinon ``.env``, sinon la valeur par défaut.

    Args:
        nom: Nom du paramètre (par exemple ``"CG_LLM_MODELE"``).
        defaut: Valeur utilisée si le paramètre n'est défini nulle part.

    Returns:
        La valeur du paramètre.
    """
    if nom in os.environ:
        return os.environ[nom]
    return _fichier_env().get(nom, defaut)


def _fichier_env() -> dict[str, str]:
    """Lit toutes les lignes ``CLE=valeur`` du fichier ``.env`` (s'il existe)."""
    chemin = RACINE / ".env"
    if not chemin.exists():
        return {}
    resultat = {}
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            cle, valeur = ligne.split("=", 1)
            resultat[cle.strip()] = valeur.strip()
    return resultat


# LLM local (D-016) : changer de modèle = changer cette valeur (ou CG_LLM_MODELE), pas le code.
LLM_MODELE: str = parametre("CG_LLM_MODELE", "qwen3-vl:8b-instruct")  # D-022
LLM_URL: str = parametre("CG_LLM_URL", "http://127.0.0.1:11434")
# Longueur maximale de la sortie du LLM (tokens). qwen3-vl:8b réfléchit toujours (variante « thinking »,
# le réglage think=false est ignoré) : il lui faut de la place pour réfléchir PUIS répondre.
LLM_NUM_PREDICT: int = int(parametre("CG_LLM_NUM_PREDICT", "4096"))
# Échantillonnage recommandé par Qwen pour ses modèles « thinking » : en décodage glouton (température 0),
# qwen3-vl:8b réfléchit en boucle sans jamais répondre (constaté le 2026-11-24). Graine fixe : reproductible.
LLM_TEMPERATURE: float = float(parametre("CG_LLM_TEMPERATURE", "0.6"))
LLM_TOP_P: float = float(parametre("CG_LLM_TOP_P", "0.95"))
LLM_TOP_K: int = int(parametre("CG_LLM_TOP_K", "20"))
