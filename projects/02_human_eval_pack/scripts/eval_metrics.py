from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
from shared.scripts.repo_paths import repo_root, read_sql


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb", help="DuckDB path (repo-relative unless absolute)")
    ap.add_argument("--outdir", default="projects/02_human_eval_pack/outputs", help="Output directory (repo-relative unless absolute)")
    args = ap.parse_args()

    root = repo_root(__file__)
    db_arg = Path(args.db)
    db_path = db_arg if db_arg.is_absolute() else (root / db_arg)

    out_arg = Path(args.outdir)
    outdir = out_arg if out_arg.is_absolute() else (root / out_arg)
    outdir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))
    con.execute(read_sql(__file__, "eval_metrics.sql"))

    con.execute(f"COPY eval_per_query TO '{outdir / 'eval_per_query.csv'}' (HEADER, DELIMITER ',');")
    con.execute(f"COPY eval_summary   TO '{outdir / 'eval_summary.csv'}' (HEADER, DELIMITER ',');")

    print(con.execute("SELECT * FROM eval_summary").df())
    print(f"Wrote: {outdir / 'eval_per_query.csv'}")
    print(f"Wrote: {outdir / 'eval_summary.csv'}")


if __name__ == "__main__":
    main()
