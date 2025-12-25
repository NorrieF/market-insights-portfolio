from __future__ import annotations

import argparse
from datetime import datetime
from typing import List, Tuple

import duckdb
import ir_datasets
from tqdm import tqdm


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
    ap.add_argument("--db", default="data/local.duckdb", help="DuckDB path")
    ap.add_argument("--limit", type=int, default=200_000, help="Number of qlog rows to ingest (sample)")
    ap.add_argument("--batch", type=int, default=10_000, help="Insert batch size")
    args = ap.parse_args()

    con = duckdb.connect(args.db)

    # Minimal schema
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS search_events (
          event_id BIGINT,
          user_id    VARCHAR,
          query_id   VARCHAR,
          query_norm VARCHAR,
          query_orig VARCHAR,
          ts         TIMESTAMP
        );
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS click_events (
          event_id BIGINT,
          user_id  VARCHAR,
          query_id VARCHAR,
          doc_id   VARCHAR,
          rank     INTEGER
        );
        """
    )

    # (Optional) indexes to speed up later analysis
    con.execute("CREATE INDEX IF NOT EXISTS idx_search_user_ts ON search_events(user_id, ts);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_click_event ON click_events(event_id);")

    dataset = ir_datasets.load("aol-ia")

    searches: List[SearchRow] = []
    clicks: List[ClickRow] = []

    n = 0
    event_id = 0

    for qlog in tqdm(dataset.qlogs_iter(), total=args.limit):
        # qlog fields (per ir_datasets docs): event_id, user_id, query_id, query, query_orig, time, items :contentReference[oaicite:2]{index=2}
        event_id += 1
        user_id = qlog.user_id
        query_id = qlog.query_id
        query_norm = qlog.query
        query_orig = qlog.query_orig
        ts = qlog.time

        searches.append((event_id, user_id, query_id, query_norm, query_orig, ts))

        # items include doc_id, rank, clicked (bool); keep only clicked results
        for item in qlog.items:
            if item.clicked:
                clicks.append((event_id, user_id, query_id, item.doc_id, item.rank))

        n += 1
        if n % args.batch == 0:
            flush(con, searches, clicks)

        if n >= args.limit:
            break

    flush(con, searches, clicks)

    # Quick summary
    se = con.execute("SELECT COUNT(*) FROM search_events").fetchone()[0]
    ce = con.execute("SELECT COUNT(*) FROM click_events").fetchone()[0]
    print(f"Done. search_events={se:,} click_events={ce:,} db={args.db}")


if __name__ == "__main__":
    main()
