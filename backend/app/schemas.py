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


class CreateComplaintRequest(BaseModel):
    phone: Optional[str] = None
    issue_text: str
    summary: Optional[str] = None
    language: Optional[str] = None
    sentiment: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
    status: Optional[str] = "OPEN"
    assigned_to: Optional[str] = None
    location: Optional[str] = None
    expected_resolution: Optional[str] = None


class CreateComplaintResponse(BaseModel):
    complaint_id: int


class ConversationLogRequest(BaseModel):
    complaint_id: int
    speaker: str
    message: str


class ConversationLogResponse(BaseModel):
    status: str


class GenerateSummaryRequest(BaseModel):
    complaint_id: int


class GenerateSummaryResponse(BaseModel):
    summary: str


class ComplaintData(BaseModel):
    id: int
    phone: Optional[str] = None
    issue_text: Optional[str] = None
    summary: Optional[str] = None
    language: Optional[str] = None
    sentiment: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    location: Optional[str] = None
    expected_resolution: Optional[str] = None
    created_at: Optional[str] = None


class ConversationData(BaseModel):
    id: int
    complaint_id: int
    speaker: str
    message: str
    timestamp: str


class AuditData(BaseModel):
    id: int
    complaint_id: int
    action: str
    actor: str
    timestamp: str


class ComplaintViewResponse(BaseModel):
    complaint: ComplaintData
    conversation: list[ConversationData]
    audit: list[AuditData]