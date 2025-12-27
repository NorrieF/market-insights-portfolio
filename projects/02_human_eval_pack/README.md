# Project 2: Human Judgments vs Retrieval Baseline (BEIR SciFact)

## Goal
Build a small, reproducible evaluation loop for search relevance using a **public IR benchmark**:
1) Load a dataset with **human relevance judgments** (qrels),
2) Generate retrieval candidates with a baseline ranker (BM25-style via DuckDB FTS),
3) Compute evaluation metrics (Recall@K, MRR@K),
4) (Next) Compare an LLM “judge” against human qrels on the same candidate set.

This mirrors the real workflow of search/recommendation evaluation:
**data → candidate generation → evaluation → iteration**.

## Dataset
- **BEIR / SciFact** (via `ir_datasets`)
- Split used in this demo run: `test`
- Loaded counts (test split):
  - docs: 5,183  
  - queries: 300  
  - qrels: 339  

## Storage
- DuckDB database: `data/beir_scifact.duckdb`

## Core Tables (DuckDB)
- `docs(doc_id, title, text)`
- `queries(query_id, text)`
- `qrels(query_id, doc_id, relevance, iteration)`  
  Human judgments (ground truth) from the benchmark.
- `candidates(query_id, doc_id, rank, source)`  
  Retrieval results for evaluation (top-K per query).
- `ollama_scores(...)` *(planned / optional)*  
  LLM-as-judge outputs to compare against qrels.

## Outputs
Generated CSVs under `projects/02_human_eval_pack/outputs/`:
- `eval_per_query.csv`  
  Per-query metrics (e.g., Recall@10, MRR@10).
- `eval_summary.csv`  
  Aggregate metrics across all queries.

> Note: outputs CSVs are typically gitignored. Keep an `outputs/README.md` so the folder exists in fresh clones.

## How the evaluation works (conceptual)
- **Candidates:** For each query, we retrieve the top-K candidate docs using a baseline (BM25-style).
- **Ground truth:** SciFact qrels tell us which docs are relevant to each query.
- **Metrics:**
  - **Recall@10**: fraction of queries where at least one relevant doc appears in top 10.
  - **MRR@10**: average reciprocal rank of the first relevant doc in top 10.

## How to run
From repo root:

```bash
# 1) Load BEIR SciFact into DuckDB
uv run python projects/02_human_eval_pack/scripts/etl_beir_scifact.py --split test

# 2) Create / reset evaluation tables
uv run python projects/02_human_eval_pack/scripts/init_eval_tables.py

# 3) Build retrieval candidates (BM25-style)
uv run python projects/02_human_eval_pack/scripts/build_candidates.py

# 4) Compute evaluation metrics and write CSV outputs
uv run python projects/02_human_eval_pack/scripts/eval_metrics.py
