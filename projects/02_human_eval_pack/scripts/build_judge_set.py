from __future__ import annotations

import argparse

from shared.scripts.repo_paths import read_sql, connect_duckdb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb")
    ap.add_argument("--topk", type=int, default=10)
    ap.add_argument("--table", default="judge_items_for_llm")

    args = ap.parse_args()
    con = connect_duckdb(__file__, args.db)

    sql = read_sql(__file__, "build_judge_set.sql")
    sql = sql.replace("{{TOPK}}", str(int(args.topk)))
    con.execute(sql)

    n = con.execute("SELECT COUNT(*) FROM judge_set").fetchone()[0]
    nq = con.execute("SELECT COUNT(DISTINCT query_id) FROM judge_set").fetchone()[0]
    print(f"Done. judge_set={n:,} rows across {nq:,} queries (topk={args.topk})")

    sql2 = read_sql(__file__, "build_judge_items_for_llm.sql")
    con.execute(sql2)

    n = con.execute(f"SELECT COUNT(*) FROM {args.table}").fetchone()[0]
    print(f"Done. {args.table}={n:,} rows")

    con.execute("CHECKPOINT;")
    con.close()


if __name__ == "__main__":
    main()
