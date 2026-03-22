"""
Layer 3: The Brain - Intelligent Call Router for Automated Helpline

This module receives transcribed text from STT and routes calls intelligently.
It handles:
- Emergency keyword detection (fast, regex-based)
- NLP via Sarvam-1 for intent classification and entity extraction
- Deterministic department routing
- Noise detection and filtering
- Urgency scoring
"""

import re
import logging
import time
from enum import Enum
from typing import Optional, Dict, List, Tuple
from pydantic import BaseModel, Field, field_validator
import requests
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class IntentType(str, Enum):
    """Call intent classification."""
    COMPLAINT = "COMPLAINT"
    INQUIRY = "INQUIRY"
    NOISE = "NOISE"
    VAGUE = "VAGUE"


class UrgencyLevel(str, Enum):
    """Urgency/priority levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"


class EntityExtraction(BaseModel):
    """Extracted entities from transcription."""
    problem: Optional[str] = Field(None, description="Issue/complaint topic")
    location: Optional[str] = Field(None, description="Geographic location if mentioned")
    department: Optional[str] = Field(None, description="Relevant department if inferred")


class RouterInput(BaseModel):
    """Input schema for call routing."""
    session_id: str = Field(..., description="Unique session identifier")
    transcription_text: str = Field(..., description="STT output")
    language_code: str = Field(
        default="hi", 
        description="Language code (hi=Hindi, en=English, ta=Tamil, etc.)"
    )
    
    @field_validator("transcription_text")
    @classmethod
    def validate_transcription(cls, v: str) -> str:
        """Ensure transcription is non-empty after stripping."""
        v = v.strip()
        if not v:
            raise ValueError("Transcription cannot be empty")
        return v


class RouterOutput(BaseModel):
    """Structured output from the router."""
    session_id: str
    is_emergency: bool = Field(..., description="Emergency flag")
    intent: IntentType = Field(..., description="Call intent classification")
    urgency: UrgencyLevel = Field(..., description="Urgency/priority level")
    dept_id: str = Field(..., description="Routed department ID")
    department_name: Optional[str] = Field(None, description="Human-readable dept name")
    summary: str = Field(..., description="1-sentence issue summary")
    entities: EntityExtraction = Field(..., description="Extracted entities")
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence in routing decision"
    )
    raw_transcript: str
    processing_time_ms: float


# ============================================================================
# DEPARTMENT MAPPING & KEYWORDS
# ============================================================================


DEPARTMENT_REGISTRY: Dict[str, Dict] = {
    "DEPT_WATER_001": {
        "name": "Water & Sewerage",
        "keywords": ["water", "tap", "pipe", "leak", "sewer", "drain", "sewage", "jal", "pathli", "nali"],
        "aliases": ["WATER", "SEWERAGE", "PLUMBING"],
    },
    "DEPT_ROADS_001": {
        "name": "Roads & Infrastructure",
        "keywords": ["road", "pothole", "street", "pavement", "highway", "traffic", "sadak", "gaddha"],
        "aliases": ["ROADS", "INFRASTRUCTURE", "TRANSPORT"],
    },
    "DEPT_SANITATION_001": {
        "name": "Sanitation & Waste",
        "keywords": ["garbage", "waste", "trash", "dust", "clean", "sanitation", "gali", "safai"],
        "aliases": ["SANITATION", "WASTE", "CLEANING"],
    },
    "DEPT_ELECTRICITY_001": {
        "name": "Electricity & Power",
        "keywords": ["electric", "power", "light", "bulb", "meter", "circuit", "bijli", "urja"],
        "aliases": ["ELECTRICITY", "POWER", "LIGHTS"],
    },
    "DEPT_HEALTH_001": {
        "name": "Health & Medical",
        "keywords": ["health", "hospital", "doctor", "clinic", "medical", "medicine", "vaccine"],
        "aliases": ["HEALTH", "HOSPITAL", "MEDICAL"],
    },
    "DEPT_EDUCATION_001": {
        "name": "Education",
        "keywords": ["school", "college", "education", "student", "fees", "admission", "padhai"],
        "aliases": ["EDUCATION", "SCHOOL"],
    },
    "DEPT_GENERAL_001": {
        "name": "General Grievances",
        "keywords": [],
        "aliases": ["GENERAL", "OTHER"],
    },
}

# Emergency keywords: regex pattern for high-priority issues
EMERGENCY_KEYWORDS_PATTERN = re.compile(
    r'\b(fire|emergency|ambulance|police|injury|accident|danger|critical|'
    r'urgent|violence|attack|gas leak|electrical fire|snake|electrocution)\b',
    re.IGNORECASE
)

# Noise/filler keywords: patterns indicating low-signal content
NOISE_KEYWORDS = {
    "uh", "um", "uh huh", "hello", "hi", "ok", "okay", "yeah", "yep", "nope", 
    "hmm", "huh", "eh", "ah", "pause", "repeat", "what",
    "haan", "na", "kuch nahi", "koi baat nahi", "bas", "theek"
}

# Minimum word threshold for valid transcription
MIN_WORDS_THRESHOLD = 3


# ============================================================================
# SARVAM-1 LLM INTEGRATION (WITH MOCK & RETRY)
# ============================================================================


class SarvamAPIClient(ABC):
    """Abstract base class for Sarvam API clients."""
    
    @abstractmethod
    def classify_intent(
        self, 
        text: str, 
        language_code: str
    ) -> Dict:
        """Classify intent and extract entities."""
        pass


class RealSarvamAPIClient(SarvamAPIClient):
    """Real Sarvam-1 API client with retry logic."""
    
    def __init__(
        self, 
        api_key: str, 
        api_endpoint: str = "https://api.sarvam.ai/classify",
        timeout: int = 10,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    def classify_intent(
        self, 
        text: str, 
        language_code: str
    ) -> Dict:
        """
        Call Sarvam-1 API to classify intent and extract entities.
        
        Returns:
            Dict with keys: intent, entities, urgency, confidence
        """
        payload = {
            "text": text,
            "language": language_code,
            "task": "intent_classification_with_ner",
        }
        
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as exc:
                last_error = exc
                logger.warning(
                    f"Sarvam API request failed (attempt {attempt + 1}/{self.max_retries + 1}): {exc}"
                )
                if attempt < self.max_retries:
                    wait_time = 0.5 * (2 ** attempt)  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    break
        
        raise RuntimeError(f"Sarvam API failed after {self.max_retries + 1} retries: {last_error}")


class MockSarvamAPIClient(SarvamAPIClient):
    """Mock Sarvam API client for testing/development."""
    
    def classify_intent(
        self, 
        text: str, 
        language_code: str
    ) -> Dict:
        """Mock intent classification."""
        lower_text = text.lower()
        
        # Heuristic-based mock classification
        intent = IntentType.INQUIRY
        confidence = 0.75
        
        # Check for complaints: problem keywords or specific complaint indicators
        problem_words = ["leak", "pothole", "broken", "issue", "problem", "complain", 
                        "garbage", "waste", "electric", "light", "pani", "gaddha", "pipe", "water"]
        has_problem = any(word in lower_text for word in problem_words)
        has_complaint_indicator = any(word in lower_text for word in ["please fix", "broken", "issue", "complain"])
        
        if has_problem or has_complaint_indicator:
            intent = IntentType.COMPLAINT
            confidence = 0.85
        
        urgency = UrgencyLevel.LOW
        if any(word in lower_text for word in ["urgent", "asap", "quickly", "immediately", "bahut", "bohot"]):
            urgency = UrgencyLevel.HIGH
            confidence = min(confidence + 0.1, 1.0)
        
        # Extract entities
        entities = {
            "problem": self._extract_problem(text),
            "location": self._extract_location(text),
        }
        
        return {
            "intent": intent.value,
            "entities": entities,
            "urgency": urgency.value,
            "confidence": min(confidence, 1.0),
        }
    
    @staticmethod
    def _extract_problem(text: str) -> Optional[str]:
        """Simple problem extraction."""
        keywords = {
            "water": ["water", "tap", "pipe", "leak", "pani", "takarav", "jal"],
            "roads": ["road", "pothole", "street", "sadak", "gaddha", "pavement"],
            "garbage": ["garbage", "waste", "trash", "dust", "clean", "sanitation", "gali"],
            "electricity": ["electric", "light", "power", "bulb", "meter", "circuit", "bijli", "urja"],
        }
        
        for problem, kw_list in keywords.items():
            if any(k in text.lower() for k in kw_list):
                return problem
        return None
    
    @staticmethod
    def _extract_location(text: str) -> Optional[str]:
        """Simple location extraction (mock)."""
        # In production, use NER but for demo we look for common patterns
        if "near" in text.lower() or "at" in text.lower():
            words = text.lower().split()
            for i, word in enumerate(words):
                if word in ["near", "at", "by"] and i + 1 < len(words):
                    return words[i + 1]
        return None


# ============================================================================
# MAIN ROUTER CLASS
# ============================================================================


class CallRouter:
    """
    Main router class handling call intelligence and routing.
    
    Process flow:
    1. Emergency pre-filter (regex) - fast path
    2. Noise detection
    3. LLM processing (Sarvam-1)
    4. Department mapping
    5. Output validation
    """
    
    def __init__(
        self,
        llm_client: Optional[SarvamAPIClient] = None,
        use_mock: bool = True,
    ):
        """
        Initialize router.
        
        Args:
            llm_client: Sarvam API client instance
            use_mock: If True and no client provided, use mock client
        """
        if llm_client:
            self.llm_client = llm_client
        elif use_mock:
            self.llm_client = MockSarvamAPIClient()
        else:
            raise ValueError(
                "Must provide llm_client or set use_mock=True"
            )
        
        logger.info(f"CallRouter initialized with {type(self.llm_client).__name__}")
    
    def process_call(self, router_input: RouterInput) -> RouterOutput:
        """
        Main entry point: process a call and return routing decision.
        
        Args:
            router_input: RouterInput object with session_id, transcription_text, language_code
        
        Returns:
            RouterOutput with routing decision
        
        Raises:
            ValueError: If input validation fails
            RuntimeError: If LLM processing fails
        """
        start_time = time.time()
        
        try:
            # Step 1: Emergency pre-filter (fastest check)
            is_emergency = self._check_emergency(router_input.transcription_text)
            if is_emergency:
                return self._create_emergency_output(router_input, start_time)
            
            # Step 2: Noise detection
            is_noise, intent = self._detect_noise(router_input.transcription_text)
            if is_noise:
                return self._create_noise_output(router_input, intent, start_time)
            
            # Step 3: LLM processing
            llm_result = self.llm_client.classify_intent(
                router_input.transcription_text,
                router_input.language_code,
            )
            
            # Step 4: Department routing
            dept_id, dept_name = self._route_to_department(
                router_input.transcription_text,
                llm_result.get("entities", {}),
                llm_result.get("intent"),
            )
            
            # Step 5: Assemble output
            intent = IntentType(llm_result.get("intent", IntentType.INQUIRY.value))
            urgency = UrgencyLevel(llm_result.get("urgency", UrgencyLevel.MEDIUM.value))
            
            summary = self._generate_summary(
                router_input.transcription_text,
                intent,
                llm_result.get("entities", {}),
            )
            
            entities = EntityExtraction(
                problem=llm_result.get("entities", {}).get("problem"),
                location=llm_result.get("entities", {}).get("location"),
                department=dept_name,
            )
            
            output = RouterOutput(
                session_id=router_input.session_id,
                is_emergency=False,
                intent=intent,
                urgency=urgency,
                dept_id=dept_id,
                department_name=dept_name,
                summary=summary,
                entities=entities,
                confidence_score=llm_result.get("confidence", 0.7),
                raw_transcript=router_input.transcription_text,
                processing_time_ms=round((time.time() - start_time) * 1000, 2),
            )
            
            logger.info(
                f"Session {router_input.session_id}: Routed to {dept_id} "
                f"with confidence {output.confidence_score:.2f} in {output.processing_time_ms}ms"
            )
            
            return output
            
        except Exception as exc:
            logger.error(f"Router error for session {router_input.session_id}: {exc}", exc_info=True)
            raise
    
    def _check_emergency(self, text: str) -> bool:
        """
        Fast emergency keyword check using regex.
        
        Args:
            text: Transcription text
        
        Returns:
            True if emergency keywords detected
        """
        return bool(EMERGENCY_KEYWORDS_PATTERN.search(text))
    
    def _detect_noise(self, text: str) -> Tuple[bool, IntentType]:
        """
        Detect if transcript is noise/filler only.
        
        Returns:
            Tuple of (is_noise, intent_if_valid)
        """
        # Filter out punctuation and whitespace
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Check word count
        if len(words) < MIN_WORDS_THRESHOLD:
            logger.debug(f"Detected noise: insufficient words ({len(words)} < {MIN_WORDS_THRESHOLD})")
            return True, IntentType.VAGUE
        
        # Check if all words are noise
        non_noise_words = [w for w in words if w not in NOISE_KEYWORDS]
        if not non_noise_words:
            logger.debug(f"Detected noise: all words are fillers")
            return True, IntentType.NOISE
        
        return False, IntentType.COMPLAINT
    
    def _route_to_department(
        self,
        text: str,
        entities: Dict,
        detected_intent: Optional[str],
    ) -> Tuple[str, str]:
        """
        Route to best-matching department using keyword similarity and entities.
        
        Returns:
            Tuple of (dept_id, dept_name)
        """
        scores = []
        
        # Score each department based on keyword matching
        text_lower = text.lower()
        
        for dept_id, dept_info in DEPARTMENT_REGISTRY.items():
            score = 0.0
            
            # Match against keywords
            for keyword in dept_info["keywords"]:
                if keyword in text_lower:
                    score += 1.0
            
            # Boost score if problem entity matches
            problem = entities.get("problem") if entities else None
            if problem:
                problem_lower = problem.lower()
                if any(kw.startswith(problem_lower) or problem_lower in kw for kw in dept_info["keywords"]):
                    score += 0.5
            
            if score > 0 or dept_id == "DEPT_GENERAL_001":
                scores.append((dept_id, dept_info["name"], score))
        
        # Sort by score (descending) and pick top
        scores.sort(key=lambda x: x[2], reverse=True)
        
        if scores and scores[0][2] > 0:
            dept_id, dept_name, _ = scores[0]
        else:
            # Default to general if no match
            dept_id = "DEPT_GENERAL_001"
            dept_name = DEPARTMENT_REGISTRY[dept_id]["name"]
        
        return dept_id, dept_name
    
    def _generate_summary(
        self,
        text: str,
        intent: IntentType,
        entities: Dict,
    ) -> str:
        """Generate a 1-sentence summary of the issue."""
        problem = entities.get("problem") if entities else None
        problem_str = problem.title() if problem else "Issue"
        location = entities.get("location", "") if entities else ""
        
        if location:
            return f"{intent.value.title()} reported: {problem_str} at {location}."
        else:
            return f"{intent.value.title()} reported: {problem_str}."
    
    def _create_emergency_output(
        self,
        router_input: RouterInput,
        start_time: float,
    ) -> RouterOutput:
        """Create output for emergency cases."""
        return RouterOutput(
            session_id=router_input.session_id,
            is_emergency=True,
            intent=IntentType.COMPLAINT,
            urgency=UrgencyLevel.EMERGENCY,
            dept_id="DEPT_EMERGENCY_911",
            department_name="Emergency Services",
            summary="Emergency detected. Immediate response required.",
            entities=EntityExtraction(
                problem="Emergency",
                location=None,
                department="Emergency Services",
            ),
            confidence_score=1.0,
            raw_transcript=router_input.transcription_text,
            processing_time_ms=round((time.time() - start_time) * 1000, 2),
        )
    
    def _create_noise_output(
        self,
        router_input: RouterInput,
        intent: IntentType,
        start_time: float,
    ) -> RouterOutput:
        """Create output for noise/vague inputs."""
        return RouterOutput(
            session_id=router_input.session_id,
            is_emergency=False,
            intent=intent,
            urgency=UrgencyLevel.LOW,
            dept_id="DEPT_GENERAL_001",
            department_name="Requires Re-prompt",
            summary="Unable to understand request. Please repeat or provide more details.",
            entities=EntityExtraction(),
            confidence_score=0.0,
            raw_transcript=router_input.transcription_text,
            processing_time_ms=round((time.time() - start_time) * 1000, 2),
        )


# ============================================================================
# HELPER FUNCTION FOR EASY INTEGRATION
# ============================================================================


def route_call(
    session_id: str,
    text: str,
    language_code: str = "hi",
    router: Optional[CallRouter] = None,
) -> RouterOutput:
    """
    Convenience function to route a call.
    
    Example:
        result = route_call(
            session_id="call_123",
            text="Mera ghar ke paas road mein pothole hai",
            language_code="hi",
        )
    """
    if router is None:
        router = CallRouter(use_mock=True)
    
    router_input = RouterInput(
        session_id=session_id,
        transcription_text=text,
        language_code=language_code,
    )
    
    return router.process_call(router_input)
