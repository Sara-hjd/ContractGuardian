"""Client minimal du LLM local (Ollama) pour la réponse générative de F5 (D-016).

Place dans le projet : le LLM tourne **sur le Mac**, via le serveur local d'Ollama
(``http://127.0.0.1:11434``) ; aucun service payant, aucune donnée envoyée à l'extérieur (règle 4).
Le nom du modèle vient de la configuration (``cg.config.LLM_MODELE``, variable ``CG_LLM_MODELE``).

Réglages (``cg.config``) : graine fixe (même question → même réponse), échantillonnage recommandé par
Qwen pour les modèles « thinking » (température 0,6, top_p 0,95, top_k 20 ; à température 0 le modèle
réfléchit en boucle), mode « réflexion » demandé désactivé,
réponse demandée en JSON, longueur bornée par ``config.LLM_NUM_PREDICT`` (un JSON tronqué conduit à
une abstention). **Attention** : ``qwen3-vl:8b`` (variante « thinking ») réfléchit toujours, même avec
``think: false`` (constaté le 2026-11-24) ; sa réflexion consomme une partie de cette longueur.
"""

import json
import time
import urllib.error
import urllib.request

from cg import config


def discuter(
    messages: list[dict[str, str]], modele: str | None = None, delai: float = 300.0, essais: int = 3
) -> str:
    """Envoie une conversation au LLM local et renvoie le texte de sa réponse.

    Args:
        messages: Liste de messages ``{"role": "system" | "user", "content": …}``.
        modele: Nom du modèle Ollama ; par défaut ``config.LLM_MODELE``.
        delai: Temps maximal d'attente, en secondes.
        essais: Nombre de tentatives si le serveur répond par une erreur (par exemple un modèle qui
            n'a pas fini de se charger en mémoire) ; pause de 15 s entre deux tentatives.

    Returns:
        Le contenu de la réponse (une chaîne, ici du JSON).

    Raises:
        urllib.error.URLError: Si le serveur Ollama ne répond pas (lancer l'application Ollama).
    """
    corps = json.dumps({
        "model": modele or config.LLM_MODELE,
        "messages": messages,
        "stream": False,
        "format": "json",
        "think": False,
        "options": {"temperature": config.LLM_TEMPERATURE, "top_p": config.LLM_TOP_P, "top_k": config.LLM_TOP_K,
                    "num_ctx": 8192, "seed": 0, "num_predict": config.LLM_NUM_PREDICT},
    }).encode("utf-8")
    requete = urllib.request.Request(f"{config.LLM_URL}/api/chat", data=corps,
                                     headers={"Content-Type": "application/json"})
    for essai in range(1, essais + 1):
        try:
            with urllib.request.urlopen(requete, timeout=delai) as reponse:
                return json.loads(reponse.read())["message"]["content"]
        except urllib.error.HTTPError:
            if essai == essais:
                raise
            time.sleep(15)
    raise RuntimeError("inaccessible")  # jamais atteint : la boucle renvoie ou relève l'erreur
