import duckdb
from pathlib import Path

DB = "data/local.duckdb"
OUTDIR = Path("projects/01_query_log_relevance_detective/outputs")
OUTDIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(DB)

# 1) Sessionize searches: new session when gap > 30 minutes for same user
con.execute("""
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
""")

# 2) Per-event click features (clicked? best rank? reciprocal rank)
con.execute("""
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
""")

# 3) Session metrics: no-click + possible reformulation
con.execute("""
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
""")

# 4) Daily KPIs (portfolio table #1) - SAFE aggregation (no row explosion)
daily = con.execute("""
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
""").df()

daily.to_csv(OUTDIR / "daily_kpis.csv", index=False)

# 5) Top “bad queries” (portfolio table #2)
bad = con.execute("""
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
WHERE q_count >= 20
ORDER BY ctr ASC, q_count DESC
LIMIT 200;
""").df()

bad.to_csv(OUTDIR / "top_bad_queries.csv", index=False)

# 6) Top “good queries” (portfolio table #3)
good = con.execute("""
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
WHERE q_count >= 20
ORDER BY ctr DESC, mrr DESC NULLS LAST, q_count DESC
LIMIT 200;
""").df()

good.to_csv(OUTDIR / "top_good_queries.csv", index=False)

# 7) All queries (portfolio table #4)
allq = con.execute("""
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
""").df()

allq.to_csv(OUTDIR / "per_query_all.csv", index=False)

# 8) Per-day queries (portfolio table #5)
day='2006-04-13'
per_day = con.execute(f'''
WITH per_query AS (
  SELECT
    se.query_norm,
    COUNT(*) AS q_count,
    AVG(qcf.has_click) AS ctr,
    AVG(qcf.rr) AS mrr
  FROM search_events_sess se
  JOIN query_click_features qcf
    ON se.event_id = qcf.event_id
  WHERE DATE(se.ts) = DATE '{day}'
    AND se.query_norm IS NOT NULL
    AND length(trim(se.query_norm)) > 0
  GROUP BY se.query_norm
)
SELECT *
FROM per_query
WHERE q_count >= 1
''').df()

per_day.to_csv(OUTDIR / f'per_query_{day}.csv', index=False)


print("Done.")
