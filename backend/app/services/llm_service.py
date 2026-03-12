import requests
from app.config import LLM_API

def process_query(query: str):

    payload = {
        "query": query
    }

    response = requests.post(
        f"{LLM_API}/generate",
        json=payload
    )

    return response.json()