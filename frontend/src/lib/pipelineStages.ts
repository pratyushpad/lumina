/**
 * Shared retrieval-pipeline stage vocabulary. Lives outside any component
 * file so it can be imported by both the real-data `TraceInspector` (the
 * disclosure hint per stage) and the chat surface's indicative loading
 * choreography (`StreamingMessage`) without tripping
 * react-refresh/only-export-components on either.
 */
export const STAGE_HINTS: Record<string, string> = {
  query_transform: "LLM query rewriting",
  dense: "pgvector cosine ANN",
  sparse_bm25: "Okapi BM25 (in-process)",
  sparse_fts: "Postgres ts_rank_cd",
  fusion: "Reciprocal Rank Fusion",
  hybrid_sql: "dense + FTS + RRF in one SQL",
  rerank: "cross-encoder rerank",
  vision_enrich: "image description (Gemini)",
  generation: "answer generation",
};
