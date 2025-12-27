WITH per_query AS (
  SELECT
    se.query_norm,
    COUNT(*) AS q_count,
    AVG(qcf.has_click) AS ctr,
    AVG(qcf.rr) AS mrr
  FROM search_events_sess se
  JOIN query_click_features qcf ON se.event_id = qcf.event_id
  WHERE se.query_norm IS NOT NULL AND length(trim(se.query_norm)) > 0
  GROUP BY se.query_norm
)
SELECT *
FROM per_query
WHERE q_count >= 20;
