import faiss
import numpy as np

dimension = 768
index = faiss.IndexFlatL2(dimension)

def add_vector(vector):
    index.add(np.array([vector]))

def search_vector(query_vector):
    distances, indices = index.search(
        np.array([query_vector]), 5
    )
    return indices