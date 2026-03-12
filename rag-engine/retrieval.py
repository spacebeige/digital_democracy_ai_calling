from vector_store import search_vector

def retrieve_context(query_vector):

    indices = search_vector(query_vector)

    return {
        "documents": indices.tolist()
    }