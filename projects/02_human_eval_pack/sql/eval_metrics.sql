CREATE OR REPLACE VIEW relevant AS
SELECT query_id, doc_id
FROM qrels
WHERE relevance > 0;

-- For each query, find:
-- - how many relevant docs exist (n_rel)
-- - how many were retrieved in top K (n_rel_retrieved)
-- - first relevant rank (best_rank)
CREATE OR REPLACE VIEW eval_base AS
WITH rel AS (
  SELECT query_id, COUNT(*) AS n_rel
  FROM relevant
  GROUP BY query_id
),
hits AS (
  SELECT
    c.query_id,
    COUNT(*) AS n_rel_retrieved,
    MIN(c.rank) AS best_rank
  FROM candidates c
  JOIN relevant r
    ON c.query_id = r.query_id
   AND c.doc_id   = r.doc_id
  WHERE c.rank <= 10
  GROUP BY c.query_id
)
SELECT
  rel.query_id,
  rel.n_rel,
  COALESCE(hits.n_rel_retrieved, 0) AS n_rel_retrieved,
  hits.best_rank
FROM rel
LEFT JOIN hits USING (query_id);

-- Per-query metrics
CREATE OR REPLACE TABLE eval_per_query AS
SELECT
  query_id,
  n_rel,
  n_rel_retrieved,
  CASE
    WHEN n_rel = 0 THEN NULL
    ELSE CAST(n_rel_retrieved AS DOUBLE) / n_rel
  END AS recall_at_10,
  CASE
    WHEN best_rank IS NULL THEN 0.0
    ELSE 1.0 / best_rank
  END AS mrr_at_10
FROM eval_base
ORDER BY CAST(query_id AS INTEGER);

-- Overall summary
CREATE OR REPLACE TABLE eval_summary AS
SELECT
  AVG(recall_at_10) AS avg_recall_at_10,
  AVG(mrr_at_10)    AS avg_mrr_at_10,
  COUNT(*)          AS n_queries
FROM eval_per_query;