CREATE TABLE IF NOT EXISTS ollama_picks (
  query_id VARCHAR,
  slot     INTEGER,
  model    VARCHAR,
  prompt_v VARCHAR,
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ollama_picks_qid ON ollama_picks(query_id);
