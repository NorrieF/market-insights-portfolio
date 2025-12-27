from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import duckdb
import ir_datasets
from tqdm import tqdm

from shared.scripts.repo_paths import read_sql, repo_root


DocRow = Tuple[str, str, str]          # doc_id, title, text
QueryRow = Tuple[str, str]            # query_id, text
QrelRow = Tuple[str, str, int, str]   # query_id, doc_id, relevance, iteration


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--db",
        default="data/beir_scifact.duckdb",
        help="DuckDB path (repo-relative unless absolute)",
    )
    ap.add_argument("--split", default="test", choices=["test", "dev", "train"], help="BEIR split for qrels/queries")
    ap.add_argument("--batch_docs", type=int, default=5000)
    ap.add_argument("--batch_queries", type=int, default=2000)
    ap.add_argument("--batch_qrels", type=int, default=5000)
    args = ap.parse_args()

    ROOT = repo_root(__file__)
    db_arg = Path(args.db)
    db_path = db_arg if db_arg.is_absolute() else (ROOT / db_arg)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))
    con.execute(read_sql(__file__, "00_schema.sql"))

    # Reset (keeps reruns clean)
    con.execute("DELETE FROM docs;")
    con.execute("DELETE FROM queries;")
    con.execute("DELETE FROM qrels;")

    # Docs live in the base dataset
    ds_docs = ir_datasets.load("beir/scifact")

    # Queries + qrels live in the split dataset (e.g., beir/scifact/test)
    ds_split_name = f"beir/scifact/{args.split}"
    ds_split = ir_datasets.load(ds_split_name)

    # Docs
    docs: List[DocRow] = []
    for d in tqdm(ds_docs.docs_iter(), desc="docs"):
        docs.append((d.doc_id, getattr(d, "title", ""), d.text))
        if len(docs) >= args.batch_docs:
            con.executemany("INSERT INTO docs VALUES (?, ?, ?)", docs)
            docs.clear()
    if docs:
        con.executemany("INSERT INTO docs VALUES (?, ?, ?)", docs)

    # Queries (from split)
    qs: List[QueryRow] = []
    for q in tqdm(ds_split.queries_iter(), desc=f"queries ({args.split})"):
        qs.append((q.query_id, q.text))
        if len(qs) >= args.batch_queries:
            con.executemany("INSERT INTO queries VALUES (?, ?)", qs)
            qs.clear()
    if qs:
        con.executemany("INSERT INTO queries VALUES (?, ?)", qs)

    # Qrels (from split)
    if not hasattr(ds_split, "qrels_iter"):
        raise RuntimeError(f"{ds_split_name} does not expose qrels_iter() in this ir_datasets build.")

    qr: List[QrelRow] = []
    for r in tqdm(ds_split.qrels_iter(), desc=f"qrels ({args.split})"):
        qr.append((r.query_id, r.doc_id, int(r.relevance), getattr(r, "iteration", "0")))
        if len(qr) >= args.batch_qrels:
            con.executemany("INSERT INTO qrels VALUES (?, ?, ?, ?)", qr)
            qr.clear()
    if qr:
        con.executemany("INSERT INTO qrels VALUES (?, ?, ?, ?)", qr)

    # Quick sanity
    n_docs = con.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    n_q = con.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
    n_qrels = con.execute("SELECT COUNT(*) FROM qrels").fetchone()[0]
    print(f"Done. docs={n_docs:,} queries={n_q:,} qrels={n_qrels:,} db={db_path} split={args.split}")


if __name__ == "__main__":
    main()
