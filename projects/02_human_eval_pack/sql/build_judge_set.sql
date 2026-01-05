-- Build judge_set = (all positive qrels) + (BM25 fill) up to TOPK per query.
-- Placeholder: {{TOPK}} is replaced by the python script.

CREATE TABLE IF NOT EXISTS judge_set (
  query_id VARCHAR,
  doc_id   VARCHAR,
  slot     INTEGER,
  source   VARCHAR
);

DELETE FROM judge_set;

WITH
-- 1) All positive qrels (these are the "known positives")
pos AS (
  SELECT
    query_id,
    doc_id,
    row_number() OVER (
      PARTITION BY query_id
      ORDER BY doc_id
    ) AS slot
  FROM qrels
  WHERE relevance > 0
),

-- 2) Count positives per query (include queries with 0 positives too)
pos_counts AS (
  SELECT
    q.query_id,
    COALESCE(p.n_pos, 0) AS n_pos
  FROM queries q
  LEFT JOIN (
    SELECT query_id, COUNT(*) AS n_pos
    FROM pos
    GROUP BY query_id
  ) p USING (query_id)
),

-- 3) BM25 fill = candidates excluding positives for that query
fill AS (
  SELECT
    c.query_id,
    c.doc_id,
    row_number() OVER (
      PARTITION BY c.query_id
      ORDER BY c.rank, c.doc_id
    ) AS fill_rn,
    pc.n_pos
  FROM candidates c
  JOIN pos_counts pc
    ON pc.query_id = c.query_id
  LEFT JOIN pos p
    ON p.query_id = c.query_id
   AND p.doc_id   = c.doc_id
  WHERE p.doc_id IS NULL
),

fill_limited AS (
  SELECT
    query_id,
    doc_id,
    (n_pos + fill_rn) AS slot
  FROM fill
  WHERE fill_rn <= ({{TOPK}} - n_pos)
)

INSERT INTO judge_set(query_id, doc_id, slot, source)
SELECT query_id, doc_id, slot, 'qrels_pos'
FROM pos

UNION ALL

SELECT query_id, doc_id, slot, 'bm25_fill'
FROM fill_limited;
