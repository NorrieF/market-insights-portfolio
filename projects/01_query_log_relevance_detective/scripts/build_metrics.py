from pathlib import Path
import duckdb

DB = "data/local.duckdb"
ROOT = Path(__file__).resolve().parents[3]  # repo root (scripts/ -> 01_... -> projects -> repo)
SQLDIR = ROOT / "projects/01_query_log_relevance_detective/sql"
OUTDIR = ROOT / "projects/01_query_log_relevance_detective/outputs"
OUTDIR.mkdir(parents=True, exist_ok=True)

def read_sql(name: str) -> str:
    return (SQLDIR / name).read_text(encoding="utf-8")

con = duckdb.connect(str(ROOT / DB))

con.execute(read_sql("01_sessionize.sql"))
con.execute(read_sql("02_query_click_features.sql"))
con.execute(read_sql("03_session_metrics.sql"))

daily = con.execute(read_sql("04_daily_kpis.sql")).df()
daily.to_csv(OUTDIR / "daily_kpis.csv", index=False)

allq = con.execute(read_sql("05_per_query_all.sql")).df()
allq.to_csv(OUTDIR / "per_query_all.csv", index=False)

print("Done.")
