-- DuckDB FTS-based candidate generation (BM25)
INSTALL fts;
LOAD fts;

-- Create/overwrite an FTS index on docs(title, text), keyed by doc_id
PRAGMA create_fts_index('docs', 'doc_id', 'title', 'text');

-- Rebuild candidates cleanly
DELETE FROM candidates;

-- For each query, score every doc with BM25 and keep top 10
INSERT INTO candidates (query_id, doc_id, rank, source)
SELECT query_id, doc_id, rank, 'bm25'
FROM (
  SELECT
    q.query_id,
    d.doc_id,
    fts_main_docs.match_bm25(d.doc_id, q.text) AS score,
    row_number() OVER (
      PARTITION BY q.query_id
      ORDER BY score DESC
    ) AS rank
  FROM queries q
  CROSS JOIN docs d
)
WHERE score IS NOT NULL
QUALIFY rank <= 10;
