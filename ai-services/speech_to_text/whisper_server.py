from fastapi import FastAPI, UploadFile
import whisper

app = FastAPI()

model = whisper.load_model("base")

@app.post("/transcribe")
async def transcribe(file: UploadFile):

    audio = await file.read()

    with open("temp.wav", "wb") as f:
        f.write(audio)

    result = model.transcribe("temp.wav")

    return {"text": result["text"]}