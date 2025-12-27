CREATE OR REPLACE VIEW query_click_features AS
SELECT
  se.event_id,
  MIN(ce.rank) AS best_click_rank,
  CASE WHEN COUNT(ce.doc_id) > 0 THEN 1 ELSE 0 END AS has_click,
  CASE WHEN COUNT(ce.doc_id) > 0
    THEN 1.0 / CASE WHEN MIN(ce.rank) = 0 THEN 1 ELSE MIN(ce.rank) END
    ELSE NULL
  END AS rr
FROM search_events se
LEFT JOIN click_events ce
  ON se.event_id = ce.event_id
GROUP BY se.event_id;
