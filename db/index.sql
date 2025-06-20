DROP INDEX IF EXISTS sentence_embed_hnsw_cos;

CREATE INDEX sentence_embed_hnsw_cos ON Sentence USING hnsw (embedding vector_cosine_ops)
WITH
    (m = 16, ef_construction = 64);

DROP INDEX IF EXISTS related_text_embed_hnsw_cos;

CREATE INDEX related_text_embed_hnsw_cos ON Related_text USING hnsw (embedding vector_cosine_ops)
WITH
    (m = 16, ef_construction = 128);

CREATE INDEX entity_embed_hnsw_cos ON Entity USING hnsw (embedding vector_cosine_ops)
WITH
    (m = 16, ef_construction = 128);