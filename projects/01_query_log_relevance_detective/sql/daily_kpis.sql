WITH per_query_day AS (
  SELECT
    DATE_TRUNC('day', se.ts) AS day,
    COUNT(*) AS queries,
    AVG(qcf.has_click) AS ctr,
    AVG(qcf.rr) AS mrr
  FROM search_events_sess se
  JOIN query_click_features qcf ON se.event_id = qcf.event_id
  WHERE se.query_norm IS NOT NULL AND length(trim(se.query_norm)) > 0
  GROUP BY 1
),
per_session_day AS (
  SELECT
    DATE_TRUNC('day', MIN(se.ts)) AS day,
    COUNT(*) AS sessions,
    AVG(sm.no_click_session) AS no_click_rate,
    AVG(sm.possible_reformulation) AS possible_reformulation_rate
  FROM search_events_sess se
  JOIN session_metrics sm ON se.session_id = sm.session_id
  GROUP BY sm.session_id
)
SELECT
  q.day,
  q.queries,
  q.ctr,
  q.mrr,
  s.no_click_rate,
  s.possible_reformulation_rate
FROM per_query_day q
LEFT JOIN (
  SELECT
    day,
    AVG(no_click_rate) AS no_click_rate,
    AVG(possible_reformulation_rate) AS possible_reformulation_rate
  FROM per_session_day
  GROUP BY day
) s USING (day)
ORDER BY q.day;
