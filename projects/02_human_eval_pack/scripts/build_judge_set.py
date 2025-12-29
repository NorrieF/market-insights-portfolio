from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from shared.scripts.repo_paths import repo_root, read_sql


def run_sql_script(con: duckdb.DuckDBPyConnection, sql: str) -> None:
    # simple splitter is fine (no semicolons inside strings in our SQL files)
    for stmt in (s.strip() for s in sql.split(";")):
        if stmt:
            con.execute(stmt)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb")
    ap.add_argument("--topk", type=int, default=10)
    args = ap.parse_args()

    root = repo_root(__file__)
    db_arg = Path(args.db)
    db_path = db_arg if db_arg.is_absolute() else (root / db_arg)

    con = duckdb.connect(str(db_path))

    sql = read_sql(__file__, "build_judge_set.sql")
    sql = sql.replace("{{TOPK}}", str(int(args.topk)))

    run_sql_script(con, sql)

    n = con.execute("SELECT COUNT(*) FROM judge_set").fetchone()[0]
    nq = con.execute("SELECT COUNT(DISTINCT query_id) FROM judge_set").fetchone()[0]
    print(f"Done. judge_set={n:,} rows across {nq:,} queries (topk={args.topk}) db={db_path}")

    con.execute("CHECKPOINT;")
    con.close()


if __name__ == "__main__":
    main()
