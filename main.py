"""
AI-Powered Public Grievance System
FastAPI Backend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import os

# Database Configuration
DATABASE_URL = "postgresql://postgres:password@localhost:5432/grievance_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class TicketDB(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    issue = Column(String(255))
    location = Column(String(255))
    priority = Column(String(50))
    status = Column(String(50), default="Open")
    sla_hours = Column(Integer)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Pydantic Models
class TicketCreate(BaseModel):
    user_input: str

class TicketUpdate(BaseModel):
    status: str

class TicketResponse(BaseModel):
    id: int
    issue: str
    location: str
    priority: str
    status: str
    sla_hours: int
    summary: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class InsightResponse(BaseModel):
    total_tickets: int
    resolved_tickets: int
    pending_tickets: int
    high_priority_count: int
    complaints_by_location: dict
    most_common_issue: str

# FastAPI App
app = FastAPI(title="AI Grievance System")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper Functions
def detect_priority(text: str) -> str:
    """Detect priority based on keywords."""
    text_lower = text.lower()
    high_keywords = ["flood", "fire", "accident", "urgent"]
    medium_keywords = ["water", "electricity"]
    
    for keyword in high_keywords:
        if keyword in text_lower:
            return "HIGH"
    
    for keyword in medium_keywords:
        if keyword in text_lower:
            return "MEDIUM"
    
    return "LOW"

def classify_issue(text: str) -> str:
    """Classify the issue type."""
    text_lower = text.lower()
    
    if "garbage" in text_lower:
        return "waste"
    elif "flood" in text_lower or "water" in text_lower:
        return "flood"
    elif "smoke" in text_lower:
        return "pollution"
    else:
        return "other"

def get_sla_hours(priority: str) -> int:
    """Get SLA hours based on priority."""
    sla_map = {
        "HIGH": 1,
        "MEDIUM": 6,
        "LOW": 24
    }
    return sla_map.get(priority, 24)

def generate_summary(issue: str, location: str, priority: str) -> str:
    """Generate a summary of the ticket."""
    issue_class = classify_issue(issue)
    return f"Complaint about {issue_class} issue at {location} reported with {priority} priority. Details: {issue[:100]}..."

def extract_location(text: str) -> str:
    """Extract location from user input (simple heuristic)."""
    words = text.split()
    # Try to find location-like words
    location_keywords = ["at", "in", "near", "around", "location", "address"]
    
    for i, word in enumerate(words):
        if word.lower() in location_keywords and i + 1 < len(words):
            return " ".join(words[i+1:i+3])
    
    # Default to last few words
    return " ".join(words[-2:]) if len(words) >= 2 else "Unknown Location"

# API Endpoints
@app.post("/create-ticket", response_model=TicketResponse)
def create_ticket(ticket_create: TicketCreate, db: Session = None):
    """Create a new ticket from user input."""
    if db is None:
        db = SessionLocal()
    
    try:
        user_input = ticket_create.user_input
        
        # Extract information
        priority = detect_priority(user_input)
        issue = classify_issue(user_input)
        location = extract_location(user_input)
        sla_hours = get_sla_hours(priority)
        summary = generate_summary(user_input, location, priority)
        
        # Create ticket
        db_ticket = TicketDB(
            issue=issue,
            location=location,
            priority=priority,
            status="Open",
            sla_hours=sla_hours,
            summary=summary,
            created_at=datetime.utcnow()
        )
        
        db.add(db_ticket)
        db.commit()
        db.refresh(db_ticket)
        
        return TicketResponse.model_validate(db_ticket)
    finally:
        db.close()

@app.get("/tickets", response_model=List[TicketResponse])
def get_tickets(db: Session = None):
    """Retrieve all tickets."""
    if db is None:
        db = SessionLocal()
    
    try:
        tickets = db.query(TicketDB).all()
        return [TicketResponse.model_validate(t) for t in tickets]
    finally:
        db.close()

@app.put("/update-status/{ticket_id}", response_model=TicketResponse)
def update_status(ticket_id: int, update: TicketUpdate, db: Session = None):
    """Update ticket status."""
    if db is None:
        db = SessionLocal()
    
    try:
        ticket = db.query(TicketDB).filter(TicketDB.id == ticket_id).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        valid_statuses = ["Open", "In Progress", "Resolved"]
        if update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        ticket.status = update.status
        db.commit()
        db.refresh(ticket)
        
        return TicketResponse.model_validate(ticket)
    finally:
        db.close()

@app.get("/insights", response_model=InsightResponse)
def get_insights(db: Session = None):
    """Generate insights from tickets."""
    if db is None:
        db = SessionLocal()
    
    try:
        tickets = db.query(TicketDB).all()
        
        total = len(tickets)
        resolved = len([t for t in tickets if t.status == "Resolved"])
        pending = len([t for t in tickets if t.status != "Resolved"])
        high_priority = len([t for t in tickets if t.priority == "HIGH"])
        
        # Complaints by location
        location_map = {}
        for ticket in tickets:
            location_map[ticket.location] = location_map.get(ticket.location, 0) + 1
        
        # Most common issue
        issue_map = {}
        for ticket in tickets:
            issue_map[ticket.issue] = issue_map.get(ticket.issue, 0) + 1
        
        most_common = max(issue_map, key=issue_map.get) if issue_map else "None"
        
        return InsightResponse(
            total_tickets=total,
            resolved_tickets=resolved,
            pending_tickets=pending,
            high_priority_count=high_priority,
            complaints_by_location=location_map,
            most_common_issue=most_common
        )
    finally:
        db.close()

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
