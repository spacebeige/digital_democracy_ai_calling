from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import requests

from app.config import LLM_API, STT_API, TTS_API
from app.database import SessionLocal
from app.models import Complaint
from app.schemas import CallTurnResponse
from app.services.llm_service import process_query
from app.services.stt_service import speech_to_text
from app.services.tts_service import text_to_speech

router = APIRouter()


def check_service(url: str) -> dict:
    try:
        response = requests.get(url, timeout=3)
        return {
            "ok": response.status_code < 500,
            "status_code": response.status_code,
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "status_code": None,
            "error": str(exc),
        }


def persist_complaint(transcript: str, department: str, call_id: str | None) -> int:
    db = SessionLocal()
    try:
        complaint = Complaint(
            phone_number=call_id or "unknown",
            issue=transcript,
            department=department or "general",
            status="processed",
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        return complaint.id
    finally:
        db.close()


@router.post("/handle-turn", response_model=CallTurnResponse)
async def handle_turn(
    audio_file: UploadFile = File(...),
    call_id: str | None = Form(default=None),
):
    try:
        audio_bytes = await audio_file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="audio_file is empty")

        stt_result = speech_to_text(audio_bytes, audio_file.filename or "audio.wav")
        transcript = (stt_result.get("text") or "").strip()
        if not transcript:
            raise HTTPException(status_code=502, detail="STT service returned empty transcript")

        llm_result = process_query(transcript)
        agent_text = (llm_result.get("response_text") or llm_result.get("response") or "").strip()
        department = (llm_result.get("department") or "general").strip() or "general"
        if not agent_text:
            raise HTTPException(status_code=502, detail="LLM service returned empty response")

        tts_result = text_to_speech(agent_text)
        audio_base64 = (tts_result.get("audio_base64") or "").strip()
        if not audio_base64:
            raise HTTPException(status_code=502, detail="TTS service returned no audio")

        complaint_id = persist_complaint(transcript, department, call_id)

        return {
            "success": True,
            "transcript": transcript,
            "agent_text": agent_text,
            "audio_base64": audio_base64,
            "complaint_id": complaint_id,
            "department": department,
            "call_id": call_id,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Call turn processing failed: {exc}")


@router.get("/health")
def call_health() -> dict:
    stt = check_service(STT_API)
    tts = check_service(TTS_API)
    llm = check_service(LLM_API)
    all_ok = stt["ok"] and tts["ok"] and llm["ok"]

    return {
        "ok": all_ok,
        "services": {
            "stt": {"url": STT_API, **stt},
            "tts": {"url": TTS_API, **tts},
            "llm": {"url": LLM_API, **llm},
        },
    }