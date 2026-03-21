"""
SQLAlchemy ORM models for Ticketing System
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class Ticket(Base):
    """
    Ticket model representing a citizen complaint/issue ticket
    
    Status workflow: OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED or REOPENED
    """
    __tablename__ = "tickets"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Unique ticket identifier (e.g., TCK1234)
    ticket_id = Column(String, unique=True, index=True, nullable=False)
    
    # Issue description
    issue = Column(String, nullable=False)
    
    # Location of the issue
    location = Column(String, nullable=False)
    
    # Priority level: LOW, MEDIUM, HIGH
    priority = Column(String, default="MEDIUM", nullable=False)
    
    # Status: OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, REOPENED
    status = Column(String, default="OPEN", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Ticket(ticket_id={self.ticket_id}, status={self.status}, priority={self.priority})>"