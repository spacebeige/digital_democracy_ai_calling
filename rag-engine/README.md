# RAG Engine Quickstart

## 1) Build the local index

```bash
cd rag-engine
python3 -m pip install -r requirements.txt
python3 ingestion.py
```

This creates:
- `rag-engine/artifacts/kb.index`
- `rag-engine/artifacts/kb_docs.json`

## 2) Test retrieval

```bash
cd rag-engine
python3 -c "from retrieval import retrieve_context; print(retrieve_context('road pothole near school', k=3))"
```

## 3) Use with LLM service

The LLM service automatically attempts retrieval from `rag-engine`.
If artifacts are missing, it falls back to non-RAG response mode.

## Notes
- Current embeddings are deterministic hashed vectors for MVP speed.
- Replace `embed_text` in `ingestion.py` with a real embedding model for production quality.
