from ingestion import embed_text
from vector_store import load_documents, load_index, search_vector


def retrieve_context(query: str, k: int = 3):
    loaded = load_index()
    documents = load_documents()
    if not loaded or not documents:
        return {
            "documents": [],
            "message": "index_not_ready",
        }

    query_vector = embed_text(query)
    distances, indices = search_vector(query_vector)

    flat_indices = indices[0].tolist()
    flat_distances = distances[0].tolist()

    results = []
    for idx, distance in zip(flat_indices[:k], flat_distances[:k]):
        if idx < 0 or idx >= len(documents):
            continue
        doc = documents[idx]
        results.append(
            {
                "id": doc["id"],
                "text": doc["text"],
                "source": doc["source"],
                "distance": float(distance),
            }
        )

    return {
        "documents": results,
        "message": "ok",
    }