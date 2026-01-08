WITH rel AS (
      SELECT query_id, doc_id
      FROM qrels
      WHERE relevance > 0
    ),
    nrel1 AS (
      SELECT query_id
      FROM rel
      GROUP BY query_id
      HAVING COUNT(*) = 1
    ),
    qpos AS (
      SELECT r.query_id, r.doc_id AS qrels_doc_id
      FROM rel r
      JOIN nrel1 USING (query_id)
    ),
    picks_ranked AS (
      SELECT
        query_id,
        doc_id AS ollama_doc_id,
        slot,
        created_at,
        ROW_NUMBER() OVER (
          PARTITION BY query_id
          ORDER BY slot ASC, created_at ASC, doc_id ASC
        ) AS rn
      FROM ollama_picks
      WHERE model = ?
    ),
    first_pick AS (
      SELECT query_id, ollama_doc_id
      FROM picks_ranked
      WHERE rn = 1
    ),
    misses AS (
      SELECT
        q.query_id,
        q.qrels_doc_id,
        fp.ollama_doc_id
      FROM qpos q
      JOIN first_pick fp USING (query_id)
      WHERE fp.ollama_doc_id <> q.qrels_doc_id
    )
    SELECT
      m.query_id,
      qu.text AS query_text,

      m.qrels_doc_id,
      dpos.title AS qrels_title,
      dpos.text  AS qrels_text,

      m.ollama_doc_id,
      doll.title AS ollama_title,
      doll.text  AS ollama_text
    FROM misses m
    JOIN queries qu ON qu.query_id = m.query_id
    JOIN docs dpos  ON dpos.doc_id = m.qrels_doc_id
    JOIN docs doll  ON doll.doc_id = m.ollama_doc_id
    ORDER BY CAST(m.query_id AS INTEGER)
    LIMIT ?;