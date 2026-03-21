"""
FastAPI Ticketing State Machine Backend
Minimal implementation for hackathon use
"""
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.database import Base, engine, get_db, init_db
from app.models import Ticket
from app.schemas import (
    TicketCreate,
    TicketResponse,
    TicketListResponse,
    TicketStatusUpdate,
    AnalyticsResponse,
    ErrorResponse
)
from app.utils import (
    generate_ticket_id,
    detect_priority,
    is_valid_transition,
    simulate_sms_notification
)

# Create FastAPI app
app = FastAPI(
    title="Ticketing State Machine API",
    description="Minimal Ticketing system with state machine validation",
    version="1.0.0"
)


@app.on_event("startup")
def startup_event():
    """
    Initialize database on startup
    """
    init_db()
    print("✅ Database initialized")


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Ticketing State Machine API is active"
    }


# ============================================================================
# TICKET CREATION ENDPOINTS
# ============================================================================

@app.post("/ticket/create", response_model=TicketResponse, tags=["Tickets"])
def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new ticket
    
    - **issue**: Description of the issue
    - **location**: Location where the issue occurred
    - **priority**: Optional (LOW, MEDIUM, HIGH). Auto-detected if not provided
    
    Returns:
        Ticket details with auto-generated ticket_id
    """
    # Auto-detect priority if not explicitly set or if default MEDIUM
    if ticket_data.priority == "MEDIUM":
        detected_priority = detect_priority(ticket_data.issue)
        priority = detected_priority
    else:
        priority = ticket_data.priority
    
    # Generate unique ticket ID
    ticket_id = generate_ticket_id()
    
    # Create ticket object
    ticket = Ticket(
        ticket_id=ticket_id,
        issue=ticket_data.issue,
        location=ticket_data.location,
        priority=priority,
        status="OPEN",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Save to database
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    # Simulate SMS notification
    simulate_sms_notification(ticket_id)
    
    return ticket


# ============================================================================
# TICKET RETRIEVAL ENDPOINTS
# ============================================================================

@app.get("/tickets", response_model=TicketListResponse, tags=["Tickets"])
def get_all_tickets(db: Session = Depends(get_db)):
    """
    Retrieve all tickets
    
    Returns:
        List of all tickets with total count
    """
    tickets = db.query(Ticket).all()
    return {
        "tickets": tickets,
        "total_count": len(tickets)
    }


@app.get("/ticket/{ticket_id}", response_model=TicketResponse, tags=["Tickets"])
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a specific ticket by ticket_id
    
    - **ticket_id**: The unique ticket identifier (e.g., TCK1234ABCD)
    
    Returns:
        Ticket details
    """
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    return ticket


# ============================================================================
# TICKET STATUS UPDATE ENDPOINT
# ============================================================================

@app.put("/ticket/{ticket_id}/status", response_model=TicketResponse, tags=["Tickets"])
def update_ticket_status(
    ticket_id: str,
    status_update: TicketStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update ticket status with state machine validation
    
    Valid transitions:
    - OPEN → ASSIGNED
    - ASSIGNED → IN_PROGRESS
    - IN_PROGRESS → RESOLVED
    - RESOLVED → CLOSED or REOPENED
    - REOPENED → IN_PROGRESS
    
    - **ticket_id**: The ticket ID to update
    - **status**: New status to transition to
    
    Returns:
        Updated ticket details
    """
    # Fetch ticket
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    # Validate state transition
    new_status = status_update.status.upper()
    current_status = ticket.status
    
    if not is_valid_transition(current_status, new_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: {current_status} → {new_status}. "
                   f"Valid transitions from {current_status}: {', '.join([s for s in ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'REOPENED', 'CLOSED'] if is_valid_transition(current_status, s)])}"
        )
    
    # Update ticket
    ticket.status = new_status
    ticket.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ticket)
    
    return ticket


# ============================================================================
# ANALYTICS ENDPOINT
# ============================================================================

@app.get("/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
def get_analytics(db: Session = Depends(get_db)):
    """
    Get ticket count grouped by location
    
    Returns:
        Dictionary with location names as keys and ticket counts as values
    """
    # Query tickets grouped by location
    results = db.query(
        Ticket.location,
        func.count(Ticket.id).label("count")
    ).group_by(Ticket.location).all()
    
    # Convert to dictionary
    analytics = {location: count for location, count in results}
    
    return {"analytics": analytics}


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )