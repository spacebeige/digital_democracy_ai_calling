from typing import Any, Optional

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


class SendTicketSMSRequest(BaseModel):
    to: str
    custom_text: str
    id: Optional[int] = None
    ticket_id: str
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
    media_url: Optional[str] = None
    status: str
    sid: Optional[str] = None
    detail: Optional[str] = None