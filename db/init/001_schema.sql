-- Schéma initial de la base de l'application ContractGuardian (D-010).
-- Exécuté automatiquement par l'image PostgreSQL à la première création du volume.
--
-- Principe (D-001, règle 1) : tout résultat pointe vers un segment, et tout segment garde sa
-- provenance : contrat, page, positions [debut, fin) dans le texte complet du contrat.
-- Les positions sont des positions de CARACTÈRES, comme en Python ; en SQL,
-- substring(texte from debut + 1 for fin - debut) redonne le texte du segment.

-- pgvector : activé dès maintenant ; la colonne de vecteurs sera ajoutée avec F5, quand le
-- modèle d'embeddings (et donc la dimension des vecteurs) sera choisi.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE contrats (
    id              BIGSERIAL PRIMARY KEY,
    titre           TEXT NOT NULL UNIQUE,
    source          TEXT NOT NULL CHECK (source IN ('cuad', 'import')),
    nom_fichier     TEXT,
    empreinte_sha256 TEXT,                    -- du fichier PDF : détecter un même fichier importé deux fois
    mode_extraction TEXT NOT NULL,            -- par exemple 'pymupdf-1.28/blocs' (D-008)
    texte_complet   TEXT NOT NULL,            -- le texte sur lequel portent toutes les positions
    nb_pages        INTEGER NOT NULL CHECK (nb_pages >= 0),
    importe_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE pages (
    contrat_id  BIGINT NOT NULL REFERENCES contrats (id) ON DELETE CASCADE,
    numero      INTEGER NOT NULL CHECK (numero >= 1),
    debut       INTEGER NOT NULL CHECK (debut >= 0),
    fin         INTEGER NOT NULL,
    PRIMARY KEY (contrat_id, numero),
    CHECK (fin >= debut)
);

CREATE TABLE segments (
    id          BIGSERIAL PRIMARY KEY,
    contrat_id  BIGINT NOT NULL REFERENCES contrats (id) ON DELETE CASCADE,
    page        INTEGER NOT NULL,
    debut       INTEGER NOT NULL CHECK (debut >= 0),
    fin         INTEGER NOT NULL,
    texte       TEXT NOT NULL,
    CHECK (fin > debut),
    UNIQUE (contrat_id, debut, fin),
    FOREIGN KEY (contrat_id, page) REFERENCES pages (contrat_id, numero) ON DELETE CASCADE
);
CREATE INDEX segments_contrat_idx ON segments (contrat_id);

-- Résultats d'analyse (clauses détectées, incohérences, réponses…) : toujours rattachés à un segment.
CREATE TABLE resultats (
    id          BIGSERIAL PRIMARY KEY,
    segment_id  BIGINT NOT NULL REFERENCES segments (id) ON DELETE CASCADE,
    tache       TEXT NOT NULL,                -- 'extraction' (F2), 'comparaison' (F3)…
    etiquette   TEXT NOT NULL,                -- par exemple la famille 'responsabilité'
    score       REAL,                         -- probabilité donnée par le modèle, si elle existe
    modele      TEXT NOT NULL,                -- quel modèle a produit le résultat (F7)
    cree_le     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX resultats_segment_idx ON resultats (segment_id);
