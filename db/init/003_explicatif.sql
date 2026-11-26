-- Corpus documentaire explicatif (F5, D-023) : indexé SÉPARÉMENT des contrats.
-- Exécuté automatiquement à la création d'un nouveau volume ; sur une base existante, il s'applique
-- avec psql (idempotent : « IF NOT EXISTS »). Voir src/cg/explicatif/README.md.
-- Les sources sont des documents publics sous licence ouverte ; leur texte n'est jamais commité.

-- Une ligne par source : références, licence et attribution à afficher (obligatoire en CC BY-SA).
CREATE TABLE IF NOT EXISTS sources_explicatives (
    id            SERIAL PRIMARY KEY,
    cle           TEXT NOT NULL UNIQUE,          -- identifiant stable (cg.explicatif.sources)
    titre         TEXT NOT NULL,
    url           TEXT NOT NULL,                 -- page citée à l'utilisateur
    url_version   TEXT,                          -- version exacte (révision Wikipédia), si elle existe
    editeur       TEXT NOT NULL,
    licence       TEXT NOT NULL,
    attribution   TEXT NOT NULL,
    date_version  TEXT,                          -- date de la version téléchargée
    consulte_le   DATE NOT NULL,
    sha256        TEXT NOT NULL,                 -- empreinte du fichier téléchargé
    texte_complet TEXT NOT NULL
);

-- Une ligne par passage, avec sa provenance (règle 1) : positions, page (PDF) et section.
CREATE TABLE IF NOT EXISTS segments_explicatifs (
    id        SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources_explicatives(id) ON DELETE CASCADE,
    debut     INTEGER NOT NULL,
    fin       INTEGER NOT NULL,
    texte     TEXT NOT NULL,
    page      INTEGER,                           -- NULL pour une page web
    section   TEXT,
    tsv       tsvector GENERATED ALWAYS AS (to_tsvector('english', texte)) STORED,
    embedding vector(384),
    CHECK (debut >= 0 AND fin > debut)
);
CREATE INDEX IF NOT EXISTS segments_explicatifs_source_idx ON segments_explicatifs (source_id);
CREATE INDEX IF NOT EXISTS segments_explicatifs_tsv_idx ON segments_explicatifs USING GIN (tsv);
CREATE INDEX IF NOT EXISTS segments_explicatifs_embedding_idx
    ON segments_explicatifs USING hnsw (embedding vector_cosine_ops);
