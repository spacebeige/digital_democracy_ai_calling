import logging
from fastapi import FastAPI, UploadFile, File
import time
import hashlib

app = FastAPI(title="Smarter Mock STT")
logger = logging.getLogger("stt")

# lookup table of "Accurate" transcriptions for testing Layer 3
# Key can be a snippet of the filename or a fingerprint if we wanted to be fancy.
GOLDEN_TRANSCRIPTS = {
    "water": "Mere ghar ke saamne pani ki pipeline tut gayi hai, bahut pani beh raha hai ji umm help",
    "fire": "Emergency! Mere building mein fire lag gayi hai, please help quickly!",
    "prank": "hello ji... umm... hello... hi... haha",
    "electricity": "Hamaare mohalle mein bijli nahi aa rahi hai, transformer kharab hai",
    "road": "Main road pe bahut bada pothole hai, do accidents ho chuke hain",
    "dummy": "This is a dummy transcription for a dummy file."
}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    filename = file.filename.lower()
    logger.info(f"Smarter Mock STT: Transcribing {filename}")
    
    # Simulate a small delay for "Realism"
    time.sleep(0.5)

    # Heuristic: find a matching transcript based on filename
    transcript = "unknown audio input"
    for key, val in GOLDEN_TRANSCRIPTS.items():
        if key in filename:
            transcript = val
            break
            
    # If it's the exact dummy file I created, return the water leak one for the smoke test
    if filename == "dummy.wav":
        transcript = GOLDEN_TRANSCRIPTS["water"]

    return {"text": transcript}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)