# Project 1: Query Log Relevance Detective (AOL-IA demo)

## Goal
Analyze query logs + clicks to identify search pain patterns and propose fixes.

## Data
- Source: AOL-IA query logs via ir_datasets (sample: 200k queries)
- Local store: DuckDB (`data/local.duckdb`)
- Outputs: aggregated CSVs in `outputs/`

## Core Metrics
- CTR: avg(has_click)
- MRR: avg(1 / best_click_rank)
- No-click session rate
- Possible reformulation rate (multi-query sessions proxy)

## Key Outputs
- `outputs/daily_kpis.csv`
- `outputs/top_bad_queries.csv`

## Next Steps
- Add query feature columns (length, script flags, etc.)
- Segment “bad queries” by type (navigational vs informational)
- Produce Tableau dashboard + 1-page insights memo
https://public.tableau.com/views/demo_17666438544170/Dashboard1?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link