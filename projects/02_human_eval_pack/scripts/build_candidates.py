from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
from tqdm import tqdm

from shared.scripts.repo_paths import repo_root, read_sql


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb")
    ap.add_argument("--topk", type=int, default=10)
    args = ap.parse_args()

    root = repo_root(__file__)
    db_arg = Path(args.db)
    db_path = db_arg if db_arg.is_absolute() else (root / db_arg)

    con = duckdb.connect(str(db_path))

    con.execute(read_sql(__file__, "build_candidates.sql"))

    queries = con.execute("SELECT query_id, text FROM queries ORDER BY query_id").fetchall()

    insert_rows = []
    for query_id, qtext in tqdm(queries, desc="building candidates"):
        rows = con.execute(
            """
            SELECT
              doc_id,
              fts_main_docs.match_bm25(doc_id, ?) AS score
            FROM docs
            WHERE score IS NOT NULL
            ORDER BY score DESC
            LIMIT ?
            """,
            [qtext, args.topk],
        ).fetchall()

        for rank, (doc_id, _score) in enumerate(rows, start=1):
            insert_rows.append((str(query_id), str(doc_id), int(rank), "bm25"))

    con.executemany(
        "INSERT INTO candidates(query_id, doc_id, rank, source) VALUES (?, ?, ?, ?)",
        insert_rows,
    )

    n = con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    print(f"Done. candidates={n:,} db={db_path}")

    con.execute("CHECKPOINT;")
    con.close()


if __name__ == "__main__":
    main()
