from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.database import SessionLocal
from app.models import AuditLog, Complaint, ConversationLog
from app.services.llm_service import process_query
from app.schemas import (
    ComplaintQueryRequest,
    ComplaintQueryResponse,
    ComplaintViewResponse,
    ConversationLogRequest,
    ConversationLogResponse,
    CreateComplaintRequest,
    CreateComplaintResponse,
    GenerateSummaryRequest,
    GenerateSummaryResponse,
)

router = APIRouter()


def _log_action(db, complaint_id: int, action: str, actor: str) -> None:
    db.add(AuditLog(complaint_id=complaint_id, action=action, actor=actor))


def _to_iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)

@router.post("/")
def create_complaint(payload: ComplaintQueryRequest) -> ComplaintQueryResponse:
    result = process_query(payload.query)
    return {
        "message": "Complaint processed",
        "response": result
    }


@router.post("/create-complaint", response_model=CreateComplaintResponse)
def create_complaint_record(payload: CreateComplaintRequest) -> CreateComplaintResponse:
    db = SessionLocal()
    try:
        expected_resolution = None
        if payload.expected_resolution:
            expected_resolution = datetime.fromisoformat(payload.expected_resolution)

        complaint = Complaint(
            phone=payload.phone,
            issue_text=payload.issue_text,
            summary=payload.summary,
            language=payload.language,
            sentiment=payload.sentiment,
            priority=payload.priority,
            status=payload.status,
            assigned_to=payload.assigned_to,
            location=payload.location,
            expected_resolution=expected_resolution,
        )
        db.add(complaint)
        db.flush()

        _log_action(db, complaint.id, "created", "AI")
        db.commit()
        return {"complaint_id": complaint.id}
    finally:
        db.close()


@router.post("/log-conversation", response_model=ConversationLogResponse)
def log_conversation(payload: ConversationLogRequest) -> ConversationLogResponse:
    db = SessionLocal()
    try:
        complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        conversation = ConversationLog(
            complaint_id=payload.complaint_id,
            speaker=payload.speaker,
            message=payload.message,
        )
        db.add(conversation)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


@router.post("/generate-summary", response_model=GenerateSummaryResponse)
def generate_summary(payload: GenerateSummaryRequest) -> GenerateSummaryResponse:
    db = SessionLocal()
    try:
        complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        conversation = (
            db.query(ConversationLog)
            .filter(ConversationLog.complaint_id == payload.complaint_id)
            .order_by(ConversationLog.timestamp.asc())
            .all()
        )
        if not conversation:
            raise HTTPException(status_code=400, detail="No conversation logs found for this complaint")

        conversation_text = "\n".join(f"{msg.speaker}: {msg.message}" for msg in conversation)
        prompt = (
            "Summarize this complaint with issue, priority, language, and sentiment.\n"
            f"Conversation:\n{conversation_text}"
        )

        try:
            llm_result = process_query(prompt)
            summary = (
                (llm_result.get("response_text") or llm_result.get("response") or "").strip()
            )
        except Exception:
            summary = ""

        if not summary:
            summary = conversation_text[:500]

        complaint.summary = summary
        _log_action(db, complaint.id, "summary_generated", "AI")
        db.commit()
        return {"summary": summary}
    finally:
        db.close()


@router.get("/complaint/{id}", response_model=ComplaintViewResponse)
def get_complaint(id: int) -> ComplaintViewResponse:
    db = SessionLocal()
    try:
        complaint = db.query(Complaint).filter(Complaint.id == id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        conversation = (
            db.query(ConversationLog)
            .filter(ConversationLog.complaint_id == id)
            .order_by(ConversationLog.timestamp.asc())
            .all()
        )
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.complaint_id == id)
            .order_by(AuditLog.timestamp.asc())
            .all()
        )

        return {
            "complaint": {
                "id": complaint.id,
                "phone": complaint.phone,
                "issue_text": complaint.issue_text,
                "summary": complaint.summary,
                "language": complaint.language,
                "sentiment": complaint.sentiment,
                "priority": complaint.priority,
                "status": complaint.status,
                "assigned_to": complaint.assigned_to,
                "location": complaint.location,
                "expected_resolution": _to_iso(complaint.expected_resolution),
                "created_at": _to_iso(complaint.created_at),
            },
            "conversation": [
                {
                    "id": msg.id,
                    "complaint_id": msg.complaint_id,
                    "speaker": msg.speaker,
                    "message": msg.message,
                    "timestamp": _to_iso(msg.timestamp),
                }
                for msg in conversation
            ],
            "audit": [
                {
                    "id": log.id,
                    "complaint_id": log.complaint_id,
                    "action": log.action,
                    "actor": log.actor,
                    "timestamp": _to_iso(log.timestamp),
                }
                for log in audit
            ],
        }
    finally:
        db.close()