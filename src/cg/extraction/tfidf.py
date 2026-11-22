"""Baseline 2 : TF-IDF + régression logistique, un classifieur oui / non par famille.

Place dans le projet : première baseline apprise de F2 (multi-étiquette : un segment peut
appartenir à plusieurs familles). Elle est rapide, tourne sur un ordinateur portable (règle 4)
et reste lisible : on peut afficher les mots qui pèsent le plus pour chaque famille.

Le déséquilibre (environ 97 % de segments « aucune famille ») est compensé par
``class_weight="balanced"`` : une erreur sur un segment positif, rare, coûte plus cher.
"""

import numpy as np
from scipy.sparse import spmatrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def creer_vectoriseur(ngram_max: int, min_df: int = 2) -> TfidfVectorizer:
    """Crée le vectoriseur TF-IDF.

    Args:
        ngram_max: 1 = mots seuls ; 2 = mots et paires de mots consécutifs (« in no », « no event »).
        min_df: Un mot doit apparaître dans au moins ``min_df`` segments du train pour être
            gardé (écarte les fautes de conversion et les mots uniques).

    Returns:
        Un ``TfidfVectorizer`` non entraîné.
    """
    return TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, ngram_max),
        min_df=min_df,
        # log(1 + fréquence) : un mot répété 10 fois ne pèse pas 10 fois plus.
        sublinear_tf=True,
    )


def entrainer_classifieur(X: spmatrix, y: np.ndarray, C: float, graine: int = 0) -> LogisticRegression:
    """Entraîne une régression logistique pondérée pour une famille.

    Args:
        X: Matrice TF-IDF des segments d'entraînement.
        y: Étiquettes oui / non de la famille.
        C: Inverse de la force de régularisation : petit C = modèle plus prudent, qui
            s'appuie sur moins de mots ; grand C = modèle qui colle davantage au train.
        graine: Graine pour un résultat reproductible.

    Returns:
        Le classifieur entraîné.
    """
    classifieur = LogisticRegression(
        C=C, class_weight="balanced", max_iter=2000, solver="liblinear", random_state=graine
    )
    classifieur.fit(X, y)
    return classifieur


def mots_les_plus_lourds(
    vectoriseur: TfidfVectorizer, classifieur: LogisticRegression, n: int = 15
) -> list[tuple[str, float]]:
    """Les mots (ou paires de mots) qui poussent le plus vers « oui » pour une famille.

    Args:
        vectoriseur: Le vectoriseur entraîné.
        classifieur: Le classifieur entraîné de la famille.
        n: Nombre de mots à renvoyer.

    Returns:
        Les ``n`` couples (mot, poids) de plus grand poids positif, du plus lourd au moins lourd.
    """
    vocabulaire = vectoriseur.get_feature_names_out()
    poids = classifieur.coef_[0]
    ordre = np.argsort(poids)[::-1][:n]
    return [(str(vocabulaire[i]), round(float(poids[i]), 2)) for i in ordre]
