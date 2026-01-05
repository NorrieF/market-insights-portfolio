from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from shared.scripts.repo_paths import repo_root, read_sql


def run_sql_script(con: duckdb.DuckDBPyConnection, sql: str) -> None:
    for stmt in (s.strip() for s in sql.split(";")):
        if stmt:
            con.execute(stmt)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb")
    ap.add_argument("--table", default="judge_items_for_llm")
    args = ap.parse_args()

    root = repo_root(__file__)
    db_arg = Path(args.db)
    db_path = db_arg if db_arg.is_absolute() else (root / db_arg)

    con = duckdb.connect(str(db_path))

    sql = read_sql(__file__, "build_judge_items_for_llm.sql")
    run_sql_script(con, sql)

    n = con.execute(f"SELECT COUNT(*) FROM {args.table}").fetchone()[0]
    print(f"Done. {args.table}={n:,} rows db={db_path}")

    con.execute("CHECKPOINT;")
    con.close()


if __name__ == "__main__":
    main()
