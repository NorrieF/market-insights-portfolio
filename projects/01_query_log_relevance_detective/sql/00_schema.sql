-- Project 1 ETL schema (AOL-IA)

CREATE TABLE IF NOT EXISTS search_events (
  event_id   BIGINT,
  user_id    VARCHAR,
  query_id   VARCHAR,
  query_norm VARCHAR,
  query_orig VARCHAR,
  ts         TIMESTAMP
);

CREATE TABLE IF NOT EXISTS click_events (
  event_id BIGINT,
  user_id  VARCHAR,
  query_id VARCHAR,
  doc_id   VARCHAR,
  rank     INTEGER
);

-- Optional indexes to speed up later analysis
CREATE INDEX IF NOT EXISTS idx_search_user_ts ON search_events(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_click_event   ON click_events(event_id);
