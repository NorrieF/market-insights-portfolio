# Project 2: Human Eval Pack — Human Evaluation vs LLM Judgement

## Data we use: SciFact

This project uses **BEIR / SciFact**, which is a public benchmark for **scientific claim verification** and **information retrieval**.

Even though we talk about “queries” and “documents”, this is *not* web search.
The data consists of **short scientific statements (claims)** + **paper abstracts** + **human judgments of their relevance**:

### 1) Queries = scientific claims
Each “query” is a short sentence that reads like a claim someone might make in a paper or discussion.

Example (query_text):
- `0-dimensional biomaterials show inductive properties.`  
- `ADAR1 binds to Dicer to cleave pre-miRNA.`

In our database:
- `queries(query_id, text)`

### 2) Documents = paper titles + abstracts
Each “doc” is a scientific paper entry, typically:
- A **title**
- An **abstract** (or abstract-like text)

Example (doc):
- title: `ADAR1 Forms a Complex with Dicer to Promote MicroRNA Processing...`
- text: *(abstract text)*

In our database:
- `docs(doc_id, title, text)`

### 3) Human evaluation labels = “this doc is relevant to this claim”
SciFact provides **human relevance judgments** that mark a small set of documents as relevant to each query/claim.

Important: these labels are mostly **positive judgments**.
- If a doc is labeled relevant, a human decided it matches the claim task (often: evidence for/against the claim).
- If a doc is *not labeled*, it often means **not evaluated**, not “proven irrelevant.”

In our database:
- `qrels(query_id, doc_id, relevance, iteration)`

In this project we treat:
- `relevance > 0` as **human-labeled relevant**  
(SciFact’s relevance is effectively binary for our usage here.)

### 4) Data engineering for LLM judgement
Because judging every doc (5,183) per query would be expensive, we build a **per-query candidate pool** of size `K`:

- Always include **all human-labeled relevant docs** for that query
- Fill the rest using **BM25 retrieval** (top-scoring docs from DuckDB full-text search)

This produces:
- `judge_set(query_id, doc_id, slot, source)`  
  where:
  - `slot` is 1..K (position inside the pool)
  - `source` is `qrels_pos` for the human-labeled positives, and `bm25_fill` for the rest

Then we create a denormalized view for Ollama prompts:
- `judge_items_for_llm(query_id, query_text, n_rel, doc_id, title, text, slot)`

### 5) Ollama outputs
For each query, we tell Ollama:
- The claim (query_text)
- The `K` candidate docs (title + abstract text)
- `n_rel` = how many docs humans labeled relevant for that query

Ollama must return exactly `n_rel` **slots** (which docs it thinks are relevant).
We store that as:
- `ollama_picks(query_id, doc_id, slot, model, prompt_v, created_at)`

### Mental model
**Humans label which abstracts are relevant to a claim; BM25 builds a small pool; Ollama tries to pick the same “relevant evidence” from that pool, and we analyze where they agree or disagree.**
In short,
**load labeled data → build a candidate pool → have LLM label relevance → compare human & LLM judges → adjudicate**
> SciFact includes benchmark splits like `train`/`test`. Here we use the **test split for evaluation**. The split naming is benchmark protocol, not ML training.

---

## Process
1) Load a dataset with **human relevance judgments**
2) Build a **candidate pool per query** that contains:
   - **all known human-labeled relevant docs**, plus
   - **BM25 top docs** to fill up to K total
3) Ask **Ollama** to select which docs are relevant *from the same pool* (while being told how many positives to pick)
4) Compare **Ollama vs human evaluation** to:
   - measure agreement
   - identify likely **missing labels** (docs Ollama marks relevant but humans didn’t label)
   - produce a disagreement queue for follow-up review

**Research question:** *Can an LLM help audit or expand an IR benchmark’s relevance labels?*

---

## Dataset
- **BEIR / SciFact** via `ir_datasets`
- Split used: `test`

Loaded counts (`test` run):
- docs: **5,183**
- queries: **300**
- human-labeled positives: **339** (relevance is binary in SciFact: relevant vs not relevant)

---

## Storage
- DuckDB database: `data/beir_scifact.duckdb`

---

## DuckDB tables

### Core tables
- `docs(doc_id, title, text)`
- `queries(query_id, text)`
- `qrels(query_id, doc_id, relevance, iteration)`  
  Human judgments (human-labeled relevant docs are `relevance > 0`)

### Candidate pool + LLM judging
- `candidates(query_id, doc_id, rank, source)`  
  BM25 retrieval results (top-K per query, `source='bm25'`)
- `judge_set(query_id, doc_id, slot, source)`  
  The **shared pool** used for judging:
  - includes **all human-labeled relevant docs** for the query (`source='qrels_pos'`)
  - plus **BM25 fill docs** until total size reaches K (`source='bm25_fill'`)
- `judge_items_for_llm(query_id, query_text, n_rel, doc_id, title, text, slot)`  
  Denormalized rows used to build Ollama prompts.
- `ollama_picks(query_id, doc_id, slot, model, prompt_v, created_at)`  
  Ollama’s selected relevant docs (as slots mapped back to doc_ids).

> Important nuance: in IR benchmarks, “not labeled relevant” can mean “not judged” rather than “judged irrelevant.”
> So docs Ollama selects outside the human-labeled positives are treated as **potential missing labels**, not automatic false positives.

---

## The role BM25 plays
BM25 isn’t the star. It’s the *bouncer at the club door* 🕶️:

- It creates a **small, plausible set of candidate docs per query**
- So Ollama can judge relevance without scoring all 5,183 docs
- Disagreements focus on **near-miss** docs (the ones worth arguing about)

---

## Candidate pool design
For each query:

1) Start with **all human-labeled relevant docs**
2) Add BM25 results **excluding those positives** until total pool size reaches **K**

Formally:

`judge_set(q) = human_positives(q) ∪ (bm25_top_docs(q) \\ human_positives(q))`

Default: `K = 10` (can be increased to 20 for more “hard” negatives).

This design:
- guarantees all known positives are present
- increases the chance that disagreement = “interesting” (possible missing label)
- avoids pretending that “unjudged = irrelevant”

---

## Evaluation taxonomy

### LLM Judgement
For each query, the LLM sees:
- the query
- the K candidate docs (title + text)
- and `n_rel` (how many docs humans labeled relevant for this query)

The LLM returns:
- **LLM-selected relevant docs**: which items it believes are relevant (returned as pool slots, mapped back to doc_ids)

### Comparison Outcomes
Each doc in the pool falls into one of these buckets:

- **Agreement on relevant**  
  Human says relevant AND LLM says relevant
- **Human relevant, LLM missed** (missed positives)  
  Human says relevant BUT LLM did not pick it
- **LLM picked, humans didn’t label it** (possible missing label)  
  LLM says relevant BUT humans didn’t label it relevant  
  (treat as “review needed,” not automatic error)
- **Neither picked**  
  Human didn’t label it relevant AND LLM didn’t pick it

**Key rule:** “LLM picked but not human-labeled” is *not automatically wrong* because the benchmark labels may be incomplete.

---

## Metrics and Outputs

### Retrieval Baseline (BM25 vs Human Labels)
Classic IR metrics for BM25 top-K against human-labeled positives:
- **Recall@10**  
  `(# human positives retrieved in top10) / (# human positives total)`
- **MRR@10**  
  `1 / rank(first human-positive doc)` (0 if none in top10)

Outputs:
- `projects/02_human_eval_pack/outputs/eval_per_query.csv`
- `projects/02_human_eval_pack/outputs/eval_summary.csv`

### LLM Judge Evaluation (Ollama vs Human Labels)
Ollama is told `n_rel` and must return exactly that many pool **slots** from the K-sized pool.
We then compare its picks to human-labeled positives to compute:
- per-query recall of human-labeled positives
- overall agreement rate
- disagreement queue (human positives vs LLM picks)

---

## Results (Ollama's judgement might vary across trials)

### BM25 Retrieval Baseline
BM25 retrieval on SciFact test split (top 10 per query):
- **Avg Recall@10:** `0.8209`
- **Avg MRR@10:** `0.6321`
- **Queries evaluated:** `300`

### Ollama Judge
Ollama judge (`llama3.1:8b`, `prompt_v=v1`) on `judge_set` with `K=10`:
- picks written: **339** (exactly matches total human-labeled positives across all queries)
- pick agreement with human-labeled positives: **45 / 339 ≈ 13.3%** 

This low agreement is expected in early iterations and is the point of the project: surface disagreements that may indicate:
- LLM weakness on scientific relevance,
- prompt format issues,
- or **missing / incomplete labels** in the benchmark.

---

## Manual spot-check: 10 missed-positive examples (n_rel=1)
To get an intuitive feel for why Ollama disagrees with human evaluation, we inspected 10 queries where:
- humans labeled exactly **1** relevant doc in the pool, and
- Ollama selected a different doc (a missed-positive case)

**Summary of what we saw:**
1) **Query 1 (0-dimensional biomaterials...)**: the human-labeled doc is only loosely related (nanotech + stem cells), while Ollama’s pick directly discusses stem-cell properties and mechanisms, matching the “inductive properties” vibe better.
2) **Query 3 (1,000 genomes project...)**: the human-labeled doc is highly specific to synthetic associations/rare variants, while Ollama’s pick is a broad overview; humans likely rewarded specificity, Ollama rewarded topical overlap.
3) **Query 5 (PrP positivity prevalence...)**: the human-labeled doc is a large-scale prevalence survey (exactly the claim), while Ollama picked a transfusion case report; Ollama latched onto vCJD but missed the prevalence framing.
4) **Query 13 (perinatal mortality & low birth weight...)**: the human-labeled doc is global underweight prevalence, while Ollama’s pick is direct perinatal mortality data; Ollama looks more on-target, suggesting the human label may be incomplete or proxy-based.
5) **Query 42 (microerythrocyte count & thalassemia...)**: the human-labeled doc is a mechanistic malaria/anemia study in α+-thalassemia, while Ollama’s pick is a genotyping survey; human relevance is about the exact causal story, Ollama chose a keyword-adjacent but less explanatory paper.
6) **Query 48 (UK asymptomatic vCJD carriers...)**: the human-labeled doc is the prevalence survey again (exact claim), while Ollama picked the transfusion preclinical case; same pattern as Query 5: topic match, wrong “what is being claimed.”
7) **Query 49 (ADAR1 binds Dicer...)**: the human-labeled doc is exactly ADAR1-Dicer complex and miRNA processing, while Ollama picked a Dicer-2 specificity paper; Ollama matched “Dicer” but missed ADAR1.
8) **Query 50 (AIRE expressed in some skin tumors...)**: the human-labeled doc is tumor keratinocytes expressing Aire (exact), while Ollama picked thymic selection and melanoma immunity; Ollama matched AIRE but missed “skin tumors / expression.”
9) **Query 51 (ALDH1 better outcomes...)**: the human-labeled doc actually reports ALDH1 correlates with poor prognosis (contradicts query), while Ollama picked birthweight and breast cancer; both are arguably off, but this is a good example where the human-labeled positive may reflect dataset claim-linking rather than surface relevance.
10) **Query 53 (ALDH1 poorer prognosis...)**: the human-labeled doc supports poor prognosis (matches query), while Ollama picked obesity and breast cancer prognosis; Ollama matched “poor prognosis” but missed the ALDH1-specific claim.

> These examples suggest a consistent failure mode: Ollama often matches broad topical similarity (keywords and general domain) but misses the *claim-specific* nature of SciFact labels, which are closer to “supports/refutes this statement” than “same topic.”

---

## Hypothetical conclusion (what we can say right now)
Based on the current agreement rate (~13% on human-labeled positives) and the 10-example spot-check:

- **Ollama (llama3.1:8b, v1 prompt) is not yet reliable as a drop-in replacement for human evaluation on SciFact-style claim verification.**
- Its picks often look *plausible* in-topic, but frequently fail the stricter “this document supports the specific statement” standard.
- Some disagreements also appear to expose **labeling quirks** (e.g., query-text vs paper claim alignment), meaning the benchmark itself can contain surprising positives.

**Next iteration direction:** tighten prompts toward claim verification (support/refute/insufficient) and require citation-style justification (“Which sentence in the abstract supports the claim?”), then re-measure agreement and re-review missed-positive examples.

## How to run

From repo root:

```bash
# 1) Load SciFact into DuckDB (docs + queries + human labels)
uv run python projects/02_human_eval_pack/scripts/etl_beir_scifact.py

# 2) Create / reset eval tables (used by BM25 metrics)
uv run python projects/02_human_eval_pack/scripts/init_eval_tables.py

# 3) Create / reset Ollama tables (stores LLM picks/scores)
uv run python projects/02_human_eval_pack/scripts/init_ollama_tables.py

# 4) Build BM25 candidates (topK per query)
uv run python projects/02_human_eval_pack/scripts/build_candidates.py

# 5) Build the shared judge pool (all human positives + BM25 fill up to K)
uv run python projects/02_human_eval_pack/scripts/build_judge_set.py

# 6) Build denormalized prompt rows for the LLM judge
uv run python projects/02_human_eval_pack/scripts/build_judge_items_for_llm.py

# 7) (optional) Baseline retrieval metrics for BM25 (writes CSV outputs)
uv run python projects/02_human_eval_pack/scripts/eval_metrics.py

# 8) Run Ollama judging (requires Ollama running locally and model pulled)
uv run python projects/02_human_eval_pack/scripts/run_ollama_judge.py --model llama3.1:8b

# 9) (optional) Export inspection examples (writes CSV to outputs/)
uv run python projects/02_human_eval_pack/scripts/export_inspection_rows.py
```

---

## Install Ollama

### Linux
Install:
```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ollama --version
```

If the service isn’t running:
```bash
    sudo systemctl enable --now ollama
```

Pull a model + smoke test:
```bash
    ollama pull llama3.1:8b
    ollama run llama3.1:8b "Say hello in one sentence."
```

Verify the local API:
```bash
    curl -s http://localhost:11434/api/tags | head
```

### macOS
1) Download and install Ollama for macOS from the official Ollama site.
2) Open the Ollama app once (this starts the local server).
3) In Terminal:
```bash
    ollama --version
    ollama pull llama3.1:8b
    ollama run llama3.1:8b "Say hello in one sentence."
```
Verify the local API:
```bash
    curl -s http://localhost:11434/api/tags | head
```

### Windows
1) Download and install Ollama for Windows from the official Ollama site.
2) Open Ollama (this starts the local server).
3) In PowerShell:
```bash
    ollama --version
    ollama pull llama3.1:8b
    ollama run llama3.1:8b "Say hello in one sentence."
```
Verify the local API:
```bash
    curl http://localhost:11434/api/tags
```