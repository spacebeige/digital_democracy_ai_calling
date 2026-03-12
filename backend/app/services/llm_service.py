import requests
import time
from app.config import LLM_API


REQUEST_TIMEOUT_SECONDS = 20
MAX_RETRIES = 2


def _post_with_retry(url: str, payload: dict) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == MAX_RETRIES:
                break
            time.sleep(0.4 * (attempt + 1))

    raise RuntimeError(f"LLM request failed after retries: {last_error}")

def process_query(query: str):

    payload = {
        "query": query
    }

    response = _post_with_retry(f"{LLM_API}/generate", payload)

    return response.json()