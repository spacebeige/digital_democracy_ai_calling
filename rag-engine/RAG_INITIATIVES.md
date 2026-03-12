# RAG Initiatives (MVP -> Production)

## Initiative 1: Grounded MVP (Now)
- Create a local knowledge base from policy FAQs and SOP notes.
- Ingest text into chunked documents and vector index.
- Retrieve top-k context for each query before response generation.
- Return source snippets in API response for basic traceability.
- Success metric: at least 80% of test prompts include relevant context snippets.

## Initiative 2: Service Integration
- Trigger ingestion via script during deployment or startup.
- Add `/rag/health` and `/rag/stats` endpoints for observability.
- Use complaint department as a retrieval hint (water, roads, sanitation, electricity).
- Add fallback behavior when retrieval returns no relevant chunks.
- Success metric: p95 retrieval latency under 100 ms for local index.

## Initiative 3: Quality and Safety
- Add reranking strategy for top-k retrieved chunks.
- Add citation IDs in generated responses.
- Block unsupported claims when no grounded context exists.
- Add adversarial tests for hallucination and off-topic prompts.
- Success metric: reduced hallucination rate on internal eval set.

## Initiative 4: Production Hardening
- Move from in-memory FAISS to persistent index files or Qdrant.
- Add metadata filters (department, region, policy version, language).
- Add background re-indexing pipeline for updated documents.
- Introduce dashboard metrics for retrieval hit rate and drift.
- Success metric: stable retrieval quality across weekly doc updates.
