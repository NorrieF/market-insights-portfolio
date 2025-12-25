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
    SUM(new_sess) OVER (PARTITION BY user_id ORDER BY ts
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS sess_num
  FROM flags
)
SELECT
  user_id,
  query_id,
  query_norm,
  query_orig,
  ts,
  CAST(sess_num AS VARCHAR) AS sess_num,
  user_id || ':' || CAST(sess_num AS VARCHAR) AS session_id
FROM numbered;
""")

# 2) Per-query click features (clicked? best rank? reciprocal rank)
con.execute("""
CREATE OR REPLACE VIEW query_click_features AS
SELECT
  se.query_id,
  MIN(ce.rank) AS best_click_rank,
  CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END AS has_click,
  CASE WHEN COUNT(*) > 0 THEN 1.0 / MIN(ce.rank) ELSE NULL END AS rr
FROM search_events se
LEFT JOIN click_events ce
  ON se.query_id = ce.query_id
GROUP BY se.query_id;
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
  JOIN query_click_features qcf ON se.query_id = qcf.query_id
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

# 4) Daily KPIs (portfolio table #1)
daily = con.execute("""
WITH per_query AS (
  SELECT
    DATE_TRUNC('day', se.ts) AS day,
    qcf.has_click,
    qcf.rr
  FROM search_events_sess se
  JOIN query_click_features qcf ON se.query_id = qcf.query_id
),
per_session AS (
  SELECT
    DATE_TRUNC('day', MIN(se.ts)) AS day,
    MAX(sm.no_click_session) AS no_click_session,
    MAX(sm.possible_reformulation) AS possible_reformulation
  FROM search_events_sess se
  JOIN session_metrics sm ON se.session_id = sm.session_id
  GROUP BY sm.session_id
)
SELECT
  pq.day,
  COUNT(*) AS queries,
  AVG(pq.has_click) AS ctr,
  AVG(pq.rr) AS mrr,
  AVG(ps.no_click_session) AS no_click_rate,
  AVG(ps.possible_reformulation) AS possible_reformulation_rate
FROM per_query pq
JOIN per_session ps USING (day)
GROUP BY pq.day
ORDER BY pq.day;
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
  JOIN query_click_features qcf ON se.query_id = qcf.query_id
  GROUP BY se.query_norm
)
SELECT *
FROM per_query
WHERE q_count >= 20
ORDER BY ctr ASC, q_count DESC
LIMIT 200;
""").df()
bad.to_csv(OUTDIR / "top_bad_queries.csv", index=False)

print("Wrote:", OUTDIR / "daily_kpis.csv")
print("Wrote:", OUTDIR / "top_bad_queries.csv")
print("Done.")
