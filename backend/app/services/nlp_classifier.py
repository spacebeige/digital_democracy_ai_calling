"""
NLP Classifier: Language Detection, Intent Classification, and Edge-Case Handling
===================================================================================

Handles:
- Language detection (hi, en, hinglish, ta, te, bn, mr, kn, ml, pa)
- Intent classification (NEW_COMPLAINT, STATUS_QUERY, FEEDBACK, ABUSE, OTHER)
- Pre-check edge cases: emergency (regex), silence (length), abuse (lexicon + LLM)
- Structured Sarvam-1 integration with forced JSON schema
- Hinglish/regional language normalization for analytics
"""

import asyncio
import json
import logging
import os
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import httpx
from pydantic import BaseModel, Field, field_validator
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════


class LanguageCode(str, Enum):
    """Supported language codes."""
    HINDI = "hi"
    ENGLISH = "en"
    HINGLISH = "hinglish"
    TAMIL = "ta"
    TELUGU = "te"
    BENGALI = "bn"
    MARATHI = "mr"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    OTHER = "other"


class IntentType(str, Enum):
    """Intent classification categories."""
    NEW_COMPLAINT = "NEW_COMPLAINT"
    STATUS_QUERY = "STATUS_QUERY"
    FEEDBACK = "FEEDBACK"
    ABUSE = "ABUSE"
    OTHER = "OTHER"


class IssueCategory(str, Enum):
    """Civic issue categories."""
    WATER = "Water"
    ELECTRICITY = "Electricity"
    ROAD = "Road"
    WASTE = "Waste"
    HEALTH = "Health"
    EDUCATION = "Education"
    GENERAL = "General"


class EdgeCaseType(str, Enum):
    """Edge case classifications."""
    EMERGENCY = "EMERGENCY"
    SILENCE = "SILENCE"
    ABUSE = "ABUSE"
    VALID = "VALID"


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class NLPInput(BaseModel):
    """Input to NLP classifier."""
    session_id: Union[str, UUID] = Field(..., description="Unique session identifier (UUID or string)")
    transcript: str = Field(..., description="Raw STT transcript")
    detected_language: Optional[str] = Field(
        default=None,
        description="Optional pre-detected language hint (hi, en, ta, etc.)",
    )

    @field_validator("transcript")
    @classmethod
    def transcript_valid(cls, v: str) -> str:
        # Allow empty/whitespace transcripts - will be caught by silence detector
        return v.strip() if v else ""


class SarvamNLPResponse(BaseModel):
    """Structured response from Sarvam-1 LLM."""
    language: LanguageCode = LanguageCode.OTHER
    intent: IntentType = IntentType.OTHER
    issue_category: IssueCategory = IssueCategory.GENERAL
    urgency: int = Field(default=3, ge=1, le=5)
    abuse_flag: bool = False
    emergency_flag: bool = False
    summary: str = Field(default="", description="Issue summary")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class EdgeCaseResult(BaseModel):
    """Result of edge-case pre-checks."""
    case_type: EdgeCaseType
    detected: bool
    reason: Optional[str] = None
    action_required: Optional[str] = None
    confidence: Optional[float] = Field(default=1.0, description="Confidence score (0.0-1.0), lower if conflicting signals")


class NLPOutput(BaseModel):
    """Complete NLP classification output."""
    session_id: Union[str, UUID]
    transcript: str
    language: LanguageCode
    intent: IntentType
    issue_category: IssueCategory
    urgency: int
    abuse_flag: bool
    emergency_flag: bool
    edge_case: EdgeCaseType
    edge_case_reason: Optional[str] = None
    summary: str
    confidence: float
    processing_time_ms: float
    audit_log: List[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS: PATTERNS & LEXICONS
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# DYNAMIC KEYWORD LOADING (from JSON configuration)
# ═══════════════════════════════════════════════════════════════════════════════

def _load_emergency_keywords():
    """Load emergency keywords from JSON configuration file."""
    keywords_file = os.path.join(
        os.path.dirname(__file__),
        "emergency_keywords.json"
    )
    try:
        with open(keywords_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as exc:
        logger.warning(f"Failed to load emergency keywords from {keywords_file}: {exc}")
        logger.warning("Falling back to minimal keywords")
        return {
            "emergency_keywords": {"medical_emergency": [], "police_law": []},
            "silence_fillers": {"english": [], "hindi": []},
            "abuse_toxicity": {"hindi": [], "english": [], "universal": []}
        }

_KEYWORD_CONFIG = _load_emergency_keywords()

# Build compiled regex patterns from dynamic keywords
def _build_emergency_pattern():
    """Build regex pattern from dynamic emergency keywords."""
    emergency_dict = _KEYWORD_CONFIG.get("emergency_keywords", {})
    all_keywords = []
    for category, keywords in emergency_dict.items():
        all_keywords.extend(keywords)
    
    if not all_keywords:
        # Fallback minimal pattern
        return re.compile(
            r"\b(fire|aag|ambulance|police|accident|emergency|urgent)\b",
            re.IGNORECASE
        )
    
    # Escape special characters and join with OR
    escaped_keywords = [re.escape(kw) for kw in all_keywords]
    pattern_str = r"\b(" + "|".join(escaped_keywords) + r")\b"
    return re.compile(pattern_str, re.IGNORECASE)

# Build filler words from dynamic keywords
def _build_filler_words():
    """Build filler words set from dynamic configuration."""
    filler_dict = _KEYWORD_CONFIG.get("silence_fillers", {})
    all_fillers = []
    for lang, words in filler_dict.items():
        all_fillers.extend(words)
    return frozenset(w.lower().replace("-", " ") for w in all_fillers)

# Build abuse lexicon from dynamic keywords
def _build_abuse_lexicon():
    """Build abuse lexicon from dynamic configuration."""
    abuse_dict = _KEYWORD_CONFIG.get("abuse_toxicity", {})
    all_abuse = []
    for category, words in abuse_dict.items():
        all_abuse.extend(words)
    return frozenset(w.lower().replace("-", " ") for w in all_abuse)

# Build prank indicators from dynamic keywords
def _build_prank_indicators():
    """Build prank indicator set from dynamic configuration."""
    prank_dict = _KEYWORD_CONFIG.get("prank_indicators", {})
    all_prank = []
    for category, words in prank_dict.items():
        all_prank.extend(words)
    return frozenset(w.lower().replace("-", " ") for w in all_prank)

# Initialize dynamic patterns
EMERGENCY_PATTERN = _build_emergency_pattern()
FILLER_WORDS = _build_filler_words()
ABUSE_LEXICON = _build_abuse_lexicon()
PRANK_INDICATORS = _build_prank_indicators()

# Count loaded keywords
_emergency_count = sum(len(v) for v in _KEYWORD_CONFIG.get("emergency_keywords", {}).values())
_filler_count = sum(len(v) for v in _KEYWORD_CONFIG.get("silence_fillers", {}).values())
_abuse_count = sum(len(v) for v in _KEYWORD_CONFIG.get("abuse_toxicity", {}).values())
_prank_count = sum(len(v) for v in _KEYWORD_CONFIG.get("prank_indicators", {}).values())

logger.info("NLP Classifier initialized: %d emergency keywords, %d filler words, %d abuse terms, %d prank indicators",
            _emergency_count, _filler_count, _abuse_count, _prank_count)

# Language detection patterns
HINDI_PATTERN = re.compile(r"[\u0900-\u097F]")  # Devanagari script
TAMIL_PATTERN = re.compile(r"[\u0B80-\u0BFF]")  # Tamil script
TELUGU_PATTERN = re.compile(r"[\u0C00-\u0C7F]")  # Telugu script
KANNADA_PATTERN = re.compile(r"[\u0C80-\u0CFF]")  # Kannada script
MALAYALAM_PATTERN = re.compile(r"[\u0D00-\u0D7F]")  # Malayalam script
BENGALI_PATTERN = re.compile(r"[\u0980-\u09FF]")  # Bengali script
GURMUKHI_PATTERN = re.compile(r"[\u0A00-\u0A7F]")  # Punjabi (Gurmukhi)
MARATHI_PATTERN = re.compile(r"[\u0900-\u097F]")  # Marathi (Devanagari)

MIN_WORDS_THRESHOLD = 3
MIN_CHARS_THRESHOLD = 5


# ═══════════════════════════════════════════════════════════════════════════════
# SARVAM-1 LLM CLIENT (with forced JSON schema)
# ═══════════════════════════════════════════════════════════════════════════════

_SARVAM_SYSTEM_PROMPT = """\
You are an intelligent NLP classifier for Indian government helpline transcripts.
Analyze the citizen's transcript and respond ONLY with valid JSON. No explanation, \
no markdown, no extra text — just the JSON object.

Required JSON schema:
{
  "language": "<hi|en|hinglish|ta|te|bn|mr|kn|ml|pa|other>",
  "intent": "<NEW_COMPLAINT|STATUS_QUERY|FEEDBACK|ABUSE|OTHER>",
  "issue_category": "<Water|Electricity|Road|Waste|Health|Education|General>",
  "urgency": <1 to 5, where 5 is most urgent>,
  "abuse_flag": <true|false>,
  "emergency_flag": <true|false>,
  "summary": "<Concise 10-word summary of the issue>"
}

Instructions:
1. For language:
   - If mixed Hindi-English → "hinglish"
   - Pure Hindi → "hi"
   - Pure English → "en"
   - Regional scripts → detect (ta, te, bn, mr, kn, ml, pa)

2. For intent:
   - NEW_COMPLAINT: Citizen reporting civic issue
   - STATUS_QUERY: Asking about existing complaint
   - FEEDBACK: Appreciation or suggestion
   - ABUSE: Profanity, threats, or hostile language
   - OTHER: Unclear

3. For urgency:
   - 5: Life-threatening, immediate action needed
   - 4: Very urgent, high priority
   - 3: Normal/medium priority
   - 2: Low priority
   - 1: Informational only

4. For abuse_flag:
   - true if profanity, threats, or abusive language detected
   - false otherwise

5. For emergency_flag:
   - true if life-threatening or emergency keywords present
   - false otherwise

6. For issue_category:
   - Map complaint to ONE category
   - Default to General if unclear
"""


class SarvamLLMClient:
    """Sarvam-1 LLM client with retry and timeout handling."""

    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.sarvam.ai/v1/chat/completions",
        timeout: float = 10.0,
    ):
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=True,
    )
    async def classify(self, transcript: str) -> SarvamNLPResponse:
        """
        Send transcript to Sarvam-1 and parse forced-JSON response.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sarvam-1",
                    "messages": [
                        {"role": "system", "content": _SARVAM_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Classify this transcript:\n\n{transcript}"},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "max_tokens": 300,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        # Extract and parse JSON from response
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        return self._parse_response(content)

    @staticmethod
    def _parse_response(raw_text: str) -> SarvamNLPResponse:
        """Safely parse LLM JSON with fallback."""
        # Clean markdown code fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
            return SarvamNLPResponse(**data)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Malformed LLM response, using fallback: %s", exc)
            return SarvamNLPResponse(summary="Unable to parse LLM response")


class MockSarvamClient:
    """Mock Sarvam client for development/testing."""

    async def classify(self, transcript: str) -> SarvamNLPResponse:
        """Heuristic-based mock classification."""
        lower = transcript.lower()

        # Detect language
        language = self._detect_language(transcript)

        # Detect abuse
        abuse_flag = any(word in lower for word in ABUSE_LEXICON)

        # Detect emergency
        emergency_flag = bool(EMERGENCY_PATTERN.search(transcript))

        # Detect intent
        intent = IntentType.OTHER
        if emergency_flag:
            intent = IntentType.NEW_COMPLAINT
        elif abuse_flag:
            intent = IntentType.ABUSE
        elif any(word in lower for word in ["status", "kya hua", "kab hoga", "update"]):
            intent = IntentType.STATUS_QUERY
        elif any(word in lower for word in ["thanks", "thank", "dhanyavad", "feedback"]):
            intent = IntentType.FEEDBACK
        elif any(
            word in lower
            for word in ["water", "pani", "pothole", "sadak", "bijli", "doctor", "school"]
        ):
            intent = IntentType.NEW_COMPLAINT

        # Detect issue category
        category = IssueCategory.GENERAL
        if any(w in lower for w in ["water", "pani", "tap", "leak", "nal", "nali"]):
            category = IssueCategory.WATER
        elif any(w in lower for w in ["pothole", "road", "sadak", "gaddha", "street"]):
            category = IssueCategory.ROAD
        elif any(w in lower for w in ["electric", "bijli", "power", "light", "meter"]):
            category = IssueCategory.ELECTRICITY
        elif any(w in lower for w in ["garbage", "waste", "trash", "kachra", "safai"]):
            category = IssueCategory.WASTE
        elif any(w in lower for w in ["hospital", "doctor", "health", "aspatal", "dawai"]):
            category = IssueCategory.HEALTH
        elif any(w in lower for w in ["school", "college", "padhai", "student", "fees"]):
            category = IssueCategory.EDUCATION

        # Urgency scoring
        urgency = 3
        if emergency_flag:
            urgency = 5
        elif any(word in lower for word in ["urgent", "jaldi", "turant", "immediately"]):
            urgency = 4

        summary = " ".join(transcript.split()[:10])
        if len(summary) > 60:
            summary = summary[:57] + "..."

        return SarvamNLPResponse(
            language=language,
            intent=intent,
            issue_category=category,
            urgency=urgency,
            abuse_flag=abuse_flag,
            emergency_flag=emergency_flag,
            summary=summary,
            confidence=0.8,
        )

    @staticmethod
    def _detect_language(text: str) -> LanguageCode:
        """Detect language from script and word patterns."""
        hindi_count = len(HINDI_PATTERN.findall(text))
        tamil_count = len(TAMIL_PATTERN.findall(text))
        telugu_count = len(TELUGU_PATTERN.findall(text))
        kannada_count = len(KANNADA_PATTERN.findall(text))
        malayalam_count = len(MALAYALAM_PATTERN.findall(text))
        bengali_count = len(BENGALI_PATTERN.findall(text))
        punjabi_count = len(GURMUKHI_PATTERN.findall(text))

        if hindi_count > 0:
            return LanguageCode.HINDI
        elif tamil_count > 0:
            return LanguageCode.TAMIL
        elif telugu_count > 0:
            return LanguageCode.TELUGU
        elif kannada_count > 0:
            return LanguageCode.KANNADA
        elif malayalam_count > 0:
            return LanguageCode.MALAYALAM
        elif bengali_count > 0:
            return LanguageCode.BENGALI
        elif punjabi_count > 0:
            return LanguageCode.PUNJABI
        
        # Check for hinglish (mix of English + script)
        english_words = len(re.findall(r"\b[a-z]{2,}\b", text.lower()))
        if english_words > 5 and hindi_count > 5:
            return LanguageCode.HINGLISH

        return LanguageCode.ENGLISH


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASE DETECTION (Pre-checks before LLM)
# ═══════════════════════════════════════════════════════════════════════════════


class EdgeCaseDetector:
    """Deterministic edge-case detection using rules."""

    @staticmethod
    def check_emergency(transcript: str) -> EdgeCaseResult:
        """
        Detect emergency keywords with conflict detection for prank indicators.
        
        Strategy:
        - If emergency keyword + prank indicator → CONFLICTED (needs human review)
        - If emergency keyword only → EMERGENCY (auto-transfer)
        - If prank indicator only → Not emergency
        - If neither → Not emergency
        """
        lower = transcript.lower()
        
        has_emergency = bool(EMERGENCY_PATTERN.search(lower))
        has_prank_signal = any(
            re.search(r"\b" + re.escape(indicator) + r"\b", lower)
            for indicator in PRANK_INDICATORS
        )
        
        # Conflict: Emergency keyword + Prank signal detected
        if has_emergency and has_prank_signal:
            return EdgeCaseResult(
                case_type=EdgeCaseType.EMERGENCY,
                detected=True,
                reason="⚠️ CONFLICTED: Emergency keyword detected BUT prank indicators present (needs verification)",
                action_required="ESCALATE_TO_HUMAN",  # Requires human judgment
                confidence=0.5,  # Lower confidence due to conflict
            )
        
        # Clear emergency: Emergency keyword only
        if has_emergency:
            return EdgeCaseResult(
                case_type=EdgeCaseType.EMERGENCY,
                detected=True,
                reason="Emergency keyword detected",
                action_required="TRANSFER_HUMAN",
                confidence=0.95,
            )
        
        # Not emergency
        return EdgeCaseResult(case_type=EdgeCaseType.EMERGENCY, detected=False)

    @staticmethod
    def check_silence(transcript: str) -> EdgeCaseResult:
        """Detect silence, empty input, or very short transcripts."""
        stripped = transcript.strip()
        word_count = len(stripped.split())

        if not stripped:
            return EdgeCaseResult(
                case_type=EdgeCaseType.SILENCE,
                detected=True,
                reason="Empty transcript",
                action_required="REPROMPT_USER",
            )

        if len(stripped) < MIN_CHARS_THRESHOLD:
            return EdgeCaseResult(
                case_type=EdgeCaseType.SILENCE,
                detected=True,
                reason="Transcript too short (<5 chars)",
                action_required="REPROMPT_USER",
            )

        if word_count < MIN_WORDS_THRESHOLD:
            return EdgeCaseResult(
                case_type=EdgeCaseType.SILENCE,
                detected=True,
                reason=f"Too few words ({word_count} < {MIN_WORDS_THRESHOLD})",
                action_required="REPROMPT_USER",
            )

        # Check for filler-only content
        non_filler_words = [w for w in stripped.lower().split() if w not in FILLER_WORDS]
        if len(non_filler_words) < MIN_WORDS_THRESHOLD:
            return EdgeCaseResult(
                case_type=EdgeCaseType.SILENCE,
                detected=True,
                reason="Filler-only content (um, huh, okay, hi, etc.)",
                action_required="REPROMPT_USER",
            )

        return EdgeCaseResult(case_type=EdgeCaseType.SILENCE, detected=False)

    @staticmethod
    def check_abuse(transcript: str) -> EdgeCaseResult:
        """Detect obvious abuse/toxicity via lexicon (fast check, LLM as fallback)."""
        lower = transcript.lower()
        for abuse_word in ABUSE_LEXICON:
            if re.search(r"\b" + re.escape(abuse_word) + r"\b", lower):
                return EdgeCaseResult(
                    case_type=EdgeCaseType.ABUSE,
                    detected=True,
                    reason=f"Abuse keyword detected: {abuse_word}",
                    action_required="WARN_AND_REPROMPT",
                )
        return EdgeCaseResult(case_type=EdgeCaseType.ABUSE, detected=False)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN NLP CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════════


class NLPClassifier:
    """
    End-to-end NLP classifier combining edge-case detection + Sarvam-1 LLM.

    Pipeline:
      1. Pre-checks (emergency, silence, abuse) → fast rules
      2. If valid, send to Sarvam-1 for structured classification
      3. Return comprehensive NLPOutput with audit trail
    """

    def __init__(
        self,
        sarvam_api_key: Optional[str] = None,
        sarvam_endpoint: str = "https://api.sarvam.ai/v1/chat/completions",
        use_mock: bool = False,
    ):
        self._use_mock = use_mock or (sarvam_api_key is None)
        self._edge_detector = EdgeCaseDetector()

        if self._use_mock:
            self._llm_client = MockSarvamClient()
            logger.info("NLPClassifier initialized with MockSarvamClient")
        else:
            self._llm_client = SarvamLLMClient(api_key=sarvam_api_key, endpoint=sarvam_endpoint)
            logger.info("NLPClassifier initialized with real SarvamLLMClient")

    async def classify(self, nlp_input: NLPInput) -> NLPOutput:
        """
        Main entry point: classify a transcript end-to-end.
        """
        start = time.perf_counter()
        audit: List[str] = []

        # ── Stage 1: Emergency check ────────────────────────────────────
        emergency_result = self._edge_detector.check_emergency(nlp_input.transcript)
        if emergency_result.detected:
            elapsed = (time.perf_counter() - start) * 1000
            audit.append(f"EDGE_CASE: Emergency ({emergency_result.reason})")
            
            # Determine if this is a clear emergency or conflicted
            if emergency_result.action_required == "ESCALATE_TO_HUMAN":
                summary = "⚠️ CONFLICTED: Emergency signal with prank indicators - requires immediate human review"
                intent = IntentType.OTHER  # Don't assume intent due to conflict
            else:
                summary = "Emergency detected — immediate transfer required"
                intent = IntentType.NEW_COMPLAINT
            
            return NLPOutput(
                session_id=nlp_input.session_id,
                transcript=nlp_input.transcript,
                language=LanguageCode.OTHER,
                intent=intent,
                issue_category=IssueCategory.GENERAL,
                urgency=5,
                abuse_flag=False,
                emergency_flag=True,
                edge_case=EdgeCaseType.EMERGENCY,
                edge_case_reason=emergency_result.reason,
                summary=summary,
                confidence=emergency_result.confidence or 0.95,  # Use result confidence
                processing_time_ms=round(elapsed, 2),
                audit_log=audit,
            )
        audit.append("EDGE_CASE_CHECK: Emergency → PASS")

        # ── Stage 2: Silence/noise check ───────────────────────────────
        silence_result = self._edge_detector.check_silence(nlp_input.transcript)
        if silence_result.detected:
            elapsed = (time.perf_counter() - start) * 1000
            audit.append(f"EDGE_CASE: Silence ({silence_result.reason})")
            return NLPOutput(
                session_id=nlp_input.session_id,
                transcript=nlp_input.transcript,
                language=LanguageCode.OTHER,
                intent=IntentType.OTHER,
                issue_category=IssueCategory.GENERAL,
                urgency=1,
                abuse_flag=False,
                emergency_flag=False,
                edge_case=EdgeCaseType.SILENCE,
                edge_case_reason=silence_result.reason,
                summary="Insufficient content — please provide more details",
                confidence=0.1,
                processing_time_ms=round(elapsed, 2),
                audit_log=audit,
            )
        audit.append("EDGE_CASE_CHECK: Silence → PASS")

        # ── Stage 3: Abuse check ───────────────────────────────────────
        abuse_result = self._edge_detector.check_abuse(nlp_input.transcript)
        if abuse_result.detected:
            elapsed = (time.perf_counter() - start) * 1000
            audit.append(f"EDGE_CASE: Abuse ({abuse_result.reason})")
            return NLPOutput(
                session_id=nlp_input.session_id,
                transcript=nlp_input.transcript,
                language=LanguageCode.OTHER,
                intent=IntentType.ABUSE,
                issue_category=IssueCategory.GENERAL,
                urgency=1,
                abuse_flag=True,
                emergency_flag=False,
                edge_case=EdgeCaseType.ABUSE,
                edge_case_reason=abuse_result.reason,
                summary="Abusive content detected — escalating for human review",
                confidence=0.95,
                processing_time_ms=round(elapsed, 2),
                audit_log=audit,
            )
        audit.append("EDGE_CASE_CHECK: Abuse → PASS")

        # ── Stage 4: Sarvam-1 LLM classification ───────────────────────
        try:
            llm_response = await self._llm_client.classify(nlp_input.transcript)
            audit.append(
                f"LLM_CLASSIFY: intent={llm_response.intent.value}, "
                f"language={llm_response.language.value}, "
                f"urgency={llm_response.urgency}"
            )
        except Exception as exc:
            logger.error("LLM classification failed: %s", exc, exc_info=True)
            audit.append(f"LLM_CLASSIFY: FAILED ({exc!r}) → fallback to mock")
            # Fallback to heuristic
            llm_response = SarvamNLPResponse(
                language=LanguageCode.OTHER,
                intent=IntentType.NEW_COMPLAINT,
                issue_category=IssueCategory.GENERAL,
                urgency=3,
                summary="LLM unavailable — using fallback classification",
            )

        # ── Build output ──────────────────────────────────────────────
        elapsed = (time.perf_counter() - start) * 1000
        audit.append("CLASSIFY_COMPLETE")

        return NLPOutput(
            session_id=nlp_input.session_id,
            transcript=nlp_input.transcript,
            language=llm_response.language,
            intent=llm_response.intent,
            issue_category=llm_response.issue_category,
            urgency=llm_response.urgency,
            abuse_flag=llm_response.abuse_flag,
            emergency_flag=llm_response.emergency_flag,
            edge_case=EdgeCaseType.VALID,
            summary=llm_response.summary,
            confidence=llm_response.confidence,
            processing_time_ms=round(elapsed, 2),
            audit_log=audit,
        )
