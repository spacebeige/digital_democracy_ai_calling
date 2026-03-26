import base64
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Mock TTS 9011")


class SpeakRequest(BaseModel):
    text: str


@app.get("/")
def health():
    return {"status": "healthy", "service": "tts"}


@app.post("/speak")
def speak(payload: SpeakRequest):
    tiny_wav = "UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAP8A/wD/"
    return {"audio_base64": tiny_wav, "mime_type": "audio/wav"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9011)
