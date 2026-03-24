import uvicorn
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import logging
import threading
import time
import os
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("start_all")

# IMPORT the backend app (make sure we're in the right directory)
# backend/app/main.py -> app
# We'll need to add 'backend' to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.main import app as backend_app

# ═══════════════════════════════════════════════════════════════════════════════
# MOCK STT (Port 9000)
# ═══════════════════════════════════════════════════════════════════════════════
stt_app = FastAPI(title="Smarter Mock STT")

GOLDEN_TRANSCRIPTS = {
    "water": "Mere ghar ke saamne pani ki pipeline tut gayi hai, bahut pani beh raha hai ji umm help",
    "fire": "Emergency! Mere building mein fire lag gayi hai, please help quickly!",
    "prank": "hello ji... umm... hello... hi... haha",
    "electricity": "Hamaare mohalle mein bijli nahi aa rahi hai, transformer kharab hai",
    "road": "Main road pe bahut bada pothole hai, do accidents ho chuke hain",
    "dummy": "This is a dummy transcription for a dummy file."
}

@stt_app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    filename = file.filename.lower()
    logger.info(f"STT Mock: Transcribing {filename}")
    transcript = "unknown audio input"
    for key, val in GOLDEN_TRANSCRIPTS.items():
        if key in filename:
            transcript = val
            break
    if filename == "dummy.wav":
        transcript = GOLDEN_TRANSCRIPTS["water"]
    return {"text": transcript}

@stt_app.get("/")
def stt_health():
    return {"status": "healthy"}

# ═══════════════════════════════════════════════════════════════════════════════
# MOCK TTS (Port 9001)
# ═══════════════════════════════════════════════════════════════════════════════
tts_app = FastAPI(title="Mock TTS Service")

class SpeakRequest(BaseModel):
    text: str

@tts_app.post("/speak")
def speak(payload: SpeakRequest):
    logger.info(f"TTS Mock: Speaking '{payload.text[:30]}...'")
    tiny_wav = "UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAP8A/wD/"
    return {"audio_base64": tiny_wav, "mime_type": "audio/wav"}

@tts_app.get("/")
def tts_health():
    return {"status": "healthy"}

# ═══════════════════════════════════════════════════════════════════════════════
# MOCK LLM (Port 9002)
# ═══════════════════════════════════════════════════════════════════════════════
llm_app = FastAPI(title="Mock LLM Service")

class QueryRequest(BaseModel):
    query: str

@llm_app.post("/generate")
def generate(payload: QueryRequest):
    logger.info(f"LLM Mock: Processing '{payload.query[:30]}...'")
    return {
        "response_text": f"Grievance recorded: {payload.query}",
        "department": "Water & Sewerage",
        "status": "success"
    }

@llm_app.get("/")
def llm_health():
    return {"status": "healthy"}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run_service(app_to_run, port):
    uvicorn.run(app_to_run, host="0.0.0.0", port=port, log_level="error")

if __name__ == "__main__":
    logger.info("Starting Consolidated Stack on 8080, 9000, 9001, 9002...")
    
    threads = [
        threading.Thread(target=run_service, args=(backend_app, 8080), daemon=True),
        threading.Thread(target=run_service, args=(stt_app, 9000), daemon=True),
        threading.Thread(target=run_service, args=(tts_app, 9001), daemon=True),
        threading.Thread(target=run_service, args=(llm_app, 9002), daemon=True),
    ]
    
    for t in threads:
        t.start()
    
    # Give it a second to boot
    time.sleep(2)
    logger.info("Stack Ready! Test at http://localhost:8080/calls/health")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping all services.")
