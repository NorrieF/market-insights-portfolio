-- Materialize the LLM input "packet" as a TABLE (snapshot)
-- Includes: query_text + n_rel + K candidates (doc title/text), but DOES NOT include source.

CREATE OR REPLACE TABLE judge_items_for_llm AS
WITH rel_counts AS (
  SELECT
    query_id,
    COUNT(*) AS n_rel
  FROM qrels
  WHERE relevance > 0
  GROUP BY query_id
)
SELECT
  js.query_id,
  q.text AS query_text,
  rc.n_rel,
  js.doc_id,
  d.title,
  d.text,
  js.slot
FROM judge_set js
JOIN queries q
  ON q.query_id = js.query_id
JOIN docs d
  ON d.doc_id = js.doc_id
JOIN rel_counts rc
  ON rc.query_id = js.query_id;
