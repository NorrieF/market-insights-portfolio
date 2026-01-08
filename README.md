# Market Insights Portfolio (Data + Search Quality + LLM Evaluation)

A compact, reproducible portfolio repo that simulates day-to-day work in **market insights / search quality / human evaluation** roles.

Each project uses real public datasets and produces:
- a clean data pipeline (ETL → DuckDB),
- measurable quality metrics,
- shareable artifacts (CSVs, dashboards, reports),
- and clear, engineer-friendly writeups.

> **Audience:** recruiters, hiring managers, data scientists/engineers, and anyone who wants to see practical analysis + evaluation work end-to-end.

---

## Skills Demonstrated

### ✅ Practical data analysis
- SQL + Python pipelines
- DuckDB as a lightweight analytics warehouse
- Metric design and careful proxy definitions (when raw impressions aren’t available)
- Reproducible outputs (CSV exports for Tableau/BI)

### ✅ LLM evaluation workflows
- Using human judgments as ground truth
- Candidate generation + evaluation loop
- A clear slot to plug in an LLM-as-judge and compare against humans

### ✅ Portfolio-ready communication
- Clear README per project
- Visual artifacts (dashboard screenshots)
- Transparent caveats and assumptions

---

## Repo structure

```text
market-insights-portfolio/
  data/                         # DuckDB databases (gitignored)
  projects/
    01_query_log_relevance_detective/
      scripts/
      sql/
      outputs/                  # CSV outputs (gitignored, folder kept)
      reports/                  # images used in README (tracked)
      README.md
    02_human_eval_pack/
      scripts/
      sql/
      outputs/                  # CSV outputs (gitignored, folder kept)
      README.md
  shared/                       # shared helpers (paths, SQL loaders, etc.)
  pyproject.toml                # dependencies
  .gitignore
  uv.lock                       # versions 
```

## Projects

### Project 1: Query Log Relevance Detective (AOL-IA)
**Goal:** Use query logs + click signals to surface search pain points, quantify impact, and produce actionable insights.

**Highlights:**
- ETL from the AOL-IA query log dataset into DuckDB
- Sessionization (30-min inactivity gap)
- Click-based proxy metrics (CTR proxy, MRR, no-click sessions, possible reformulation)
- Tableau dashboard published to Tableau Public

➡️ See: [projects/01_query_log_relevance_detective/README.md](https://github.com/NorrieF/market-insights-portfolio/blob/main/projects/01_query_log_relevance_detective/README.md)

---

### Project 2: Human Eval Pack (BEIR SciFact)
**Goal:** Build a reproducible evaluation loop that compares human relevance labels with an LLM judge:
- Load the benchmark dataset (documents, queries, human labels),
- Build a per-query candidate pool (BM25 via DuckDB full-text search),
- Compute retrieval metrics (Recall@10, MRR@10),
- Run an Ollama model to judge relevance on the same pool and compare outputs.

➡️ See: [projects/02_human_eval_pack/README.md](https://github.com/NorrieF/market-insights-portfolio/blob/main/projects/02_human_eval_pack/README.md)

---

## Quickstart

### 1. Create environment
This repo uses `uv` for fast, reproducible Python environments.

```bash
uv sync
```

### 2. Run Project 1 pipeline
```bash
uv run python projects/01_query_log_relevance_detective/scripts/etl_aol_ia.py --limit 200000
uv run python projects/01_query_log_relevance_detective/scripts/build_metrics.py
```

### 3. Run Project 2 pipeline
```bash
uv run python projects/02_human_eval_pack/scripts/etl_beir_scifact.py
uv run python projects/02_human_eval_pack/scripts/init_eval_tables.py
uv run python projects/02_human_eval_pack/scripts/init_ollama_tables.py
uv run python projects/02_human_eval_pack/scripts/build_candidates.py
uv run python projects/02_human_eval_pack/scripts/build_judge_set.py
uv run python projects/02_human_eval_pack/scripts/build_judge_items_for_llm.py
uv run python projects/02_human_eval_pack/scripts/eval_metrics.py
uv run python projects/02_human_eval_pack/scripts/run_ollama_judge.py --model llama3.1:8b
uv run python projects/02_human_eval_pack/scripts/export_inspection_rows.py
```
Note: output CSVs are typically gitignored. Each outputs/ folder includes a `.gitkeep` so the folder exists for new clones.

## Tooling
- **DuckDB** for storage and analytics
- **Python** for ETL and metric generation
- **SQL** separated into `sql/` folders for consistency and readability
- **Tableau Public** for interactive dashboards (Project 1)

## Notes on reproducibility
Public datasets and packages can change over time. This repo is designed so you can:
- rebuild databases from scratch,
- regenerate metrics deterministically,
- and keep artifacts (dashboard screenshots) stable for recruiters.

If something breaks, the fastest reset is usually deleting the local DuckDB file under `data/` and rerunning the pipeline scripts.

## Contact / Context
This repo is a portfolio project for roles involving:
- market insights,
- search/recommendation quality analysis,
- human evaluation and LLM evaluation workflows.

My LinkedIn: https://www.linkedin.com/in/norikazu-furukawa-a6215729/
