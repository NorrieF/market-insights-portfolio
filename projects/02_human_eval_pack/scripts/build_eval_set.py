from __future__ import annotations

import argparse
import random
from pathlib import Path

import duckdb
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/local.duckdb", help="DuckDB path")
    ap.add_argument("--outdir", default="projects/02_human_eval_pack/inputs", help="Output directory")
    ap.add_argument("--n_events", type=int, default=200, help="Number of query events to sample")
    ap.add_argument("--clicked_events", type=int, default=120, help="How many sampled events should have clicks")
    ap.add_argument("--neg_per_query", type=int, default=9, help="Random negative candidates per query")
    ap.add_argument("--seed", type=int, default=7, help="Random seed")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(args.db)

    # Sample events: mix clicked and no-click.
    # (If your dataset has fewer clicked/no-click events than requested, DuckDB will just return fewer.)
    events = con.execute(
        f"""
        WITH base AS (
          SELECT
            se.event_id,
            se.query_norm,
            se.ts,
            CASE WHEN EXISTS (
              SELECT 1 FROM click_events ce WHERE ce.event_id = se.event_id
            ) THEN 1 ELSE 0 END AS has_click
          FROM search_events se
          WHERE se.query_norm IS NOT NULL AND length(trim(se.query_norm)) > 0
        ),
        picked AS (
          SELECT *
          FROM base
          QUALIFY
            (has_click = 1 AND row_number() OVER (PARTITION BY has_click ORDER BY random()) <= {args.clicked_events})
            OR
            (has_click = 0 AND row_number() OVER (PARTITION BY has_click ORDER BY random()) <= {args.n_events - args.clicked_events})
        )
        SELECT *
        FROM picked
        ORDER BY ts
        """
    ).df()

    # Build a pool of doc_ids to sample negatives from.
    doc_pool = con.execute(
        """
        SELECT DISTINCT doc_id
        FROM click_events
        WHERE doc_id IS NOT NULL
        """
    ).df()["doc_id"].tolist()

    random.seed(args.seed)

    rows: list[dict] = []
    for r in events.itertuples(index=False):
        event_id = int(r.event_id)
        q = r.query_norm

        # Positive candidate: best clicked doc for this event (if any).
        pos = con.execute(
            """
            SELECT doc_id, MIN(rank) AS best_rank
            FROM click_events
            WHERE event_id = ?
            GROUP BY doc_id
            ORDER BY best_rank ASC
            LIMIT 1
            """,
            [event_id],
        ).df()

        if len(pos) == 1:
            rows.append(
                {
                    "event_id": event_id,
                    "query_norm": q,
                    "candidate_doc_id": pos.loc[0, "doc_id"],
                    "candidate_source": "clicked_best",
                    "candidate_rank_if_clicked": int(pos.loc[0, "best_rank"]),
                    "relevance_0_3": "",
                    "notes": "",
                }
            )

        # Negative candidates: random docs from the global clicked pool.
        k = min(args.neg_per_query, len(doc_pool))
        for doc_id in random.sample(doc_pool, k=k):
            rows.append(
                {
                    "event_id": event_id,
                    "query_norm": q,
                    "candidate_doc_id": doc_id,
                    "candidate_source": "random_negative",
                    "candidate_rank_if_clicked": "",
                    "relevance_0_3": "",
                    "notes": "",
                }
            )

    cand = pd.DataFrame(rows)

    (events[["event_id", "query_norm", "ts", "has_click"]]).to_csv(outdir / "eval_queries.csv", index=False)
    cand.to_csv(outdir / "eval_candidates.csv", index=False)

    print("Wrote:", outdir / "eval_queries.csv", "rows=", len(events))
    print("Wrote:", outdir / "eval_candidates.csv", "rows=", len(cand))


if __name__ == "__main__":
    main()
