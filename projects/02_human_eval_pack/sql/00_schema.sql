CREATE TABLE IF NOT EXISTS docs (
  doc_id VARCHAR,
  title  VARCHAR,
  text   VARCHAR
);

CREATE TABLE IF NOT EXISTS queries (
  query_id VARCHAR,
  text     VARCHAR
);

CREATE TABLE IF NOT EXISTS qrels (
  query_id  VARCHAR,
  doc_id    VARCHAR,
  relevance INTEGER,
  iteration VARCHAR
);

-- Optional: helpful indexes
CREATE INDEX IF NOT EXISTS idx_docs_doc_id     ON docs(doc_id);
CREATE INDEX IF NOT EXISTS idx_queries_query_id ON queries(query_id);
CREATE INDEX IF NOT EXISTS idx_qrels_query_id   ON qrels(query_id);
CREATE INDEX IF NOT EXISTS idx_qrels_doc_id     ON qrels(doc_id);