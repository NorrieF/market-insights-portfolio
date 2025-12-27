from __future__ import annotations

import duckdb

from shared.scripts.repo_paths import read_sql, repo_root


def main() -> None:
    ROOT = repo_root(__file__)

    db_path = ROOT / "data" / "local.duckdb"

    outdir = ROOT / "projects" / "01_query_log_relevance_detective" / "outputs"
    outdir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))

    # SQL lives in ../sql relative to this script, so read_sql(__file__, ...) works
    con.execute(read_sql(__file__, "sessionize.sql"))
    con.execute(read_sql(__file__, "query_click_features.sql"))
    con.execute(read_sql(__file__, "session_metrics.sql"))

    daily = con.execute(read_sql(__file__, "daily_kpis.sql")).df()
    daily.to_csv(outdir / "daily_kpis.csv", index=False)

    allq = con.execute(read_sql(__file__, "per_query_all.sql")).df()
    allq.to_csv(outdir / "per_query_all.csv", index=False)

    print("Done.")


if __name__ == "__main__":
    main()
