from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from datetime import datetime
from sqlalchemy.orm import relationship

from app.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String)
    issue_text = Column(Text)
    summary = Column(Text)
    language = Column(String)
    sentiment = Column(String)
    priority = Column(String)
    status = Column(String)
    assigned_to = Column(String)
    location = Column(String)
    expected_resolution = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation_logs = relationship(
        "ConversationLog",
        back_populates="complaint",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="complaint",
        cascade="all, delete-orphan",
    )


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), index=True)
    speaker = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="conversation_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), index=True)
    action = Column(String)
    actor = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="audit_logs")