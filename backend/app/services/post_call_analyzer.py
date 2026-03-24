"""
Post-Call Analysis Pipeline
============================

Processes complete call transcripts AFTER the call ends:
1. Language Detection
2. Intent Classification  
3. Emergency Detection
4. Smart Routing & Department Assignment
5. Structured Output for Storage/Action

Pipeline Flow:
  Full Transcript → NLP Classifier → Smart Router → Analysis Output
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.services.nlp_classifier import (
    NLPClassifier,
    NLPInput,
    LanguageCode,
    IntentType as ClassifierIntentType,
    EdgeCaseType,
)
from app.services.smart_router import SmartRouter, VoiceInput, DEPT_MAPPING, ActionType

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════


class AnalysisStatus(str, Enum):
    """Status of post-call analysis."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ActionRequired(str, Enum):
    """Action to be taken based on analysis."""
    CREATE_TICKET = "CREATE_TICKET"
    TRANSFER_TO_HUMAN = "TRANSFER_TO_HUMAN"
    ESCALATE_EMERGENCY = "ESCALATE_EMERGENCY"
    AUTO_RESOLVE = "AUTO_RESOLVE"
    MARK_PRANK = "MARK_PRANK"
    STORE_FEEDBACK = "STORE_FEEDBACK"
    ARCHIVE_COMPLETE = "ARCHIVE_COMPLETE"


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class CallMetadata(BaseModel):
    """Metadata about the call."""
    call_id: Union[str, UUID] = Field(..., description="Unique call identifier")
    session_id: Union[str, UUID] = Field(..., description="Session ID")
    caller_phone: Optional[str] = Field(None, description="Caller's phone number (optional)")
    call_start_time: datetime = Field(..., description="Call start timestamp")
    call_end_time: datetime = Field(..., description="Call end timestamp")
    call_duration_seconds: float = Field(..., description="Total call duration in seconds")
    recording_path: Optional[str] = Field(None, description="Path to call recording")


class TranscriptSegment(BaseModel):
    """A segment of the transcript (for multi-speaker support)."""
    speaker: str = Field(..., description="Speaker identifier (e.g., 'user', 'ai')")
    text: str = Field(..., description="Segment text")
    start_time: float = Field(..., description="Start time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    confidence: float = Field(default=1.0, description="Transcription confidence (0-1)")


class PostCallAnalysisInput(BaseModel):
    """Input schema for post-call analysis."""
    call_metadata: CallMetadata
    full_transcript: str = Field(..., description="Complete call transcript")
    transcript_segments: Optional[List[TranscriptSegment]] = Field(
        None, description="Optional segmented transcript by speaker"
    )
    detected_language: Optional[str] = Field(
        None, description="Pre-detected language hint"
    )

    @field_validator("full_transcript")
    @classmethod
    def validate_transcript(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Transcript cannot be empty")
        return v.strip()


class ClassificationResult(BaseModel):
    """Result from NLP classification."""
    language: str = Field(..., description="Detected language")
    intent: str = Field(..., description="Classified intent")
    edge_case: str = Field(..., description="Edge case type (EMERGENCY, SILENCE, ABUSE, VALID)")
    confidence: float = Field(..., description="Classification confidence")
    keywords_detected: List[str] = Field(default_factory=list, description="Detected keywords")


class RoutingResult(BaseModel):
    """Result from smart routing."""
    department_id: str = Field(..., description="Routed department ID")
    department_name: str = Field(..., description="Department name")
    issue_category: str = Field(..., description="Issue category")
    routing_confidence: float = Field(..., description="Routing decision confidence")
    suggested_action: ActionRequired = Field(..., description="Suggested action")
    priority_level: str = Field(..., description="Priority (LOW, MEDIUM, HIGH, EMERGENCY)")


class PostCallAnalysisOutput(BaseModel):
    """Complete post-call analysis output."""
    status: AnalysisStatus = Field(..., description="Analysis status")
    analysis_id: str = Field(..., description="Unique analysis ID")
    call_id: Union[str, UUID]
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Classification results
    classification: ClassificationResult
    
    # Routing results
    routing: RoutingResult
    
    # Summary
    summary: str = Field(..., description="1-2 sentence summary of the call")
    
    # Detected entities
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    
    # Flags
    is_emergency: bool = Field(default=False, description="Emergency flag")
    is_abuse: bool = Field(default=False, description="Abuse/profanity detected")
    is_prank: bool = Field(default=False, description="Likely prank call")
    is_genuine_complaint: bool = Field(default=True, description="Genuine complaint flag")
    
    # Metadata
    processing_time_ms: float = Field(..., description="Time taken to process (ms)")
    transcript_length: int = Field(..., description="Number of characters in transcript")
    word_count: int = Field(..., description="Approximate word count")
    
    # Raw outputs for debugging
    raw_nlp_output: Optional[Dict[str, Any]] = Field(None, description="Raw NLP classifier output")
    raw_routing_output: Optional[Dict[str, Any]] = Field(None, description="Raw routing output")


# ═══════════════════════════════════════════════════════════════════════════════
# POST-CALL ANALYZER SERVICE
# ═══════════════════════════════════════════════════════════════════════════════


class PostCallAnalyzer:
    """
    Main service for post-call analysis.
    Orchestrates NLP classification and smart routing.
    """

    def __init__(self):
        """Initialize analyzer with NLP and routing services."""
        self.nlp_classifier = NLPClassifier()
        self.smart_router = SmartRouter()
        logger.info("PostCallAnalyzer initialized")

    async def analyze(
        self, analysis_input: PostCallAnalysisInput
    ) -> PostCallAnalysisOutput:
        """
        Perform complete post-call analysis.
        
        Args:
            analysis_input: PostCallAnalysisInput with call metadata and transcript
            
        Returns:
            PostCallAnalysisOutput with complete analysis
        """
        analysis_id = f"pca_{analysis_input.call_metadata.call_id}_{datetime.utcnow().timestamp()}"
        start_time = datetime.utcnow()

        try:
            logger.info(f"Starting post-call analysis: {analysis_id}")

            # ─────────────────────────────────────────────────────────────────
            # Step 1: NLP Classification
            # ─────────────────────────────────────────────────────────────────
            
            nlp_input = NLPInput(
                session_id=analysis_input.call_metadata.session_id,
                transcript=analysis_input.full_transcript,
                detected_language=analysis_input.detected_language,
            )

            classification_result = await self.nlp_classifier.classify(nlp_input)
            logger.info(f"Classification completed: {classification_result}")

            # ─────────────────────────────────────────────────────────────────
            # Step 2: Smart Routing
            # ─────────────────────────────────────────────────────────────────
            
            routing_input = VoiceInput(
                session_id=analysis_input.call_metadata.session_id,
                transcript=analysis_input.full_transcript,
            )

            routing_result = await self.smart_router.process(routing_input)
            logger.info(f"Routing completed: {routing_result}")

            # ─────────────────────────────────────────────────────────────────
            # Step 3: Determine Flags & Actions
            # ─────────────────────────────────────────────────────────────────
            
            is_emergency = classification_result.edge_case == EdgeCaseType.EMERGENCY
            is_abuse = classification_result.edge_case == EdgeCaseType.ABUSE
            is_silence = classification_result.edge_case == EdgeCaseType.SILENCE
            
            # Determine if genuine complaint
            is_genuine = (
                classification_result.edge_case == EdgeCaseType.VALID
                and classification_result.intent == ClassifierIntentType.NEW_COMPLAINT
            )
            
            # Determine action
            action = self._determine_action(
                is_emergency=is_emergency,
                is_abuse=is_abuse,
                is_silence=is_silence,
                intent=classification_result.intent,
                routing_data=routing_result,
            )

            # ─────────────────────────────────────────────────────────────────
            # Step 4: Extract Entities
            # ─────────────────────────────────────────────────────────────────
            
            entities = self._extract_entities(routing_result)

            # ─────────────────────────────────────────────────────────────────
            # Step 5: Generate Summary
            # ─────────────────────────────────────────────────────────────────
            
            summary = self._generate_summary(
                transcript=analysis_input.full_transcript,
                intent=classification_result.intent,
                routing_data=routing_result,
            )

            # ─────────────────────────────────────────────────────────────────
            # Step 6: Build Output
            # ─────────────────────────────────────────────────────────────────
            
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            word_count = len(analysis_input.full_transcript.split())

            output = PostCallAnalysisOutput(
                status=AnalysisStatus.COMPLETED,
                analysis_id=analysis_id,
                call_id=analysis_input.call_metadata.call_id,
                analysis_timestamp=datetime.utcnow(),
                classification=ClassificationResult(
                    language=classification_result.language.value,
                    intent=classification_result.intent.value,
                    edge_case=classification_result.edge_case.value,
                    confidence=classification_result.confidence,
                    keywords_detected=[],  # NLP classifier doesn't return keywords
                ),
                routing=RoutingResult(
                    department_id=routing_result.routing_data.dept_id,
                    department_name=DEPT_MAPPING.get(
                        routing_result.routing_data.dept_id, {}
                    ).get("name", "Unknown"),
                    issue_category=routing_result.issue_category,
                    routing_confidence=routing_result.confidence,
                    suggested_action=self._action_type_to_action_required(routing_result.action),
                    priority_level=self._priority_to_level(routing_result.routing_data.priority),
                ),
                summary=summary,
                entities=entities,
                is_emergency=routing_result.is_emergency,
                is_abuse=is_abuse,
                is_prank=(classification_result.intent == ClassifierIntentType.ABUSE),
                is_genuine_complaint=is_genuine,
                processing_time_ms=processing_time_ms,
                transcript_length=len(analysis_input.full_transcript),
                word_count=word_count,
                raw_nlp_output=classification_result.model_dump() if classification_result else None,
                raw_routing_output=routing_result.model_dump() if routing_result else None,
            )

            logger.info(f"Post-call analysis completed: {analysis_id}")
            return output

        except Exception as e:
            logger.error(f"Post-call analysis failed for {analysis_id}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _determine_action(
        is_emergency: bool,
        is_abuse: bool,
        is_silence: bool,
        intent: str,
        routing_data: Any,
    ) -> ActionRequired:
        """Determine action based on analysis results."""
        if is_emergency:
            return ActionRequired.ESCALATE_EMERGENCY
        elif is_abuse:
            return ActionRequired.TRANSFER_TO_HUMAN
        elif is_silence:
            return ActionRequired.AUTO_RESOLVE
        elif intent == ClassifierIntentType.ABUSE:
            return ActionRequired.MARK_PRANK
        elif intent == ClassifierIntentType.FEEDBACK:
            return ActionRequired.STORE_FEEDBACK
        elif intent == ClassifierIntentType.NEW_COMPLAINT:
            return ActionRequired.CREATE_TICKET
        else:
            return ActionRequired.TRANSFER_TO_HUMAN

    @staticmethod
    def _extract_entities(routing_data: Any) -> Dict[str, Any]:
        """Extract entities from routing data."""
        entities = {}
        if hasattr(routing_data, "routing_data") and routing_data.routing_data:
            if hasattr(routing_data.routing_data, "issue_category"):
                entities["issue_category"] = routing_data.routing_data.issue_category
            if hasattr(routing_data.routing_data, "priority_level"):
                entities["priority"] = routing_data.routing_data.priority_level
        return entities

    @staticmethod
    def _generate_summary(
        transcript: str, intent: str, routing_data: Any
    ) -> str:
        """Generate a brief summary of the call."""
        words = transcript.split()[:20]
        preview = " ".join(words)
        if len(transcript.split()) > 20:
            preview += "..."

        department = "Unknown Department"
        if hasattr(routing_data, "department_name"):
            department = routing_data.department_name

        return f"Call classified as {intent} routed to {department}. Summary: {preview}"

    @staticmethod
    def _action_type_to_action_required(action_type: ActionType) -> ActionRequired:
        """Convert ActionType to ActionRequired."""
        mapping = {
            ActionType.CREATE_TICKET: ActionRequired.CREATE_TICKET,
            ActionType.TRANSFER_HUMAN: ActionRequired.TRANSFER_TO_HUMAN,
            ActionType.DISCONNECT: ActionRequired.AUTO_RESOLVE,
            ActionType.REPROMPT_USER: ActionRequired.AUTO_RESOLVE,
        }
        return mapping.get(action_type, ActionRequired.TRANSFER_TO_HUMAN)

    @staticmethod
    def _priority_to_level(priority: int) -> str:
        """Convert numeric priority to level string."""
        if priority >= 5:
            return "EMERGENCY"
        elif priority >= 4:
            return "HIGH"
        elif priority >= 2:
            return "MEDIUM"
        else:
            return "LOW"
