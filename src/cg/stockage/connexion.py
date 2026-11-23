"""Connexion à la base PostgreSQL de l'application (D-010).

Place dans le projet : point d'entrée unique vers la base. Les identifiants viennent des variables
d'environnement ou, à défaut, du fichier ``.env`` à la racine du projet (jamais commité).
"""

import os
from pathlib import Path

import psycopg

RACINE = Path(__file__).resolve().parents[3]
CLES: tuple[str, ...] = (
    "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST", "POSTGRES_PORT",
)


def lire_configuration(chemin_env: Path = RACINE / ".env") -> dict[str, str]:
    """Lit la configuration de connexion.

    Les variables d'environnement l'emportent sur le fichier ``.env`` (utile pour les tests ou
    une autre machine).

    Args:
        chemin_env: Fichier ``CLE=valeur`` ; les lignes vides et les commentaires (#) sont ignorés.

    Returns:
        Un dictionnaire avec les clés de ``CLES`` trouvées.
    """
    configuration: dict[str, str] = {}
    if chemin_env.exists():
        for ligne in chemin_env.read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            configuration[cle.strip()] = valeur.strip()
    for cle in CLES:
        if cle in os.environ:
            configuration[cle] = os.environ[cle]
    return configuration


def connecter(configuration: dict[str, str] | None = None) -> psycopg.Connection:
    """Ouvre une connexion à la base.

    Args:
        configuration: Configuration à utiliser ; par défaut, ``lire_configuration()``.

    Returns:
        Une connexion psycopg (à fermer, idéalement avec ``with``).

    Raises:
        KeyError: Si une clé indispensable manque (copier ``.env.example`` en ``.env``).
        psycopg.OperationalError: Si la base ne répond pas (lancer ``docker compose up -d``).
    """
    c = configuration if configuration is not None else lire_configuration()
    return psycopg.connect(
        host=c.get("POSTGRES_HOST", "127.0.0.1"),
        port=int(c.get("POSTGRES_PORT", "5432")),
        user=c["POSTGRES_USER"],
        password=c["POSTGRES_PASSWORD"],
        dbname=c["POSTGRES_DB"],
        connect_timeout=5,
    )
