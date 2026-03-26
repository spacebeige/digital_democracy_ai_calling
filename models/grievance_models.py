"""
Standardized Data Models for Grievance Processing
================================================
Defines all JSON schemas and data structures for:
- Grievance intake
- NLP analysis  
- Routing decisions
- Analytical metadata
- TTS responses
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import uuid


class UrgencyLevel(Enum):
    """Urgency classification levels."""
    CRITICAL = "CRITICAL"  # Emergency: fire, medical, death threat
    HIGH = "HIGH"  # Serious: theft, electricity/water outage, injury
    MEDIUM = "MEDIUM"  # Moderate: infrastructure damage, missing items
    LOW = "LOW"  # General: suggestions, information requests


class EmotionState(Enum):
    """Detected emotional states from voice."""
    ANGRY = "ANGRY"
    FRUSTRATED = "FRUSTRATED"
    NEUTRAL = "NEUTRAL"
    ANXIOUS = "ANXIOUS"
    CALM = "CALM"


class ConfidenceMetric:
    """Computed confidence using multiple factors."""
    
    @staticmethod
    def calculate(
        keyword_match: float,  # 0-1: keyword presence
        urgency_consistency: float,  # 0-1: how consistent keywords are
        pattern_match: float,  # 0-1: how well matches known patterns
        emotion_alignment: float,  # 0-1: emotion matches urgency
    ) -> tuple[float, str]:
        """
        Calculate confidence score (0-4) with reasoning.
        
        Args:
            keyword_match: 0-1 score for keyword presence
            urgency_consistency: 0-1 score for pattern consistency
            pattern_match: 0-1 score for known pattern match
            emotion_alignment: 0-1 score for emotion-urgency alignment
            
        Returns:
            (score: 0-4, reason: explanation)
        """
        # Weighted average: keywords (0.3) + consistency (0.25) + pattern (0.25) + emotion (0.2)
        weighted = (keyword_match * 0.3 + 
                   urgency_consistency * 0.25 + 
                   pattern_match * 0.25 + 
                   emotion_alignment * 0.2)
        
        score = int(weighted * 4)  # Convert to 0-4 scale
        score = max(0, min(4, score))  # Clamp to 0-4
        
        reasons = []
        if keyword_match > 0.7:
            reasons.append("strong keyword match")
        if urgency_consistency > 0.7:
            reasons.append("consistent patterns")
        if pattern_match > 0.8:
            reasons.append("matches known issue")
        if emotion_alignment > 0.7:
            reasons.append("emotion aligns with urgency")
            
        reason = ", ".join(reasons) if reasons else "limited evidence"
        return score, reason


@dataclass
class EmotionAnalysis:
    """Voice emotion analysis results."""
    detected_emotion: EmotionState
    anger_score: float  # 0-1: likelihood of anger
    frustration_score: float  # 0-1: frustration level
    stress_level: float  # 0-1: overall stress
    tone_changes: int  # Number of tone shifts detected
    speech_rate_abnormal: bool  # Is speech rate unusual?
    reasoning: str  # Explanation of emotion detection


@dataclass
class IntentClassification:
    """Intent and urgency classification."""
    primary_intent: str  # e.g., "report_fire", "request_water", "complaint_electricity"
    secondary_intents: List[str] = field(default_factory=list)
    urgency_level: UrgencyLevel = UrgencyLevel.LOW
    urgency_score: int = 0  # 0-4 based on keywords and patterns
    confidence: int = 0  # 0-4: confidence in classification
    confidence_reason: str = ""
    matched_keywords: List[str] = field(default_factory=list)


@dataclass
class GovServiceMapping:
    """Maps grievance to Indian government services."""
    service_type: str  # e.g., "electricity", "water", "fire", "police"
    service_name: str  # e.g., "Maharashtra State Electricity Distribution"
    department_code: str  # e.g., "AES", "JDVN", "FD"
    contact_method: str  # e.g., "phone", "sms", "email", "portal"
    contact_info: str  # Phone number, email, portal URL
    priority: int  # 1-5: routing priority (1=highest)
    sla_minutes: int  # Service level agreement response time
    regional_office: Optional[str] = None
    handling_team: Optional[str] = None


@dataclass
class RoutingDecision:
    """Intelligent routing decision."""
    primary_department: str  # e.g., "fire", "electricity", "water"
    mapped_service: Optional[GovServiceMapping] = None
    has_gov_service_match: bool = False
    priority_level: int = 4  # 1-5: internal priority
    reason: str = ""


@dataclass
class VADAnalysis:
    """Voice Activity Detection and speech pattern analysis."""
    speech_segments: int  # Number of distinct speech segments
    total_speech_duration: float  # Seconds of actual speech
    total_silence_duration: float  # Seconds of silence
    longest_utterance: float  # Longest continuous speech
    speech_intensity_peaks: List[float] = field(default_factory=list)  # Decibel spikes
    pause_patterns: str = ""  # "normal", "hesitant", "rapid"


@dataclass
class TranscriptionMetadata:
    """STT metadata and quality metrics."""
    engine_used: str  # "groq_whisper", "faster_whisper", "google_cloud"
    language_detected: str  # ISO 639-1 code
    language_confidence: float  # 0-1
    transcript_quality: str  # "excellent", "good", "fair", "poor"
    transcription_corrections: List[str] = field(default_factory=list)


@dataclass
class AnalyticalModel:
    """Middle-layer analytical model combining all insights."""
    session_id: str
    timestamp: datetime
    
    # Input metadata
    transcription: TranscriptionMetadata
    vad_analysis: VADAnalysis
    emotion: EmotionAnalysis
    
    # Analysis results
    intent: IntentClassification
    routing: RoutingDecision
    
    # AI Summary
    ai_summary: str  # Short overview of grievance
    issue_category: str  # Main issue type
    severity_flags: List[str] = field(default_factory=list)  # Special handling flags
    follow_up_needed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        
        # Convert Enum values to strings
        if isinstance(data.get('emotion'), dict) and 'detected_emotion' in data['emotion']:
            data['emotion']['detected_emotion'] = data['emotion']['detected_emotion'].value
        if isinstance(data.get('intent'), dict) and 'urgency_level' in data['intent']:
            data['intent']['urgency_level'] = data['intent']['urgency_level'].value
            
        # Convert datetime to ISO format
        data['timestamp'] = self.timestamp.isoformat()
        
        return data


@dataclass
class GrievanceResponse:
    """Complete grievance processing response."""
    session_id: str
    timestamp: datetime
    
    # Input
    original_transcript: str
    language: str
    duration_seconds: float
    
    # Analysis
    analytical_model: AnalyticalModel
    
    # Output
    response_text: str  # Text to be read to user
    response_audio_file: Optional[str] = None
    action_taken: str = ""
    ticket_number: Optional[str] = None
    
    # Quality metrics
    processing_time_ms: float = 0.0
    quality_score: float = 0.0  # 0-1: overall response quality
    
    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "input": {
                "transcript": self.original_transcript,
                "language": self.language,
                "duration_seconds": self.duration_seconds,
            },
            "analysis": self.analytical_model.to_dict(),
            "response": {
                "text": self.response_text,
                "audio_file": self.response_audio_file,
                "action": self.action_taken,
                "ticket_number": self.ticket_number,
            },
            "quality": {
                "processing_time_ms": self.processing_time_ms,
                "quality_score": self.quality_score,
            },
        }
    
    def save_to_json(self, output_dir: str = "outputs/json_results") -> str:
        """Save response to JSON file."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{output_dir}/grievance_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_json_dict(), f, indent=2, ensure_ascii=False)
        return filename


def create_session_id() -> str:
    """Generate unique session ID."""
    return str(uuid.uuid4())[:13]
