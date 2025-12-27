SELECT 'docs' AS table_name, COUNT(*) AS n FROM docs
UNION ALL SELECT 'queries', COUNT(*) FROM queries
UNION ALL SELECT 'qrels', COUNT(*) FROM qrels
UNION ALL SELECT 'candidates', COUNT(*) FROM candidates
UNION ALL SELECT 'ollama_scores', COUNT(*) FROM ollama_scores;
