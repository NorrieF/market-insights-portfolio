from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import duckdb
import ir_datasets
from tqdm import tqdm

from shared.scripts.repo_paths import read_sql, repo_root


SearchRow = Tuple[int, str, str, str, str, datetime]
ClickRow = Tuple[int, str, str, str, int]


def flush(con: duckdb.DuckDBPyConnection, searches: List[SearchRow], clicks: List[ClickRow]) -> None:
    if searches:
        con.executemany(
            """
            INSERT INTO search_events(event_id, user_id, query_id, query_norm, query_orig, ts)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            searches,
        )
        searches.clear()

    if clicks:
        con.executemany(
            """
            INSERT INTO click_events(event_id, user_id, query_id, doc_id, rank)
            VALUES (?, ?, ?, ?, ?)
            """,
            clicks,
        )
        clicks.clear()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/local.duckdb", help="DuckDB path (repo-relative unless absolute)")
    ap.add_argument("--limit", type=int, default=200_000, help="Number of qlog rows to ingest (sample)")
    ap.add_argument("--batch", type=int, default=10_000, help="Insert batch size")
    args = ap.parse_args()

    ROOT = repo_root(__file__)

    # Resolve DB path safely (works no matter where you run the script from)
    db_arg = Path(args.db)
    db_path = db_arg if db_arg.is_absolute() else (ROOT / db_arg)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))

    # Schema + indexes (from SQL file at ../sql relative to this script)
    con.execute(read_sql(__file__, "schema.sql"))

    dataset = ir_datasets.load("aol-ia")

    searches: List[SearchRow] = []
    clicks: List[ClickRow] = []

    n = 0
    event_id = 0

    for qlog in tqdm(dataset.qlogs_iter(), total=args.limit):
        event_id += 1
        user_id = qlog.user_id
        query_id = qlog.query_id
        query_norm = qlog.query
        query_orig = qlog.query_orig
        ts = qlog.time

        searches.append((event_id, user_id, query_id, query_norm, query_orig, ts))

        for item in qlog.items:
            if item.clicked:
                clicks.append((event_id, user_id, query_id, item.doc_id, item.rank))

        n += 1
        if n % args.batch == 0:
            flush(con, searches, clicks)

        if n >= args.limit:
            break

    flush(con, searches, clicks)

    se = con.execute("SELECT COUNT(*) FROM search_events").fetchone()[0]
    ce = con.execute("SELECT COUNT(*) FROM click_events").fetchone()[0]
    print(f"Done. search_events={se:,} click_events={ce:,} db={db_path}")


if __name__ == "__main__":
    main()
