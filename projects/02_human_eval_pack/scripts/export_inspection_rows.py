from __future__ import annotations

import argparse
import csv

from shared.scripts.repo_paths import read_sql, connect_duckdb, ensure_outpath


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

    out_path = ensure_outpath(__file__, args.out)
    sql = read_sql(__file__, "export_inspection.sql")

    con = connect_duckdb(__file__, args.db)

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
