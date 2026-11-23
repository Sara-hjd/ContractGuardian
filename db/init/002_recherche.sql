-- Recherche hybride (F5, D-015) : texte intégral + vecteurs, sur la table segments.
-- Exécuté automatiquement à la création d'un nouveau volume ; sur une base existante, il s'applique
-- avec psql (idempotent : « IF NOT EXISTS »). Voir src/cg/recherche/README.md.

-- Recherche par mots : vecteur de mots (tsvector) calculé automatiquement par PostgreSQL à partir
-- du texte (racinisation anglaise : « terminated » et « termination » se rapprochent).
ALTER TABLE segments
    ADD COLUMN IF NOT EXISTS tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', texte)) STORED;
CREATE INDEX IF NOT EXISTS segments_tsv_idx ON segments USING GIN (tsv);

-- Recherche par sens : vecteur de 384 nombres produit par le modèle d'embeddings (D-015).
ALTER TABLE segments ADD COLUMN IF NOT EXISTS embedding vector(384);
-- Index HNSW : retrouve vite les vecteurs les plus proches (distance cosinus).
CREATE INDEX IF NOT EXISTS segments_embedding_idx ON segments USING hnsw (embedding vector_cosine_ops);
