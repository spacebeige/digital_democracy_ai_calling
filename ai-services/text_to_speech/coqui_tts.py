from fastapi import FastAPI
from TTS.api import TTS

app = FastAPI()

tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

@app.post("/speak")
def speak(text: str):

    file_path = "output.wav"

    tts.tts_to_file(text=text, file_path=file_path)

    return {"audio": file_path}