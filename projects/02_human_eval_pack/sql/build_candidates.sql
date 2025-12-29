INSTALL fts;
LOAD fts;

-- Always rebuild the index (FTS indexes do not auto-update when data changes).
PRAGMA create_fts_index(
  'docs', 'doc_id', 'title', 'text',
  overwrite = 1
);

DELETE FROM candidates;

WITH scored AS (
  SELECT
    q.query_id,
    d.doc_id,
    fts_main_docs.match_bm25(d.doc_id, q.text) AS score
  FROM queries q
  CROSS JOIN docs d
),
filtered AS (
  SELECT * FROM scored WHERE score IS NOT NULL
),
ranked AS (
  SELECT
    query_id,
    doc_id,
    row_number() OVER (PARTITION BY query_id ORDER BY score DESC) AS rank
  FROM filtered
)
INSERT INTO candidates(query_id, doc_id, rank, source)
SELECT query_id, doc_id, rank, 'bm25'
FROM ranked
WHERE rank <= 10;
