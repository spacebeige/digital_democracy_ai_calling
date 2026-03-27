"""
Analytical Model Module - Middle Layer Orchestrator
===================================================
Brings together all analysis components:
- NLP routing & intent classification
- Emotion analysis
- Confidence scoring
- Routing decision
- AI summary generation
- Response generation
"""

from datetime import datetime
from typing import Optional, Tuple, List
import numpy as np
import logging
import os

# Groq initialization with fallback for version incompatibility
try:
    from groq import Groq
    GROQ_LIBRARY_AVAILABLE = True
except ImportError:
    GROQ_LIBRARY_AVAILABLE = False
    Groq = None

from models.grievance_models import (
    AnalyticalModel,
    TranscriptionMetadata,
    VADAnalysis,
    IntentClassification,
    RoutingDecision,
    EmotionAnalysis,
    UrgencyLevel,
)
from core.nlp_routing import (
    classify_urgency,
    classify_intent,
    create_ai_summary,
)
from core.emotion_detection import analyze_emotions
from external_services.gov_services_map import (
    detect_service_type,
    get_service_mapping,
    SERVICE_KEYWORDS,
)
from routing.route_dispatcher import RouteDispatcher
from routing.escalation_engine import EscalationEngine
from outputs.json_storage_manager import JSONStorageManager

logger = logging.getLogger(__name__)


class AnalyticalModelProcessor:
    """Main processor for grievance analysis with intelligent routing and escalation."""
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize with optional Groq API for AI summaries."""
        self.groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        self.groq_client = None
        self.groq_available = False
        
        # Try to initialize Groq with error handling for version incompatibility
        if self.groq_api_key and GROQ_LIBRARY_AVAILABLE and Groq is not None:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                self.groq_available = True
                logger.info("✅ Groq client initialized for AI-powered intent analysis")
            except TypeError as e:
                # Version mismatch with proxies parameter - fallback to basic analysis
                logger.warning(f"⚠️ Groq initialization failed (version issue): {e}")
                logger.info("   Falling back to rule-based intent classification")
                self.groq_available = False
            except Exception as e:
                logger.warning(f"⚠️ Groq initialization error: {e}")
                self.groq_available = False
        
        # Initialize routing components
        self.route_dispatcher = RouteDispatcher()
        self.escalation_engine = EscalationEngine()
        
        # Initialize JSON storage manager
        self.json_storage = JSONStorageManager(base_output_dir="outputs/json_results")
        
        logger.info("✅ AnalyticalModelProcessor initialized with routing + escalation engines")
    
    def process_grievance(
        self,
        session_id: str,
        transcript: str,
        audio_data: np.ndarray,
        sample_rate: int,
        detected_language: str = "en",
        state: str = "maharashtra",
    ) -> AnalyticalModel:
        """
        Process complete grievance and generate analytical model.
        
        Args:
            session_id: Unique session identifier
            transcript: User's complaint text
            audio_data: Audio samples for emotion analysis
            sample_rate: Audio sample rate (Hz)
            detected_language: ISO language code
            state: State/region for service mapping
            
        Returns:
            AnalyticalModel with all analysis results
        """
        timestamp = datetime.utcnow()
        
        # ─────────────────────────────────────────────────────────────
        # 1. TRANSCRIPTION METADATA
        # ─────────────────────────────────────────────────────────────
        transcription_metadata = TranscriptionMetadata(
            engine_used="groq_whisper",  # Detected from STT service
            language_detected=detected_language,
            language_confidence=0.95,  # Example confidence
            transcript_quality=self._assess_transcript_quality(transcript),
            transcription_corrections=[],
        )
        
        # ─────────────────────────────────────────────────────────────
        # 2. VAD ANALYSIS
        # ─────────────────────────────────────────────────────────────
        vad_analysis = self._analyze_vad(audio_data, sample_rate)
        
        # ─────────────────────────────────────────────────────────────
        # 3. EMOTION ANALYSIS
        # ─────────────────────────────────────────────────────────────
        emotion_analysis = analyze_emotions(audio_data, sample_rate, len(transcript.split()))
        
        # ─────────────────────────────────────────────────────────────
        # 4. NLP ROUTING & INTENT CLASSIFICATION
        # ─────────────────────────────────────────────────────────────
        
        # Step 1: Classify urgency
        urgency_level, matched_keywords, urgency_confidence = classify_urgency(
            transcript,
            emotion_score=emotion_analysis.stress_level,
        )
        
        # Step 2: Classify intent with confidence metrics
        intent = classify_intent(
            transcript,
            urgency_level,
            matched_keywords,
            detected_language,
        )
        
        # ─────────────────────────────────────────────────────────────
        # 5. ROUTING DECISION WITH GOV SERVICE MAPPING
        # ─────────────────────────────────────────────────────────────
        
        # Detect service type
        service_type, service_keywords, may_escalate = detect_service_type(
            transcript,
            matched_keywords,
            intent.primary_intent,
        )
        
        # Get government service mapping
        gov_service = get_service_mapping(service_type, state, detected_language)
        
        # Determine routing priority
        priority = {
            UrgencyLevel.CRITICAL: 1,
            UrgencyLevel.HIGH: 2,
            UrgencyLevel.MEDIUM: 3,
            UrgencyLevel.LOW: 4,
        }.get(urgency_level, 4)
        
        # Build routing decision
        routing = RoutingDecision(
            primary_department=service_type,
            mapped_service=gov_service,
            has_gov_service_match=gov_service is not None,
            priority_level=priority,
            reason=self._build_routing_reason(
                intent.primary_intent,
                matched_keywords,
                urgency_level,
            ),
        )
        
        # ─────────────────────────────────────────────────────────────
        # 6. AI SUMMARY & ISSUE CATEGORIZATION
        # ─────────────────────────────────────────────────────────────
        
        ai_summary = create_ai_summary(
            transcript,
            intent,
            matched_keywords,
            urgency_level,
        )
        
        # Enhance summary with Groq if available
        if self.groq_available and self.groq_client:
            ai_summary = self._enhance_summary_with_groq(
                transcript,
                intent,
                matched_keywords,
                urgency_level,
            )
        
        issue_category = self._categorize_issue(service_type, matched_keywords)
        
        # ─────────────────────────────────────────────────────────────
        # 7. SEVERITY FLAGS
        # ─────────────────────────────────────────────────────────────
        
        severity_flags = []
        
        if urgency_level == UrgencyLevel.CRITICAL:
            severity_flags.append("EMERGENCY_ESCALATE")
        
        if emotion_analysis.anger_score > 0.7:
            severity_flags.append("ANGRY_CUSTOMER")
        
        if emotion_analysis.stress_level > 0.8:
            severity_flags.append("HIGH_STRESS")
        
        if may_escalate:
            severity_flags.append("POSSIBLE_ESCALATION_NEEDED")
        
        if len(matched_keywords) == 0:
            severity_flags.append("LOW_CONFIDENCE_CLASSIFICATION")
        
        follow_up_needed = (
            urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH] or
            emotion_analysis.anger_score > 0.6 or
            intent.confidence < 2
        )
        
        # ─────────────────────────────────────────────────────────────
        # 8. BUILD ANALYTICAL MODEL
        # ─────────────────────────────────────────────────────────────
        
        analytical_model = AnalyticalModel(
            session_id=session_id,
            timestamp=timestamp,
            transcription=transcription_metadata,
            vad_analysis=vad_analysis,
            emotion=emotion_analysis,
            intent=intent,
            routing=routing,
            ai_summary=ai_summary,
            issue_category=issue_category,
            severity_flags=severity_flags,
            follow_up_needed=follow_up_needed,
        )
        
        return analytical_model
    
    def apply_routing_and_escalation(
        self,
        analytical_model: AnalyticalModel,
        transcript: str = "",
        time_since_filing_minutes: int = 0,
        num_previous_calls: int = 0,
    ) -> Tuple[AnalyticalModel, dict]:
        """
        Apply intelligent routing and check for automatic escalation.
        
        Args:
            analytical_model: Analyzed grievance model
            transcript: Original complaint text (for routing)
            time_since_filing_minutes: Minutes since grievance was filed
            num_previous_calls: Number of previous calls for this grievance
            
        Returns:
            Tuple of (updated_analytical_model, escalation_info)
        """
        # Apply intelligent routing
        routing_decision = self.route_dispatcher.dispatch_route(analytical_model, transcript)
        analytical_model.routing = routing_decision
        
        logger.info(f"🚦 Routed to: {routing_decision.primary_department} (Priority: P{routing_decision.priority_level})")
        
        # Check for automatic escalation
        triggered_escalations = self.escalation_engine.check_escalation(
            analytical_model,
            time_since_filing_minutes=time_since_filing_minutes,
            num_previous_calls=num_previous_calls
        )
        
        escalation_info = {
            "should_escalate": len(triggered_escalations) > 0,
            "triggered_rules": [e.trigger_name for e in triggered_escalations],
            "escalation_details": [
                {
                    "trigger": e.trigger_name,
                    "condition": e.trigger_condition,
                    "from_level": e.from_level,
                    "to_level": e.to_level,
                    "timeframe_minutes": e.timeframe_minutes,
                    "action": e.action_required,
                    "reason": e.reason,
                }
                for e in triggered_escalations
            ],
        }
        
        if triggered_escalations:
            analytical_model.severity_flags.append("AUTO_ESCALATION_TRIGGERED")
            logger.warning(f"⚠️ ESCALATION TRIGGERED: {escalation_info['triggered_rules']}")
        
        return analytical_model, escalation_info
    
    def save_result_organized(
        self,
        analytical_model: AnalyticalModel,
        escalation_info: Optional[dict] = None,
        extra_data: Optional[dict] = None,
    ) -> dict:
        """
        Save grievance result to organized folder structure.
        
        Saves to:
        - outputs/json_results/by_urgency/{level}/
        - outputs/json_results/by_department/{dept}/
        - outputs/json_results/by_date/{YYYY-MM-DD}/
        
        Args:
            analytical_model: Analyzed and routed grievance
            escalation_info: Escalation decision information
            extra_data: Additional data like ticket_number, state, etc.
            
        Returns:
            Dictionary with file paths where result was saved
        """
        # Build complete result document
        result_doc = {
            "session_id": analytical_model.session_id,
            "timestamp": analytical_model.timestamp.isoformat(),
            "type": "grievance_analysis",
            
            # Analysis results
            "transcription": {
                "engine_used": analytical_model.transcription.engine_used,
                "language_detected": analytical_model.transcription.language_detected,
                "language_confidence": analytical_model.transcription.language_confidence,
                "transcript_quality": analytical_model.transcription.transcript_quality,
            },
            
            "emotion": {
                "state": analytical_model.emotion.detected_emotion.name,
                "anger_score": analytical_model.emotion.anger_score,
                "frustration_score": analytical_model.emotion.frustration_score,
                "stress_level": analytical_model.emotion.stress_level,
            },
            
            "intent": {
                "primary_intent": analytical_model.intent.primary_intent,
                "secondary_intents": analytical_model.intent.secondary_intents,
                "urgency": analytical_model.intent.urgency_level.name if analytical_model.intent.urgency_level else "UNKNOWN",
            },
            
            "urgency_level": {
                "level": analytical_model.intent.urgency_level.name if analytical_model.intent.urgency_level else "UNKNOWN",
                "priority": analytical_model.routing.priority_level,
            },
            
            # Routing & escalation
            "routing": {
                "department": analytical_model.routing.primary_department,
                "service_name": analytical_model.routing.mapped_service.service_name if analytical_model.routing.mapped_service else "N/A",
                "contact_info": analytical_model.routing.mapped_service.contact_info if analytical_model.routing.mapped_service else "N/A",
                "phone": getattr(analytical_model.routing.mapped_service, 'contact_info', "N/A") if analytical_model.routing.mapped_service else "N/A",
                "confidence": getattr(analytical_model.routing, 'confidence', 0.8),
                "reasoning": analytical_model.routing.reason,
            },
            
            "escalation": escalation_info or {"should_escalate": False, "triggered_rules": []},
            
            # Summary & flags
            "ai_summary": analytical_model.ai_summary,
            "issue_category": analytical_model.issue_category,
            "severity_flags": analytical_model.severity_flags,
            "follow_up_needed": analytical_model.follow_up_needed,
        }
        
        # Add extra data if provided (ticket_number, state, etc.)
        if extra_data:
            result_doc["ticket"] = {
                "number": extra_data.get("ticket_number"),
                "state_code": extra_data.get("state_code"),
                "state_service": extra_data.get("state_service"),
                "is_scheme_enquiry": extra_data.get("is_scheme_enquiry", False),
            }
            result_doc["sentiment"] = {
                "frustration_level": extra_data.get("frustration_level", 0),
                "aggressiveness_score": extra_data.get("aggressiveness_score", 0),
            }
            if extra_data.get("ai_response"):
                result_doc["ai_response"] = extra_data.get("ai_response")
        
        # Determine urgency level for folder organization
        urgency_str = analytical_model.intent.urgency_level.name if analytical_model.intent.urgency_level else "MEDIUM"
        
        # Save to organized folders
        saved_paths = self.json_storage.save_result(
            session_id=analytical_model.session_id,
            result=result_doc,
            urgency_level=urgency_str,
            department=analytical_model.routing.primary_department,
            timestamp=analytical_model.timestamp,
        )
        
        logger.info(f"✅ Saved result for {analytical_model.session_id} to organized folders")
        return saved_paths
    
    def _assess_transcript_quality(self, transcript: str) -> str:
        """Assess quality of transcription."""
        if not transcript or len(transcript) < 10:
            return "poor"
        elif len(transcript.split()) < 5:
            return "fair"
        elif any(word in transcript.lower() for word in ["[unintelligible]", "..."]):
            return "fair"
        else:
            return "good"
    
    def _analyze_vad(self, audio_data: np.ndarray, sample_rate: int) -> VADAnalysis:
        """Analyze voice activity (speech patterns)."""
        # Simple energy-based analysis
        frame_size = sample_rate // 50  # 20ms frames
        energy = []
        
        for i in range(0, len(audio_data) - frame_size, frame_size):
            frame = audio_data[i:i+frame_size]
            energy.append(np.sqrt(np.mean(frame ** 2)))
        
        energy = np.array(energy)
        threshold = np.mean(energy) * 0.2
        
        # Count speech vs silence
        speech_frames = np.sum(energy > threshold)
        silence_frames = np.sum(energy <= threshold)
        
        total_duration = len(audio_data) / sample_rate
        speech_duration = (speech_frames / len(energy)) * total_duration if len(energy) > 0 else 0
        pause_duration = (silence_frames / len(energy)) * total_duration if len(energy) > 0 else 0
        
        # Count pause segments
        speech_mask = (energy > threshold).astype(int)
        pause_segments = np.sum(np.diff(speech_mask) == -1)
        
        # Find longest utterance
        max_speech_duration = 0
        current_duration = 0
        for is_speech in speech_mask:
            if is_speech:
                current_duration += 1
            else:
                max_speech_duration = max(max_speech_duration, current_duration)
                current_duration = 0
        
        longest_utterance = (max_speech_duration / (sample_rate / frame_size)) if (sample_rate / frame_size) > 0 else 0
        
        # Determine pause pattern
        if pause_segments == 0:
            pause_pattern = "continuous"
        elif pause_segments > 10:
            pause_pattern = "hesitant"
        else:
            pause_pattern = "normal"
        
        # Detect intensity peaks
        intensity_peaks = []
        for i in range(1, len(energy) - 1):
            if energy[i] > energy[i-1] and energy[i] > energy[i+1]:
                intensity_peaks.append(float(energy[i]))
        
        return VADAnalysis(
            speech_segments=pause_segments,
            total_speech_duration=float(speech_duration),
            total_silence_duration=float(pause_duration),
            longest_utterance=float(longest_utterance),
            speech_intensity_peaks=intensity_peaks[:10],  # Top 10 peaks
            pause_patterns=pause_pattern,
        )
    
    def _build_routing_reason(
        self,
        primary_intent: str,
        matched_keywords: List[str],
        urgency_level: UrgencyLevel,
    ) -> str:
        """Build human-readable routing reason."""
        reasons = []
        
        if urgency_level == UrgencyLevel.CRITICAL:
            reasons.append("Critical emergency")
        elif urgency_level == UrgencyLevel.HIGH:
            reasons.append("High urgency")
        
        if matched_keywords:
            keywords_str = ", ".join(matched_keywords[:3])
            reasons.append(f"Keywords: {keywords_str}")
        
        if primary_intent != "general_complaint":
            reasons.append(f"Intent: {primary_intent.replace('_', ' ')}")
        
        return " | ".join(reasons) if reasons else "General complaint"
    
    def _categorize_issue(self, service_type: str, matched_keywords: List[str]) -> str:
        """Categorize main issue for analytics."""
        issue_map = {
            "electricity": "Power/Electricity",
            "water": "Water Supply",
            "fire": "Fire/Emergency",
            "police": "Security/Crime",
            "gas": "Gas/Safety",
            "municipal": "Infrastructure",
            "telecom": "Telecom/Connectivity",
        }
        
        return issue_map.get(service_type, "General Complaint")
    
    def _enhance_summary_with_groq(
        self,
        transcript: str,
        intent: IntentClassification,
        matched_keywords: List[str],
        urgency_level: UrgencyLevel,
    ) -> str:
        """Use Groq LLM to create intelligent summary."""
        if not self.groq_available or not self.groq_client:
            return create_ai_summary(transcript, intent, matched_keywords, urgency_level)
        
        try:
            prompt = f"""Analyze this complaint and provide a brief 1-sentence summary:
            
Complaint: {transcript[:500]}
Intent: {intent.primary_intent}
Keywords: {", ".join(matched_keywords[:5]) if matched_keywords else "None"}
Urgency: {urgency_level.value}

Provide a concise summary that captures the core issue and urgency level."""
            
            message = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                max_tokens=100,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.choices[0].message.content.strip()
        
        except Exception as e:
            logger.warning(f"Groq summary generation failed: {e}")
            # Fallback to basic summary
            return create_ai_summary(transcript, intent, matched_keywords, urgency_level)


def create_processor(use_groq: bool = True) -> AnalyticalModelProcessor:
    """Factory function to create processor with optional Groq."""
    import os
    
    groq_key = os.environ.get("GROQ_API_KEY") if use_groq else None
    return AnalyticalModelProcessor(groq_key)
