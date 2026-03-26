import base64
import logging
import uvicorn
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import asyncio
from faster_whisper import WhisperModel
import os
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_services")

# ═══════════════════════════════════════════════════════════════════════════════
# MOCK STT (Port 9000)
# ═══════════════════════════════════════════════════════════════════════════════
stt_app = FastAPI(title="Mock STT Service")
_stt_model: WhisperModel | None = None


def _get_stt_model() -> WhisperModel:
    global _stt_model
    if _stt_model is None:
        _stt_model = WhisperModel("small", compute_type="int8")
    return _stt_model

@stt_app.get("/")
def stt_health():
    return {"status": "healthy", "service": "stt"}

@stt_app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    logger.info(f"STT: Transcribing {file.filename}")
    audio = await file.read()
    if not audio:
        return {"text": ""}

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            temp_path = tmp.name
            tmp.write(audio)

        model = _get_stt_model()
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


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK TTS (Port 9001)
# ═══════════════════════════════════════════════════════════════════════════════
tts_app = FastAPI(title="Mock TTS Service")

class SpeakRequest(BaseModel):
    text: str

@tts_app.get("/")
def tts_health():
    return {"status": "healthy", "service": "tts"}

@tts_app.post("/speak")
def speak(payload: SpeakRequest):
    logger.info(f"Mock TTS: Speaking '{payload.text[:30]}...'")
    # Return a tiny blank WAV file in base64 (approx 1 second of silence)
    # This keeps the frontend from crashing if it expects audio.
    tiny_wav = (
        "UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAP8A/wD/"
    )
    return {
        "audio_base64": tiny_wav,
        "mime_type": "audio/wav"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK LLM (Port 9002)
# ═══════════════════════════════════════════════════════════════════════════════
llm_app = FastAPI(title="Mock LLM Service")

class QueryRequest(BaseModel):
    query: str

@llm_app.get("/")
def llm_health():
    return {"status": "healthy", "service": "llm"}

@llm_app.post("/generate")
def generate(payload: QueryRequest):
    logger.info(f"Mock LLM: Processing '{payload.query[:30]}...'")
    # Return a basic response that works with the existing call_routes.py
    return {
        "response_text": f"Grievance recorded: {payload.query}",
        "department": "Water & Sewerage",
        "status": "success"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Start all services on their respective ports
    import threading
    
    def run_stt():
        uvicorn.run(stt_app, host="0.0.0.0", port=9000)

    def run_tts():
        uvicorn.run(tts_app, host="0.0.0.0", port=9001)

    def run_llm():
        uvicorn.run(llm_app, host="0.0.0.0", port=9002)

    logger.info("Starting Mock STT (9000), Mock TTS (9001), and Mock LLM (9002)...")
    
    threads = [
        threading.Thread(target=run_stt, daemon=True),
        threading.Thread(target=run_tts, daemon=True),
        threading.Thread(target=run_llm, daemon=True),
    ]
    
    for t in threads:
        t.start()
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping mock services.")
