from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ComplaintQueryRequest(BaseModel):
    query: str


class ComplaintQueryResponse(BaseModel):
    message: str
    response: dict[str, Any]


class CallTurnResponse(BaseModel):
    success: bool
    transcript: str
    agent_text: str
    audio_base64: str
    complaint_id: int
    department: str
    call_id: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# NEW: Simplified routing API (user only provides transcript)
# ═══════════════════════════════════════════════════════════════════════════════


class SimpleRouterRequest(BaseModel):
    """User only provides: session_id and transcript.
    Everything else (language, intent, department) is auto-detected."""
    session_id: str = "auto"  # Can be auto-generated if not provided
    transcript: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "call-001",
                "transcript": "Water is leaking from my tap"
            }
        }


class DepartmentRoutingInfo(BaseModel):
    """Department routing information."""
    dept_id: str
    dept_name: str
    priority: int  # 1-5, where 5 is most urgent


class SimpleRouterResponse(BaseModel):
    """System returns: detected language, intent, department, and action."""
    session_id: str
    transcript: str
    language: str  # Auto-detected: "hi", "en", "ta", etc.
    intent: str  # NEW_COMPLAINT, STATUS_QUERY, FEEDBACK, ABUSE, OTHER
    issue_category: str  # Water, Electricity, Road, Waste, Health, Education, General
    department: DepartmentRoutingInfo
    urgency: int  # 1-5
    is_emergency: bool
    action: str  # CREATE_TICKET, REPROMPT_USER, DISCONNECT, TRANSFER_HUMAN
    summary: str
    confidence: float  # 0.0-1.0: lower if conflicting signals (emergency + prank)
    processing_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "call-001",
                "transcript": "Water is leaking from my tap",
                "language": "en",
                "intent": "NEW_COMPLAINT",
                "issue_category": "Water",
                "department": {
                    "dept_id": "DEPT_WATER_001",
                    "dept_name": "Water & Sewerage",
                    "priority": 3
                },
                "urgency": 3,
                "is_emergency": False,
                "action": "CREATE_TICKET",
                "summary": "Water is leaking from tap",
                "processing_time_ms": 342.5
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SMS/Ticket Integration Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class SendTicketSMSRequest(BaseModel):
    to: str
    custom_text: str
    id: Optional[int] = None
    ticket_id: str
    qr_link: Optional[str] = None
    issue: Optional[str] = None
    location: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    session_id: Optional[str] = None
    include_qr_image: bool = False
    dry_run: bool = False


class SendTicketSMSResponse(BaseModel):
    success: bool
    to: str
    ticket_id: str
    body: str
    qr_link: Optional[str] = None
    media_url: Optional[str] = None
    status: str
    sid: Optional[str] = None
    detail: Optional[str] = None