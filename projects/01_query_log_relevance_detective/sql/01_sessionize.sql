CREATE OR REPLACE TABLE search_events_sess AS
WITH base AS (
  SELECT
    event_id,
    user_id,
    query_id,
    query_norm,
    query_orig,
    ts,
    LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) AS prev_ts
  FROM search_events
),
flags AS (
  SELECT
    *,
    CASE
      WHEN prev_ts IS NULL THEN 1
      WHEN ts - prev_ts > INTERVAL '30 minutes' THEN 1
      ELSE 0
    END AS new_sess
  FROM base
),
numbered AS (
  SELECT
    *,
    SUM(new_sess) OVER (
      PARTITION BY user_id ORDER BY ts
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS sess_num
  FROM flags
)
SELECT
  event_id,
  user_id,
  query_id,
  query_norm,
  query_orig,
  ts,
  CAST(sess_num AS VARCHAR) AS sess_num,
  user_id || ':' || CAST(sess_num AS VARCHAR) AS session_id
FROM numbered;
