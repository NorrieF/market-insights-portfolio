CREATE OR REPLACE VIEW session_metrics AS
WITH q AS (
  SELECT
    session_id,
    COUNT(*) AS n_queries,
    COUNT(DISTINCT query_norm) AS n_distinct_queries
  FROM search_events_sess
  GROUP BY session_id
),
c AS (
  SELECT
    se.session_id,
    MAX(qcf.has_click) AS has_click_any
  FROM search_events_sess se
  JOIN query_click_features qcf ON se.event_id = qcf.event_id
  GROUP BY se.session_id
)
SELECT
  q.session_id,
  q.n_queries,
  q.n_distinct_queries,
  CASE WHEN c.has_click_any = 1 THEN 0 ELSE 1 END AS no_click_session,
  CASE WHEN q.n_distinct_queries > 1 THEN 1 ELSE 0 END AS possible_reformulation
FROM q
JOIN c USING (session_id);
