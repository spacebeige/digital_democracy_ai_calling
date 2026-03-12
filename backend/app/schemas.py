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