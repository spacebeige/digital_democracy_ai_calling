from fastapi import FastAPI, File, UploadFile
from faster_whisper import WhisperModel
import os
import tempfile
import uvicorn

app = FastAPI(title="Mock STT 9000")

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("small", compute_type="int8")
    return _model


@app.get("/")
def health():
    return {"status": "healthy", "service": "stt"}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio = await file.read()
    if not audio:
        return {"text": ""}

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            temp_path = tmp.name
            tmp.write(audio)

        model = _get_model()
        segments, info = model.transcribe(temp_path, beam_size=1)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return {
            "text": text,
            "detected_language": getattr(info, "language", None),
            "confidence": 1.0,
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)
