# Project 3: Data Quality Bouncer (Amazon Catalog) — Quantifying Metadata Damage on Search

## What this project is
A reproducible **impact simulator** that answers a very un-trivial question:

> When catalog metadata gets messy (missing brand, truncated descriptions, broken tokenization, wrong categories), **how much does search quality actually drop** and **which fields matter most for which query types**?

This mirrors real search quality work where teams need to separate:
- “ranking regression” vs
- “data pipeline / feed quality issue”

…and then **quantify** the impact so engineering knows what to fix first.

---

## Goal
1) Load a public **Amazon-like product catalog dataset** (product metadata + text fields)
2) Build a simple baseline retriever (**BM25 via DuckDB FTS**)
3) Create controlled “data damage” versions of the catalog (corruptions)
4) Measure **search quality deltas** and **rank volatility**
5) Produce portfolio artifacts:
   - scorecards (field completeness, corruption severity)
   - retrieval metrics (Recall@K, MRR@K, nDCG@K optional)
   - a “what to fix first” report + CSVs

**Thesis:** Data quality issues are measurable, field-specific, and query-type-dependent. We can quantify sensitivity and prioritize fixes by impact.

---

## Dataset (Amazon public data)
We’ll use one of the following **public Amazon product metadata** sources (decide in implementation):
- Amazon product metadata + categories (commonly used in research; product title/description/brand/category fields)
- Amazon reviews metadata (optional; used to generate query-like text or enrich descriptions)

**Minimum required columns:**
- `doc_id` (product id)
- `title` (string)
- `description` (string; can be empty)
- `brand` (string; can be empty)
- `category` (string or list/path)

**Optional columns (nice-to-have):**
- bullet attributes (color/size/material)
- seller/merchant id (if present)
- price (for realism; not required)

> We’re not trying to build a perfect marketplace search engine. We’re building a controlled lab to measure *how data issues become retrieval issues*.

---

## What “search” means here (no click logs required)
We evaluate retrieval using **synthetic relevance judgments** derived from the catalog itself.

### Query set (generated)
We generate query types that mimic real ecommerce intent:
- **Brand intent**: “nike air max 90”
- **Category intent**: “running shoes”
- **Attribute intent**: “black waterproof jacket”
- **Mixed intent**: “sony noise cancelling headphones”
- **Tokenization edge cases**: “airmax90” vs “air max 90”

### Ground truth (labels)
For each synthetic query, we define the relevant set as:
- Products that match required fields (brand/category/attributes), using deterministic rules.

This gives us a reproducible “truth set” so we can compute metrics without human labeling.

---

## Experiment design: Controlled corruptions (“damage knobs”)
We create multiple catalog variants from the same base data:

### Corruption types
1) **Missing Brand**
- Set `brand=NULL` for X% of products (random or vendor/category targeted)

2) **Truncated Description**
- Keep only first N characters / N words

3) **Tokenization Breaks**
- Convert “Air Max 90” → “AirMax90”
- Remove spaces/hyphens, collapse punctuation, etc.

4) **Category Noise**
- Swap category with a neighboring category for X% of products

5) **Attribute Dropout** (if attributes exist)
- Remove color/size/material fields for X% of products

### Severity levels
Each corruption runs at multiple severities, e.g.:
- 0% (control), 5%, 10%, 20%, 40%

---

## Metrics: what we measure
For each catalog variant, using the same query set:

### Retrieval metrics (per query and overall)
- **Recall@K**: do we retrieve relevant items in top K?
- **MRR@K**: how early does the first relevant item appear?
- **nDCG@K** (optional): ranking quality when multiple relevant items exist

### Stability / volatility metrics
- **Top-1 flip rate**: how often the top result changes vs control
- **Jaccard@K**: overlap between top-K sets (control vs corrupted)

### Data quality scorecard
- completeness rates per field (brand/description/category/attributes)
- corruption severity parameters used

---

## Storage
DuckDB database (gitignored):
- `data/amazon_dq_bouncer.duckdb`

---

## DuckDB tables (planned)
### Core
- `products(doc_id, title, description, brand, category, attrs_json, ...)`
- `queries(query_id, query_text, query_type, params_json)`
- `truth(query_id, doc_id, relevance)` (synthetic labels)

### Retrieval
- `candidates(query_id, doc_id, rank, score, variant)`  
  `variant` identifies which corruption run (e.g., `control`, `miss_brand_10`, `trunc_desc_20`)

### Metrics
- `metrics_per_query(query_id, variant, recall_at_k, mrr_at_k, ndcg_at_k, ...)`
- `metrics_summary(variant, avg_recall_at_k, avg_mrr_at_k, avg_ndcg_at_k, top1_flip_rate, ...)`

### Data quality scorecard
- `dq_scorecard(variant, brand_fill_rate, desc_fill_rate, category_fill_rate, ...)`

---

## Outputs (portfolio artifacts)
CSV outputs (gitignored but folder kept):
- `outputs/metrics_summary.csv`
- `outputs/metrics_by_query_type.csv`
- `outputs/top_impact_corruptions.csv` (ranked by quality drop)
- `outputs/examples_rank_flips.csv` (before/after examples: query + top docs)
- `reports/` screenshots/plots for README

---

## Why this is portfolio-worthy (the “so what”)
This isn’t “missing data is bad.” This is:

- Which missing fields matter most?
- Which query types are most sensitive?
- How big is the measurable impact at realistic corruption rates?
- What would you fix first if you had one sprint?

That’s the difference between vibes and engineering decisions.

---

## How to run (planned pipeline)
From repo root:

```bash
# 0) Create environment
uv sync

# 1) Download / prepare Amazon public data (implementation decides source)
uv run python projects/03_data_quality_bouncer/scripts/get_amazon_data.py

# 2) ETL into DuckDB (products table)
uv run python projects/03_data_quality_bouncer/scripts/etl_amazon_catalog.py

# 3) Generate synthetic query set + deterministic truth labels
uv run python projects/03_data_quality_bouncer/scripts/build_queries_and_truth.py --n_queries 2000

# 4) Build retrieval index + run baseline (control)
uv run python projects/03_data_quality_bouncer/scripts/run_retrieval.py --variant control --topk 10

# 5) Run corruption suite + retrieval
uv run python projects/03_data_quality_bouncer/scripts/run_corruption_suite.py --topk 10

# 6) Compute metrics + scorecards + exports
uv run python projects/03_data_quality_bouncer/scripts/compute_metrics.py --topk 10
uv run python projects/03_data_quality_bouncer/scripts/export_reports.py
```

## Notes / caveats

- Synthetic labels are not “human truth,” but they are perfect for measuring sensitivity because the rules are stable and reproducible.
- The goal is to quantify relative degradation between control and corrupted variants, not to claim we built the best ranker.

## Success criteria (what “done” looks like)

- A clear metrics_summary.csv showing monotonic quality drops as corruption severity increases

- A “field importance” section in the final report:

    - e.g., brand-missing hurts brand-intent queries most

    - tokenization breaks hurt model/sku queries most

- A short list of actionable takeaways:

    - “Raise brand fill rate above X% to avoid Y% recall loss on brand queries”

    - “Normalize tokenization to reduce top-1 flip rate by Z%”

## Next steps (optional)

- Add lightweight visualization (Tableau or a simple matplotlib report)
- Add an LLM-based attribute repair (Ollama) and measure “repair improves retrieval” vs “repair introduces noise”
- Extend to category-specific analysis (shoes vs electronics behave differently)