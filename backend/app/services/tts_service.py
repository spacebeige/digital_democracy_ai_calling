import requests
import time
from app.config import TTS_API


REQUEST_TIMEOUT_SECONDS = 45
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
            time.sleep(0.6 * (attempt + 1))

    raise RuntimeError(f"TTS request failed after retries: {last_error}")

def text_to_speech(text):

    payload = {"text": text}

    response = _post_with_retry(f"{TTS_API}/speak", payload)

    return response.json()