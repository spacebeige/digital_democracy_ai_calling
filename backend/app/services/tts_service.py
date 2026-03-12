import requests
from app.config import TTS_API

def text_to_speech(text):

    payload = {"text": text}

    response = requests.post(
        f"{TTS_API}/speak",
        json=payload
    )

    return response.content