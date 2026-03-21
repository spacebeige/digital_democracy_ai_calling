"""
Pydantic schemas for API request/response validation
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class TicketCreate(BaseModel):
    """
    Schema for creating a new ticket
    """
    issue: str
    location: str
    priority: Optional[str] = "MEDIUM"


class TicketStatusUpdate(BaseModel):
    """
    Schema for updating ticket status
    """
    status: str


class TicketResponse(BaseModel):
    """
    Schema for returning ticket details in API responses
    """
    id: int
    ticket_id: str
    issue: str
    location: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """
    Schema for listing multiple tickets
    """
    tickets: list[TicketResponse]
    total_count: int


class AnalyticsResponse(BaseModel):
    """
    Schema for analytics endpoint
    """
    analytics: dict[str, int]


class ErrorResponse(BaseModel):
    """
    Schema for error responses
    """
    error: str
    detail: Optional[str] = None