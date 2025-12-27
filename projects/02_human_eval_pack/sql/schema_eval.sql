CREATE TABLE IF NOT EXISTS candidates (
  query_id VARCHAR,
  doc_id   VARCHAR,
  rank     INTEGER,
  source   VARCHAR
);

CREATE TABLE IF NOT EXISTS ollama_scores (
  query_id     VARCHAR,
  doc_id       VARCHAR,
  model        VARCHAR,
  score_0_3    INTEGER,
  rationale    VARCHAR,
  prompt_hash  VARCHAR,
  judged_at    TIMESTAMP
);

-- Helpful indexes (DuckDB supports CREATE INDEX)
CREATE INDEX IF NOT EXISTS idx_candidates_qid ON candidates(query_id);
CREATE INDEX IF NOT EXISTS idx_candidates_doc ON candidates(doc_id);
CREATE INDEX IF NOT EXISTS idx_ollama_qid ON ollama_scores(query_id);
CREATE INDEX IF NOT EXISTS idx_ollama_doc ON ollama_scores(doc_id);