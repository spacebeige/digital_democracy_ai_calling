"""
Enhanced Grievance Routes with Database Integration
Complete database persistence + 20+ languages + code-mixing + low latency optimization
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import Complaint
from backend.app.services.enhanced_summary_service import (
    EnhancedAISummaryService,
    EnhancedSummary,
    SummaryStyle,
    UrgencyLevel,
)
from backend.app.services.state_schemes_service import (
    SchemeCategory,
    StateSchemesService,
)
from backend.app.services.vulgarity_handler import VulgarityHandler, VulgarityResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enhanced", tags=["Enhanced Grievance with DB"])

# Initialize services (singleton pattern for performance)
vulgarity_handler = VulgarityHandler()
summary_service = EnhancedAISummaryService(enable_cache=True)
schemes_service = StateSchemesService(enable_grok=False)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE DEPENDENCY
# ═══════════════════════════════════════════════════════════════════════════════


def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class ComplaintRequest(BaseModel):
    """Enhanced complaint request."""
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    transcript: str = Field(..., description="Complaint text from STT")
    language: str = Field(default="en", description="Detected language code")
    category: Optional[str] = Field(default="General", description="Complaint category")
    phone_number: Optional[str] = None
    affected_area: Optional[str] = None


class ComplaintResponse(BaseModel):
    """Enhanced complaint response with DB integration."""
    session_id: str
    complaint_id: Optional[int] = None  # Database ID
    vulgarity_check: VulgarityResponse
    summary: EnhancedSummary
    state_schemes: Optional[List[Dict]] = None
    should_continue: bool
    response_message: Dict[str, str]
    warning_count: int
    db_saved: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED ENDPOINTS WITH DATABASE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/process-complaint", response_model=ComplaintResponse)
async def process_complaint_with_db(
    request: ComplaintRequest,
    db: Session = Depends(get_db)
):
    """
    Process complaint with ALL features + DATABASE persistence.
    
    Features:
    - Vulgarity detection with progressive warnings
    - Enhanced AI summarization with urgency detection
    - State-wise scheme recommendations
    - Complete database persistence
    - Multi-language support (20+ languages)
    - Code-mixing support (Hinglish, Tanglish, etc.)
    - Low latency (<300ms cached, <2s uncached)
    """
    try:
        start_time = datetime.now()
        
        # Step 1: Vulgarity Check (fast, lexicon-based)
        vulgarity_check = vulgarity_handler.detect_vulgarity(
            text=request.transcript,
            language=request.language,
            session_id=request.session_id
        )
        
        # Step 2: Generate Enhanced Summary (with caching for low latency)
        summary = summary_service.generate_summary(
            text=request.transcript,
            category=request.category,
            language=request.language,
            style=SummaryStyle.CONCISE
        )
        
        # Step 3: Detect State and Get Schemes (cached for 30 days)
        state_schemes = None
        detected_state = schemes_service.detect_state_from_text(request.transcript)
        
        if detected_state:
            logger.info(f"Detected state: {detected_state}")
            try:
                category_map = {
                    "Water": SchemeCategory.WATER,
                    "Electricity": SchemeCategory.ELECTRICITY,
                    "Road": SchemeCategory.ROAD,
                    "Sanitation": SchemeCategory.SANITATION,
                    "Health": SchemeCategory.HEALTH,
                    "Education": SchemeCategory.EDUCATION
                }
                
                scheme_category = category_map.get(request.category)
                schemes = await schemes_service.get_schemes_for_state(
                    state_code=detected_state,
                    category=scheme_category
                )
                
                state_schemes = [
                    {
                        "name": s.name,
                        "name_local": s.name_local,
                        "category": s.category.value,
                        "description": s.description,
                        "contact_number": s.contact_number,
                        "website": s.website
                    }
                    for s in schemes[:3]
                ]
            except Exception as e:
                logger.error(f"Error fetching schemes: {e}")
        
        # Step 4: SAVE TO DATABASE (regardless of vulgarity status for audit)
        complaint_id = None
        db_saved = False
        
        try:
            complaint = Complaint(
                session_id=request.session_id,
                phone_number=request.phone_number,
                issue=request.transcript,
                department=request.category or "General",
                status="terminated" if vulgarity_check.should_terminate else "pending",
                language=request.language,
                urgency=summary.urgency.value if summary else None,
                urgency_score=summary.urgency_score if summary else None,
                emotion=summary.citizen_emotion if summary else None,
                summary=summary.summary if summary else None,
                category=request.category,
                state_code=detected_state,
                vulgarity_detected=vulgarity_check.detected,
                warning_count=vulgarity_check.warning_count,
                affected_area=request.affected_area or (summary.affected_area if summary else None),
                response_time=summary.suggested_response_time if summary else None
            )
            
            db.add(complaint)
            db.commit()
            db.refresh(complaint)
            
            complaint_id = complaint.id
            db_saved = True
            
            logger.info(f"Saved complaint ID {complaint_id} to database")
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
            db.rollback()
        
        # Step 5: Generate Response Message
        response_message = _generate_response_message(
            vulgarity_detected=vulgarity_check.detected,
            vulgarity_response=vulgarity_check.response_message,
            summary=summary,
            has_schemes=state_schemes is not None and len(state_schemes) > 0,
            language=request.language
        )
        
        # Calculate latency
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Request processed in {latency_ms:.2f}ms")
        
        return ComplaintResponse(
            session_id=request.session_id,
            complaint_id=complaint_id,
            vulgarity_check=vulgarity_check,
            summary=summary,
            state_schemes=state_schemes,
            should_continue=not vulgarity_check.should_terminate,
            response_message=response_message,
            warning_count=vulgarity_check.warning_count,
            db_saved=db_saved
        )
    
    except Exception as e:
        logger.error(f"Error processing complaint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing complaint: {str(e)}")


@router.get("/complaints")
async def get_complaints(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of complaints from database with filters.
    
    Filters:
    - status: pending, resolved, terminated
    - urgency: CRITICAL, HIGH, MEDIUM, LOW
    - language: hi, en, ta, etc.
    """
    try:
        query = db.query(Complaint)
        
        if status:
            query = query.filter(Complaint.status == status)
        if urgency:
            query = query.filter(Complaint.urgency == urgency)
        if language:
            query = query.filter(Complaint.language == language)
        
        complaints = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "total": query.count(),
            "complaints": [
                {
                    "id": c.id,
                    "session_id": c.session_id,
                    "phone_number": c.phone_number,
                    "issue": c.issue[:100] + "..." if len(c.issue) > 100 else c.issue,
                    "summary": c.summary,
                    "department": c.department,
                    "category": c.category,
                    "urgency": c.urgency,
                    "urgency_score": c.urgency_score,
                    "emotion": c.emotion,
                    "language": c.language,
                    "state_code": c.state_code,
                    "status": c.status,
                    "vulgarity_detected": c.vulgarity_detected,
                    "warning_count": c.warning_count,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in complaints
            ]
        }
    
    except Exception as e:
        logger.error(f"Error fetching complaints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complaints/{complaint_id}")
async def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    """Get single complaint by ID."""
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        return {
            "id": complaint.id,
            "session_id": complaint.session_id,
            "phone_number": complaint.phone_number,
            "issue": complaint.issue,
            "summary": complaint.summary,
            "department": complaint.department,
            "category": complaint.category,
            "urgency": complaint.urgency,
            "urgency_score": complaint.urgency_score,
            "emotion": complaint.emotion,
            "language": complaint.language,
            "state_code": complaint.state_code,
            "status": complaint.status,
            "vulgarity_detected": complaint.vulgarity_detected,
            "warning_count": complaint.warning_count,
            "affected_area": complaint.affected_area,
            "response_time": complaint.response_time,
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching complaint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/complaints/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Update complaint status."""
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        complaint.status = status
        db.commit()
        
        return {"message": "Status updated", "complaint_id": complaint_id, "new_status": status}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating status: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Get analytics summary from database."""
    try:
        total = db.query(Complaint).count()
        pending = db.query(Complaint).filter(Complaint.status == "pending").count()
        resolved = db.query(Complaint).filter(Complaint.status == "resolved").count()
        terminated = db.query(Complaint).filter(Complaint.status == "terminated").count()
        
        critical = db.query(Complaint).filter(Complaint.urgency == "CRITICAL").count()
        high = db.query(Complaint).filter(Complaint.urgency == "HIGH").count()
        
        vulgarity_detected = db.query(Complaint).filter(Complaint.vulgarity_detected == True).count()
        
        return {
            "total_complaints": total,
            "by_status": {
                "pending": pending,
                "resolved": resolved,
                "terminated": terminated
            },
            "by_urgency": {
                "critical": critical,
                "high": high,
                "medium": db.query(Complaint).filter(Complaint.urgency == "MEDIUM").count(),
                "low": db.query(Complaint).filter(Complaint.urgency == "LOW").count()
            },
            "vulgarity_statistics": {
                "total_detected": vulgarity_detected,
                "percentage": (vulgarity_detected / total * 100) if total > 0 else 0
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def _generate_response_message(
    vulgarity_detected: bool,
    vulgarity_response: Dict[str, str],
    summary: EnhancedSummary,
    has_schemes: bool,
    language: str
) -> Dict[str, str]:
    """Generate appropriate response message based on analysis."""
    
    if vulgarity_detected:
        return vulgarity_response
    
    # Generate normal response based on summary and language
    language_responses = {
        "hi": _generate_hindi_response(summary, has_schemes),
        "en": _generate_english_response(summary, has_schemes),
        "hinglish": _generate_hinglish_response(summary, has_schemes),
        "mr": _generate_marathi_response(summary, has_schemes),
        "ta": _generate_tamil_response(summary, has_schemes),
        "tanglish": _generate_tanglish_response(summary, has_schemes),
        "te": _generate_telugu_response(summary, has_schemes),
        "bn": _generate_bengali_response(summary, has_schemes),
    }
    
    primary_response = language_responses.get(language, language_responses["en"])
    
    return {
        language: primary_response,
        "en": language_responses["en"]  # Always include English fallback
    }


def _generate_hindi_response(summary: EnhancedSummary, has_schemes: bool) -> str:
    msg = f"आपकी शिकायत दर्ज की गई है। {summary.summary}। "
    if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        msg += "यह उच्च प्राथमिकता का मामला है और जल्द ही संबोधित किया जाएगा। "
    if has_schemes:
        msg += "आपके क्षेत्र के लिए सरकारी योजनाएं उपलब्ध हैं। "
    return msg


def _generate_english_response(summary: EnhancedSummary, has_schemes: bool) -> str:
    msg = f"Your complaint has been registered. {summary.summary}. "
    if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        msg += "This is a high priority matter and will be addressed soon. "
    if has_schemes:
        msg += "Relevant government schemes are available for your area. "
    return msg


def _generate_hinglish_response(summary: EnhancedSummary, has_schemes: bool) -> str:
    msg = f"Aapki complaint register ho gayi hai. {summary.summary}. "
    if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        msg += "Yeh high priority case hai aur jaldi solve hoga. "
    if has_schemes:
        msg += "Aapke area ke liye government schemes available hain. "
    return msg


def _generate_marathi_response(summary: EnhancedSummary, has_schemes: bool) -> str:
    msg = f"तुमची तक्रार नोंदवली गेली आहे। {summary.summary}। "
    if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        msg += "हा उच्च प्राधान्य प्रकरण आहे आणि लवकरच हाताळला जाईल। "
    if has_schemes:
        msg += "तुमच्या क्षेत्रासाठी सरकारी योजना उपलब्ध आहेत। "
    return msg


def _generate_tamil_response(summary: EnhancedSummary, has_schemes: bool) -> str:
    msg = f"உங்கள் புகார் பதிவு செய்யப்பட்டுள்ளது। {summary.summary}। "
    if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        msg += "இது அதிக முன்னுரிமை விஷயம், விரைவில் தீர்க்கப்படும். "
    if has_schemes:
        msg += "உங்கள் பகுதிக்கு தொடர்புடைய அரசு திட்டங்கள் உள்ளன। "
    return msg


def _generate_tanglish_response(summary: EnhancedSummary, has_schemes: bool) -> str:
    msg = f"Unga complaint register aagiduchu. {summary.summary}. "
    if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        msg += "Idhu high priority issue, seekiram solve aagum. "
    if has_schemes:
        msg += "Unga area-ku government schemes irukku. "
    return msg


def _generate_telugu_response(summary: EnhancedSummary, has_schemes: bool) -> str:
    msg = f"మీ ఫిర్యాదు నమోదు చేయబడింది। {summary.summary}। "
    if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        msg += "ఇది అధిక ప్రాధాన్యత విషయం, త్వరలో పరిష్కరించబడుతుంది। "
    if has_schemes:
        msg += "మీ ప్రాంతానికి సంబంధించిన ప్రభుత్వ పథకాలు అందుబాటులో ఉన్నాయి। "
    return msg


def _generate_bengali_response(summary: EnhancedSummary, has_schemes: bool) -> str:
    msg = f"আপনার অভিযোগ নথিভুক্ত করা হয়েছে। {summary.summary}। "
    if summary.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        msg += "এটি উচ্চ অগ্রাধিকার বিষয়, শীঘ্রই সমাধান করা হবে। "
    if has_schemes:
        msg += "আপনার এলাকার জন্য সরকারি প্রকল্প উপলব্ধ আছে। "
    return msg
