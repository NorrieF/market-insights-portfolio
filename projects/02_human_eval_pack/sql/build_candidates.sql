INSTALL fts;
LOAD fts;

PRAGMA create_fts_index(
  'docs',      -- input_table (qualified)
  'doc_id',         -- input_id
  'title', 'text',  -- fields to index
  overwrite = 1
);

CREATE TABLE IF NOT EXISTS candidates (
  query_id VARCHAR,
  doc_id   VARCHAR,
  rank     INTEGER,
  source   VARCHAR
);

DELETE FROM candidates;

CREATE INDEX IF NOT EXISTS idx_candidates_qid ON candidates(query_id);
CREATE INDEX IF NOT EXISTS idx_candidates_doc ON candidates(doc_id);
