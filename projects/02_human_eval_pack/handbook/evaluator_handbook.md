# Evaluator Handbook: Web Search Relevance (AOL-IA demo)

## Purpose
Score how well each candidate result would satisfy the user's query.

We use a 0–3 relevance scale plus a few optional notes. The goal is consistency.

## Unit of judgment
Each row in `eval_candidates.csv` is one (query, candidate_doc_id) pair.
Judge the candidate *as if it were shown for that query*.

## Relevance scale (0–3)
**3 = Perfect**
- Directly satisfies the query intent.
- If the query is navigational (e.g., "facebook"), the official destination is a 3.

**2 = Good / Mostly satisfies**
- Clearly relevant, but not the best target or missing a key aspect.
- Example: query "facebook" → a Wikipedia page about Facebook (relevant, but not the destination).

**1 = Related but not satisfying**
- On-topic but unlikely to solve the user's intent.
- Example: query "facebook" → a news story mentioning Facebook in passing.

**0 = Wrong**
- Unrelated, spammy, misleading, or clearly not what the query asks for.

## Guidance for common query types
### Navigational queries
If the query looks like a website/brand/person name and the user likely wants a specific destination:
- Destination page: 3
- Wikipedia/overview: 2
- News/other pages: 1
- Unrelated: 0

### Transactional queries ("download", "buy", "tickets", "price")
- If the candidate enables the action: 3
- If it is info about the action but not actionable: 2
- Tangential info: 1
- Wrong: 0

### Ambiguous queries ("jaguar", "apple", etc.)
If you cannot infer intent, score based on plausibility:
- Highly plausible dominant intent match: 2–3
- Plausible but uncertain: 1–2
- Clearly different meaning: 0–1

## Notes field
Use `notes` to explain borderline decisions in a few words, e.g.
- "navigational"
- "ambiguous query"
- "news not destination"
- "spam / low-quality"
