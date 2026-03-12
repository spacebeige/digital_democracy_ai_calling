from fastapi import FastAPI, UploadFile
import os
import tempfile
import whisper

app = FastAPI()

model = whisper.load_model("base")

@app.post("/transcribe")
async def transcribe(file: UploadFile):
    audio = await file.read()
    if not audio:
        return {"text": ""}

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            temp_path = tmp.name
            tmp.write(audio)

        result = model.transcribe(temp_path)
        return {"text": result["text"]}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)