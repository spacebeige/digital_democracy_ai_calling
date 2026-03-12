import requests
import time
from app.config import STT_API


REQUEST_TIMEOUT_SECONDS = 45
MAX_RETRIES = 2


def _post_with_retry(url: str, files: dict) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(url, files=files, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == MAX_RETRIES:
                break
            time.sleep(0.6 * (attempt + 1))

    raise RuntimeError(f"STT request failed after retries: {last_error}")

def speech_to_text(audio_bytes: bytes, filename: str):

    files = {"file": (filename, audio_bytes, "audio/wav")}

    response = _post_with_retry(f"{STT_API}/transcribe", files)

    return response.json()