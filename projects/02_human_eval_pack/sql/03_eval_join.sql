WITH human AS (
  SELECT
    c.query_id,
    c.doc_id,
    c.rank,
    c.source,
    COALESCE(q.relevance, 0) AS human_relevance
  FROM candidates c
  LEFT JOIN qrels q
    ON c.query_id = q.query_id
   AND c.doc_id   = q.doc_id
),
llm AS (
  SELECT
    query_id,
    doc_id,
    model,
    score_0_3,
    rationale
  FROM ollama_scores
)
SELECT
  h.query_id,
  h.doc_id,
  h.rank,
  h.source,
  h.human_relevance,
  l.model,
  l.score_0_3 AS llm_score,
  l.rationale
FROM human h
LEFT JOIN llm l
  ON h.query_id = l.query_id
 AND h.doc_id   = l.doc_id;
