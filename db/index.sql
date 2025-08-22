CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_embed_hnsw_cos
ON related_text USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);

CREATE INDEX CONCURRENTLY IF NOT EXISTS sentence_embed_hnsw_cos
ON sentence USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_source_id_btree_nonnull
ON related_text (source_id)
WHERE embedding IS NOT NULL;


CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_group_parts_idx_rx
ON related_text (
  (split_part(related_id,'_',1)),
  (split_part(related_id,'_',2)),
  (split_part(related_id,'_',3)),
  (split_part(related_id,'_',4)),
  (split_part(related_id,'_',5)),
  ((split_part(related_id,'_',6))::int)
)
INCLUDE (related_id, details)
WHERE related_id ~ '^[0-9]+(_[0-9]+){5}$';

CREATE INDEX CONCURRENTLY IF NOT EXISTS relationship_rtid_sid_secid_idx
ON relationship (related_text_id, sentence_id, section_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS sentence_sid_secid_btree
ON sentence (sentence_id, section_id);

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS related_text_source_source_id_pk
ON related_text_source (source_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS related_text_related_id_btree
ON related_text (related_id);

ANALYZE related_text;
ANALYZE relationship;
ANALYZE sentence;
ANALYZE related_text_source;
