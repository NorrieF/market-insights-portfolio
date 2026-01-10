from __future__ import annotations

import argparse

from shared.scripts.repo_paths import read_sql, connect_duckdb, ensure_outpath


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb", help="DuckDB path (repo-relative unless absolute)")
    ap.add_argument("--out", default="projects/02_human_eval_pack/outputs", help="Output directory (repo-relative unless absolute)")
    args = ap.parse_args()

    out = ensure_outpath(__file__, args.out)

    con = connect_duckdb(__file__, args.db)
    con.execute(read_sql(__file__, "eval_metrics.sql"))

    con.execute(f"COPY eval_per_query TO '{out / 'eval_per_query.csv'}' (HEADER, DELIMITER ',');")
    con.execute(f"COPY eval_summary   TO '{out / 'eval_summary.csv'}' (HEADER, DELIMITER ',');")

    print(con.execute("SELECT * FROM eval_summary").df())
    print(f"Wrote: {out / 'eval_per_query.csv'}")
    print(f"Wrote: {out / 'eval_summary.csv'}")


if __name__ == "__main__":
    main()
