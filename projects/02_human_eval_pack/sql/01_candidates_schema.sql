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
