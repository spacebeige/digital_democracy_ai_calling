import requests
from app.config import STT_API

def speech_to_text(audio_file):

    files = {"file": audio_file}

    response = requests.post(
        f"{STT_API}/transcribe",
        files=files
    )

    return response.json()