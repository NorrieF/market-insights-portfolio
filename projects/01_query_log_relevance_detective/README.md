# Project 1: Query Log Relevance Detective (AOL-IA demo)

## Goal
Use query logs + click signals to surface search pain points, quantify impact, and outline practical fixes.

## Dataset
- Source: AOL-IA query logs via `ir_datasets` (sample: 200,000 search events)
- Storage: DuckDB at `data/local.duckdb`
- Scope note: AOL-IA provides search events and clicked items. It does not provide full impression lists (all results shown), so metrics use click-based proxies.

## Tables
- `search_events`: one row per search event (keyed by `event_id`)
- `click_events`: one row per click (joined to searches by `event_id`)
- `search_events_sess`: searches sessionized by 30-min inactivity gap per user

## Metrics (proxies)
- **CTR (proxy):** `avg(has_click)` where `has_click ∈ {0,1}` per search event  
- **MRR:** `avg(1 / best_click_rank)` using the best (minimum) clicked rank per event
- **No-click session rate:** share of sessions with zero clicks
- **Possible reformulation rate:** share of sessions with >1 distinct query (proxy, not a perfect reformulation definition)

## Outputs
- `outputs/daily_kpis.csv` (daily CTR/MRR/no-click/reformulation proxies)
- `outputs/top_bad_queries.csv` (high-volume queries ranked by lowest CTR)

## Dashboard
- [![Tableau dashboard preview](reports/dashboard.png)](https://public.tableau.com/views/demo_17666438544170/Dashboard1?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

## How to run
```bash
uv run python projects/01_query_log_relevance_detective/scripts/etl_aol_ia.py --limit 200000
uv run python projects/01_query_log_relevance_detective/scripts/build_metrics.py
