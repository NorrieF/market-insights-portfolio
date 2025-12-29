from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import ir_datasets

from shared.scripts.repo_paths import read_sql, repo_root


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb", help="DuckDB path (repo-relative or absolute)")
    ap.add_argument("--split", default="test", choices=["test", "train", "dev"])
    args = ap.parse_args()

    root = repo_root(__file__)
    db_path = (root / Path(args.db)).resolve()  # works for both relative + absolute paths
    db_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))
    con.execute(read_sql(__file__, "schema_core.sql"))

    # reset
    con.execute("DELETE FROM docs;")
    con.execute("DELETE FROM queries;")
    con.execute("DELETE FROM qrels;")

    # load datasets
    ds_docs = ir_datasets.load("beir/scifact")
    ds_split = ir_datasets.load(f"beir/scifact/{args.split}")

    # docs
    docs = [(d.doc_id, getattr(d, "title", ""), d.text) for d in ds_docs.docs_iter()]
    con.executemany("INSERT INTO docs VALUES (?, ?, ?)", docs)

    # queries
    queries = [(q.query_id, q.text) for q in ds_split.queries_iter()]
    con.executemany("INSERT INTO queries VALUES (?, ?)", queries)

    # qrels
    qrels = [(r.query_id, r.doc_id, int(r.relevance), getattr(r, "iteration", "0")) for r in ds_split.qrels_iter()]
    con.executemany("INSERT INTO qrels VALUES (?, ?, ?, ?)", qrels)

    n_docs = con.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    n_q = con.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
    n_qrels = con.execute("SELECT COUNT(*) FROM qrels").fetchone()[0]
    print(f"Done. docs={n_docs:,} queries={n_q:,} qrels={n_qrels:,} db={db_path} split={args.split}")

    con.execute("CHECKPOINT;")
    con.close()


if __name__ == "__main__":
    main()
