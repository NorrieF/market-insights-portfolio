from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
from shared.scripts.repo_paths import repo_root, read_sql


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb", help="DuckDB path (repo-relative unless absolute)")
    args = ap.parse_args()

    root = repo_root(__file__)
    db_arg = Path(args.db)
    db_path = db_arg if db_arg.is_absolute() else (root / db_arg)

    con = duckdb.connect(str(db_path))

    # Core tables should already exist from ETL, but running again is harmless
    con.execute(read_sql(__file__, "schema_core.sql"))
    con.execute(read_sql(__file__, "schema_eval.sql"))

    print(f"Done. Initialized eval tables in {db_path}")


if __name__ == "__main__":
    main()
