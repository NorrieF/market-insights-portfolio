from __future__ import annotations

import argparse
import csv
from pathlib import Path

import duckdb

from shared.scripts.repo_paths import repo_root


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

    sql = """
    WITH rel AS (
      SELECT query_id, doc_id
      FROM qrels
      WHERE relevance > 0
    ),
    nrel1 AS (
      SELECT query_id
      FROM rel
      GROUP BY query_id
      HAVING COUNT(*) = 1
    ),
    qpos AS (
      SELECT r.query_id, r.doc_id AS qrels_doc_id
      FROM rel r
      JOIN nrel1 USING (query_id)
    ),
    picks_ranked AS (
      SELECT
        query_id,
        doc_id AS ollama_doc_id,
        slot,
        created_at,
        ROW_NUMBER() OVER (
          PARTITION BY query_id
          ORDER BY slot ASC, created_at ASC, doc_id ASC
        ) AS rn
      FROM ollama_picks
      WHERE model = ?
    ),
    first_pick AS (
      SELECT query_id, ollama_doc_id
      FROM picks_ranked
      WHERE rn = 1
    ),
    misses AS (
      SELECT
        q.query_id,
        q.qrels_doc_id,
        fp.ollama_doc_id
      FROM qpos q
      JOIN first_pick fp USING (query_id)
      WHERE fp.ollama_doc_id <> q.qrels_doc_id
    )
    SELECT
      m.query_id,
      qu.text AS query_text,

      m.qrels_doc_id,
      dpos.title AS qrels_title,
      dpos.text  AS qrels_text,

      m.ollama_doc_id,
      doll.title AS ollama_title,
      doll.text  AS ollama_text
    FROM misses m
    JOIN queries qu ON qu.query_id = m.query_id
    JOIN docs dpos  ON dpos.doc_id = m.qrels_doc_id
    JOIN docs doll  ON doll.doc_id = m.ollama_doc_id
    ORDER BY CAST(m.query_id AS INTEGER)
    LIMIT ?;
    """

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
