from __future__ import annotations

import argparse
from pathlib import Path

import ir_datasets
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="projects/02_human_eval_pack/outputs/eval_candidates.csv")
    ap.add_argument("--outfile", default="projects/02_human_eval_pack/outputs/eval_candidates_enriched.csv")
    args = ap.parse_args()

    infile = Path(args.infile)
    outfile = Path(args.outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(infile)
    doc_ids = sorted(set(df["candidate_doc_id"].dropna().astype(str).tolist()))

    dataset = ir_datasets.load("aol-ia")
    store = dataset.docs_store()  # docstore supports fetching docs by doc_id :contentReference[oaicite:3]{index=3}

    # Build doc_id -> metadata map
    meta = {}
    for doc in store.get_many_iter(doc_ids):  # :contentReference[oaicite:4]{index=4}
        meta[doc.doc_id] = {
            "candidate_url": doc.url,
            "candidate_title": doc.title,
            "candidate_ia_url": doc.ia_url,
        }

    meta_df = pd.DataFrame(
        [{"candidate_doc_id": k, **v} for k, v in meta.items()]
    )

    out = df.merge(meta_df, on="candidate_doc_id", how="left")
    out.to_csv(outfile, index=False)
    print("Wrote:", outfile)
    print("Coverage:", out["candidate_url"].notna().mean())


if __name__ == "__main__":
    main()
