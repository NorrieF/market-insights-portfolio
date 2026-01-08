from __future__ import annotations

import argparse
import csv
from pathlib import Path

import duckdb

from shared.scripts.repo_paths import repo_root, read_sql


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/beir_scifact.duckdb")
    ap.add_argument("--model", default="llama3.1:8b")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument(
        "--out",
        default="projects/02_human_eval_pack/outputs/inspect_missed_positive_nrel1.csv",
        help="CSV output path (repo-relative unless absolute)",
    )
    args = ap.parse_args()

    root = repo_root(__file__)
    db_path = Path(args.db)
    db_path = db_path if db_path.is_absolute() else (root / db_path)

    out_path = Path(args.out)
    out_path = out_path if out_path.is_absolute() else (root / out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))

    sql = read_sql(__file__, "export_inspection.sql")

    rows = con.execute(sql, [args.model, args.limit]).fetchall()
    con.close()

    headers = [
        "query_id",
        "query_text",
        "qrels_doc_id",
        "qrels_title",
        "qrels_text",
        "ollama_doc_id",
        "ollama_title",
        "ollama_text",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
