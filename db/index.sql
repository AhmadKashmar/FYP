CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_embed_hnsw_cos
ON Related_text USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);

CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_source_id_btree
ON Related_text (source_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS sentence_embed_hnsw_cos
ON Sentence USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_abcde_expr_idx ON Related_text
(
  (split_part(related_id,'_',1)),
  (split_part(related_id,'_',2)),
  (split_part(related_id,'_',3)),
  (split_part(related_id,'_',4)),
  (split_part(related_id,'_',5))
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_f_expr_idx ON Related_text
((CAST(split_part(related_id,'_',6) AS int)));

CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_abcde_expr_idx_rx ON Related_text
(
  (split_part(related_id,'_',1)),
  (split_part(related_id,'_',2)),
  (split_part(related_id,'_',3)),
  (split_part(related_id,'_',4)),
  (split_part(related_id,'_',5))
)
WHERE related_id ~ '^[0-9]+(_[0-9]+){5}$';

CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_f_expr_idx_rx ON Related_text
((CAST(split_part(related_id,'_',6) AS int)))
WHERE related_id ~ '^[0-9]+(_[0-9]+){5}$';

CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_related_id_btree
ON Related_text (related_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS relationship_rtid_sid_secid_idx
ON relationship (related_text_id, sentence_id, section_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS sentence_sid_secid_btree
ON Sentence (sentence_id, section_id);

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS related_text_source_source_id_pk
ON Related_text_source (source_id);

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_related_id_trgm
ON Related_text USING GIN (related_id gin_trgm_ops);

ANALYZE Related_text;
ANALYZE relationship;
ANALYZE Sentence;
ANALYZE Related_text_source;
