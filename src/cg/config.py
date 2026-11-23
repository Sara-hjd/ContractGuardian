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
LLM_MODELE: str = parametre("CG_LLM_MODELE", "qwen3-vl:8b")
LLM_URL: str = parametre("CG_LLM_URL", "http://127.0.0.1:11434")
