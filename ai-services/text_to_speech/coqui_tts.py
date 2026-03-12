from fastapi import FastAPI
import base64
import os
import tempfile
from pydantic import BaseModel
from TTS.api import TTS

app = FastAPI()

tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")


class SpeakRequest(BaseModel):
    text: str


@app.post("/speak")
def speak(payload: SpeakRequest):
    if not payload.text.strip():
        return {"audio_base64": "", "mime_type": "audio/wav"}

    file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            file_path = tmp.name

        tts.tts_to_file(text=payload.text, file_path=file_path)

        with open(file_path, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode("ascii")

        return {
            "audio_base64": audio_base64,
            "mime_type": "audio/wav",
        }
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)