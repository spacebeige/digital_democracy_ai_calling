from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from datetime import datetime
from app.database import Base

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=True)
    phone_number = Column(String, nullable=True)
    issue = Column(Text)  # Changed to Text for longer complaints
    department = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Enhanced fields
    language = Column(String, nullable=True)
    urgency = Column(String, nullable=True)  # CRITICAL, HIGH, MEDIUM, LOW
    urgency_score = Column(Float, nullable=True)
    emotion = Column(String, nullable=True)  # angry, frustrated, neutral, satisfied
    summary = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # Water, Electricity, etc.
    state_code = Column(String, nullable=True)  # MH, DL, etc.
    vulgarity_detected = Column(Boolean, default=False)
    warning_count = Column(Integer, default=0)
    affected_area = Column(String, nullable=True)
    response_time = Column(String, nullable=True)  # e.g., "within 4 hours"