"""
Layer 3: The Brain — NLP + Smart Routing Microservice

A decoupled, production-grade, async pipeline that transforms raw STT
transcriptions into structured Actionable Intelligence.

Architecture:
    Stage 0  →  NLP Classification (Language, intent, edge cases via nlp_classifier)
    Stage A  →  High-Speed Interceptor (Regex emergency + noise filter)
    Stage B  →  Semantic Analysis     (Sarvam-1 LLM, forced JSON, tenacity retry)
    Stage C  →  Deterministic Mapping  (DEPT_MAPPING dict + mock SQLite FTS5)
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import sqlite3
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import httpx
from pydantic import BaseModel, Field, field_validator
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import SARVAM_API_KEY, SARVAM_API_ENDPOINT, USE_MOCK_NLP
from app.services.nlp_classifier import (
    NLPClassifier,
    NLPInput,
    EdgeCaseType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════


class IntentType(str, Enum):
    """Intent classification labels as required by the spec."""
    NEW_COMPLAINT = "NEW_COMPLAINT"
    STATUS_QUERY = "STATUS_QUERY"
    PRANK = "PRANK"
    FEEDBACK = "FEEDBACK"


class IssueCategory(str, Enum):
    """Civic issue categories."""
    WATER = "Water"
    ELECTRICITY = "Electricity"
    ROAD = "Road"
    WASTE = "Waste"
    HEALTH = "Health"
    EDUCATION = "Education"
    GENERAL = "General"


class ActionType(str, Enum):
    """Deterministic actions driven by the pipeline."""
    CREATE_TICKET = "CREATE_TICKET"
    REPROMPT_USER = "REPROMPT_USER"
    DISCONNECT = "DISCONNECT"
    TRANSFER_HUMAN = "TRANSFER_HUMAN"


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class VoiceInput(BaseModel):
    """
    Simplified input schema — user only provides the transcript.
    Everything else is auto-detected by the system.
    """
    session_id: Union[str, UUID] = Field(..., description="Unique session identifier (UUID or string)")
    transcript: str = Field(..., description="Raw transcript from STT (user's complaint/query)")

    @field_validator("transcript")
    @classmethod
    def transcript_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Transcript cannot be empty or whitespace-only")
        return v


class RoutingData(BaseModel):
    """Nested routing payload."""
    dept_id: str
    priority: int = Field(..., ge=1, le=5)
    summary: str


class RoutingResult(BaseModel):
    """Output schema — the Actionable Intelligence packet."""
    session_id: Union[str, UUID]
    is_emergency: bool = False
    action: ActionType
    routing_data: RoutingData
    # New fields to track auto-detected information
    language: str = "unknown"  # e.g., "hi", "en", "ta"
    intent: str = "OTHER"  # e.g., "NEW_COMPLAINT", "STATUS_QUERY"
    issue_category: str = "General"  # e.g., "Water", "Electricity"
    confidence: float = 0.85  # Classification confidence (0.0-1.0), lower if conflicting signals
    audit_log: List[str] = Field(
        default_factory=list,
        description="Trace of which pipeline stage made the final decision",
    )
    processing_time_ms: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & KEYWORD SETS
# ═══════════════════════════════════════════════════════════════════════════════


EMERGENCY_PATTERN = re.compile(
    r"\b("
    r"fire|aag|ambulance|police|thana|injury|chot|accident|durghatna|"
    r"danger|khatarnak|critical|violence|hinsa|attack|hamla|gas\s*leak|"
    r"electrocution|bijli\s*ka\s*jhatka|snake|saanp|flood|baadh|"
    r"collapse|dhahna|bomb|riot|danga|murder|kidnap|medical\s*emergency"
    r")\b",
    re.IGNORECASE,
)

FILLER_WORDS = frozenset({
    "hello", "hi", "ji", "umm", "uh", "um", "haan", "na", "ok", "okay",
    "yeah", "yep", "nope", "hmm", "huh", "eh", "ah", "bas", "theek",
    "kuch nahi", "koi baat nahi", "pause", "repeat", "what", "hallo",
    "namaste", "namaskar",
})

MIN_WORDS_THRESHOLD = 3


# ═══════════════════════════════════════════════════════════════════════════════
# DEPARTMENT MAPPING (Dict + Mock SQLite FTS5)
# ═══════════════════════════════════════════════════════════════════════════════


DEPT_MAPPING: Dict[str, Dict[str, Any]] = {
    "DEPT_WATER_001": {
        "name": "Water & Sewerage",
        "categories": [IssueCategory.WATER],
        "keywords": ["water", "tap", "pipe", "leak", "sewer", "drain", "sewage",
                      "pani", "nal", "nali", "jal", "pipeline"],
    },
    "DEPT_ELECTRICITY_001": {
        "name": "Electricity & Power",
        "categories": [IssueCategory.ELECTRICITY],
        "keywords": ["electric", "power", "light", "bulb", "meter", "circuit",
                      "bijli", "urja", "transformer", "voltage"],
    },
    "DEPT_ROADS_001": {
        "name": "Roads & Infrastructure",
        "categories": [IssueCategory.ROAD],
        "keywords": ["road", "pothole", "street", "pavement", "highway",
                      "traffic", "sadak", "gaddha", "footpath", "bridge"],
    },
    "DEPT_SANITATION_001": {
        "name": "Sanitation & Waste Management",
        "categories": [IssueCategory.WASTE],
        "keywords": ["garbage", "waste", "trash", "dustbin", "clean",
                      "sanitation", "kachra", "safai", "ganda"],
    },
    "DEPT_HEALTH_001": {
        "name": "Health & Medical",
        "categories": [IssueCategory.HEALTH],
        "keywords": ["health", "hospital", "doctor", "clinic", "medical",
                      "medicine", "vaccine", "dawai", "aspatal"],
    },
    "DEPT_EDUCATION_001": {
        "name": "Education",
        "categories": [IssueCategory.EDUCATION],
        "keywords": ["school", "college", "education", "student", "fees",
                      "admission", "padhai", "vidyalaya"],
    },
    "DEPT_GENERAL_ADMIN": {
        "name": "General Administration",
        "categories": [IssueCategory.GENERAL],
        "keywords": [],
    },
}

GENERAL_ADMIN_ID = "DEPT_GENERAL_ADMIN"


def _build_category_to_dept() -> Dict[str, str]:
    """Pre-compute category → dept_id lookup."""
    mapping: Dict[str, str] = {}
    for dept_id, info in DEPT_MAPPING.items():
        for cat in info["categories"]:
            mapping[cat.value] = dept_id
    return mapping


_CATEGORY_DEPT_MAP = _build_category_to_dept()


def _init_fts5_db() -> sqlite3.Connection:
    """Create an in-memory SQLite FTS5 table for department keyword search."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS dept_fts "
        "USING fts5(dept_id, keywords)"
    )
    for dept_id, info in DEPT_MAPPING.items():
        if info["keywords"]:
            conn.execute(
                "INSERT INTO dept_fts(dept_id, keywords) VALUES (?, ?)",
                (dept_id, " ".join(info["keywords"])),
            )
    conn.commit()
    return conn


# Module-level FTS5 connection (lightweight, in-memory)
_FTS5_CONN: sqlite3.Connection = _init_fts5_db()


def _fts5_lookup(query: str) -> Optional[str]:
    """Search FTS5 index for best department match."""
    try:
        # Sanitize for FTS5 query
        safe_query = re.sub(r"[^\w\s]", "", query)
        tokens = safe_query.lower().split()
        if not tokens:
            return None
        fts_query = " OR ".join(tokens)
        row = _FTS5_CONN.execute(
            "SELECT dept_id FROM dept_fts WHERE dept_fts MATCH ? "
            "ORDER BY rank LIMIT 1",
            (fts_query,),
        ).fetchone()
        return row[0] if row else None
    except Exception:
        logger.debug("FTS5 lookup failed, falling back to dict", exc_info=True)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# SARVAM-1 LLM CLIENT
# ═══════════════════════════════════════════════════════════════════════════════


# The system prompt forces a strict JSON schema out of the LLM.
_SARVAM_SYSTEM_PROMPT = """\
You are a government helpline classifier for India. Analyze the citizen's \
transcript and respond ONLY with valid JSON. No explanation, no markdown, no \
extra text — just the JSON object.

Required JSON schema:
{
  "intent": "<NEW_COMPLAINT | STATUS_QUERY | PRANK | FEEDBACK>",
  "issue_category": "<Water | Electricity | Road | Waste | Health | Education | General>",
  "summary": "<Concise 10-word summary of the citizen's issue>",
  "urgency": <integer 1-5, where 5 is most urgent>
}

Rules:
- If the transcript is nonsensical, abusive, or clearly a prank → intent = PRANK
- If the caller asks about an existing complaint status → intent = STATUS_QUERY
- If the caller provides appreciation or feedback → intent = FEEDBACK
- Otherwise → intent = NEW_COMPLAINT
- urgency 5 = life-threatening, 1 = informational only
"""


class SarvamLLMResponse(BaseModel):
    """Parsed LLM output."""
    intent: IntentType
    issue_category: IssueCategory = IssueCategory.GENERAL
    summary: str = "Unable to summarize"
    urgency: int = Field(default=3, ge=1, le=5)


async def call_sarvam_api(
    transcript: str,
    language_code: str,
    *,
    api_key: str,
    endpoint: str = "https://api.sarvam.ai/v1/chat/completions",
    timeout: float = 10.0,
) -> SarvamLLMResponse:
    """
    Send transcript to Sarvam-1 and parse the forced-JSON response.

    Uses tenacity for automatic retry with exponential backoff on
    timeouts and transient HTTP errors.
    """

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=True,
    )
    async def _do_request() -> dict:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sarvam-1",
                    "messages": [
                        {"role": "system", "content": _SARVAM_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": (
                                f"Language: {language_code}\n"
                                f"Transcript: {transcript}"
                            ),
                        },
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "max_tokens": 200,
                },
            )
            resp.raise_for_status()
            return resp.json()

    raw = await _do_request()

    # Extract the assistant message text
    content_str: str = (
        raw.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "{}")
    )

    return _parse_llm_json(content_str)


def _parse_llm_json(raw_text: str) -> SarvamLLMResponse:
    """
    Safely parse (potentially malformed) LLM JSON.

    Falls back to regex extraction if json.loads fails.
    """
    # Strip markdown code-fence if the LLM wraps its output
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
        return SarvamLLMResponse(**data)
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("Malformed LLM JSON, attempting regex fallback: %s", exc)

    # Regex fallback — try to extract individual fields
    intent_match = re.search(
        r'"intent"\s*:\s*"(NEW_COMPLAINT|STATUS_QUERY|PRANK|FEEDBACK)"',
        raw_text,
        re.IGNORECASE,
    )
    cat_match = re.search(
        r'"issue_category"\s*:\s*"(Water|Electricity|Road|Waste|Health|Education|General)"',
        raw_text,
        re.IGNORECASE,
    )
    summary_match = re.search(r'"summary"\s*:\s*"([^"]{1,120})"', raw_text)
    urgency_match = re.search(r'"urgency"\s*:\s*(\d)', raw_text)

    return SarvamLLMResponse(
        intent=IntentType(intent_match.group(1).upper()) if intent_match else IntentType.NEW_COMPLAINT,
        issue_category=IssueCategory(cat_match.group(1).title()) if cat_match else IssueCategory.GENERAL,
        summary=summary_match.group(1) if summary_match else "Unable to summarize",
        urgency=int(urgency_match.group(1)) if urgency_match else 3,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK SARVAM CLIENT (for dev / tests)
# ═══════════════════════════════════════════════════════════════════════════════


class MockSarvamClient:
    """Deterministic mock that mirrors the real Sarvam-1 JSON schema."""

    _KEYWORD_MAP: Dict[str, IssueCategory] = {
        "water": IssueCategory.WATER,
        "pani": IssueCategory.WATER,
        "pipe": IssueCategory.WATER,
        "leak": IssueCategory.WATER,
        "nal": IssueCategory.WATER,
        "tap": IssueCategory.WATER,
        "nali": IssueCategory.WATER,
        "pipeline": IssueCategory.WATER,
        "electric": IssueCategory.ELECTRICITY,
        "bijli": IssueCategory.ELECTRICITY,
        "power": IssueCategory.ELECTRICITY,
        "light": IssueCategory.ELECTRICITY,
        "transformer": IssueCategory.ELECTRICITY,
        "road": IssueCategory.ROAD,
        "pothole": IssueCategory.ROAD,
        "sadak": IssueCategory.ROAD,
        "gaddha": IssueCategory.ROAD,
        "garbage": IssueCategory.WASTE,
        "kachra": IssueCategory.WASTE,
        "waste": IssueCategory.WASTE,
        "safai": IssueCategory.WASTE,
        "hospital": IssueCategory.HEALTH,
        "doctor": IssueCategory.HEALTH,
        "dawai": IssueCategory.HEALTH,
        "school": IssueCategory.EDUCATION,
        "college": IssueCategory.EDUCATION,
        "padhai": IssueCategory.EDUCATION,
    }

    async def classify(self, transcript: str, language_code: str) -> SarvamLLMResponse:
        lower = transcript.lower()

        # Detect prank / nonsense
        prank_indicators = ["bakwas", "bkl", "prank", "lol", "haha", "chal hat"]
        if any(p in lower for p in prank_indicators):
            return SarvamLLMResponse(
                intent=IntentType.PRANK,
                issue_category=IssueCategory.GENERAL,
                summary="Prank or abusive call detected",
                urgency=1,
            )

        # Detect status query
        status_indicators = ["status", "kya hua", "kab hoga", "update", "tracking"]
        if any(s in lower for s in status_indicators):
            return SarvamLLMResponse(
                intent=IntentType.STATUS_QUERY,
                issue_category=IssueCategory.GENERAL,
                summary="Caller asking about complaint status",
                urgency=2,
            )

        # Detect feedback
        feedback_indicators = ["thank", "dhanyavad", "shukriya", "good work", "feedback", "appreciate"]
        if any(f in lower for f in feedback_indicators):
            return SarvamLLMResponse(
                intent=IntentType.FEEDBACK,
                issue_category=IssueCategory.GENERAL,
                summary="Positive feedback from citizen",
                urgency=1,
            )

        # Default: NEW_COMPLAINT with category detection
        category = IssueCategory.GENERAL
        for keyword, cat in self._KEYWORD_MAP.items():
            if keyword in lower:
                category = cat
                break

        urgency = 3
        urgent_words = ["urgent", "jaldi", "turant", "bahut", "bohot", "immediately", "tut"]
        if any(u in lower for u in urgent_words):
            urgency = 4

        summary_words = transcript.split()[:10]
        summary = " ".join(summary_words)
        if len(summary) > 60:
            summary = summary[:57] + "..."

        return SarvamLLMResponse(
            intent=IntentType.NEW_COMPLAINT,
            issue_category=category,
            summary=summary,
            urgency=urgency,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SMART ROUTER — THE 3-STAGE PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════


class SmartRouter:
    """
    Transforms raw, noisy transcriptions into structured Actionable Intelligence
    while minimising latency and API costs.

    Stages:
        A — High-Speed Interceptor (regex emergency + noise filter)
        B — Semantic Analysis (Sarvam-1 async LLM call)
        C — Deterministic Department Mapping (dict + FTS5 fallback)
    """

    def __init__(
        self,
        *,
        sarvam_api_key: Optional[str] = None,
        sarvam_endpoint: str = "https://api.sarvam.ai/v1/chat/completions",
        sarvam_timeout: float = 10.0,
        use_mock: bool = False,
    ) -> None:
        # Use injected key or fallback to config
        api_key = sarvam_api_key or SARVAM_API_KEY
        use_mock_flag = use_mock or USE_MOCK_NLP or (api_key is None)

        # Initialize new NLP classifier (handles language detection, intent, edge cases)
        self._nlp_classifier = NLPClassifier(
            sarvam_api_key=api_key,
            sarvam_endpoint=sarvam_endpoint or SARVAM_API_ENDPOINT,
            use_mock=use_mock_flag,
        )

        logger.info(
            "SmartRouter initialised with NLPClassifier (mode=%s)",
            "MOCK" if use_mock_flag else "PRODUCTION",
        )

    # ── public entry point ──────────────────────────────────────────────

    async def process(self, voice_input: VoiceInput) -> RoutingResult:
        """
        Run the unified NLP + routing pipeline and return a RoutingResult.
        
        System auto-detects:
        - Language (no manual input needed)
        - Intent classification
        - Edge cases (emergency, silence, abuse)
        - Department routing based on issue category
        """
        start = time.perf_counter()
        audit: List[str] = []

        # ── Stage 0: Unified NLP Classification ─────────────────────
        # Auto-detects language, intent, urgency, and edge cases
        try:
            nlp_input = NLPInput(
                session_id=voice_input.session_id,
                transcript=voice_input.transcript,
                # Language will be auto-detected (detected_language=None)
            )
            nlp_result = await self._nlp_classifier.classify(nlp_input)
            audit.extend(nlp_result.audit_log)
            
            logger.debug(
                "NLP classification: language=%s, intent=%s, edge_case=%s",
                nlp_result.language.value,
                nlp_result.intent.value,
                nlp_result.edge_case.value,
            )
        except Exception as exc:
            logger.error("NLP classification failed: %s", exc, exc_info=True)
            audit.append(f"NLP_CLASSIFY: FAILED ({exc!r})")
            elapsed = (time.perf_counter() - start) * 1000
            return RoutingResult(
                session_id=voice_input.session_id,
                is_emergency=False,
                action=ActionType.DISCONNECT,
                routing_data=RoutingData(
                    dept_id=GENERAL_ADMIN_ID,
                    priority=1,
                    summary="NLP processing error. Please try again.",
                ),
                language="unknown",
                intent="OTHER",
                issue_category="General",
                confidence=0.0,
                audit_log=audit,
                processing_time_ms=round(elapsed, 2),
            )

        # ── Handle edge cases ───────────────────────────────────────
        if nlp_result.edge_case == EdgeCaseType.EMERGENCY:
            elapsed = (time.perf_counter() - start) * 1000
            audit.append("EDGE_CASE_RESPONSE: Emergency → TRANSFER_HUMAN")
            return RoutingResult(
                session_id=voice_input.session_id,
                is_emergency=True,
                action=ActionType.TRANSFER_HUMAN,
                routing_data=RoutingData(
                    dept_id="DEPT_EMERGENCY_911",
                    priority=5,
                    summary=nlp_result.summary,
                ),
                language=nlp_result.language.value,
                intent=nlp_result.intent.value,
                issue_category=nlp_result.issue_category.value,
                confidence=nlp_result.confidence,
                audit_log=audit,
                processing_time_ms=round(elapsed, 2),
            )

        if nlp_result.edge_case == EdgeCaseType.SILENCE:
            elapsed = (time.perf_counter() - start) * 1000
            audit.append("EDGE_CASE_RESPONSE: Silence → REPROMPT_USER")
            return RoutingResult(
                session_id=voice_input.session_id,
                is_emergency=False,
                action=ActionType.REPROMPT_USER,
                routing_data=RoutingData(
                    dept_id=GENERAL_ADMIN_ID,
                    priority=1,
                    summary=nlp_result.summary,
                ),
                language=nlp_result.language.value,
                intent=nlp_result.intent.value,
                issue_category=nlp_result.issue_category.value,
                confidence=nlp_result.confidence,
                audit_log=audit,
                processing_time_ms=round(elapsed, 2),
            )

        if nlp_result.edge_case == EdgeCaseType.ABUSE:
            elapsed = (time.perf_counter() - start) * 1000
            audit.append("EDGE_CASE_RESPONSE: Abuse → WARN_AND_REPROMPT")
            return RoutingResult(
                session_id=voice_input.session_id,
                is_emergency=False,
                action=ActionType.REPROMPT_USER,
                routing_data=RoutingData(
                    dept_id=GENERAL_ADMIN_ID,
                    priority=2,
                    summary="Abusive content detected. Please maintain courtesy.",
                ),
                language=nlp_result.language.value,
                intent="ABUSE",
                issue_category=nlp_result.issue_category.value,
                confidence=nlp_result.confidence,
                audit_log=audit,
                processing_time_ms=round(elapsed, 2),
            )

        # ── Stage C: Deterministic Department Routing ───────────────
        dept_id = self._stage_c_route_department(
            nlp_result.issue_category,
            voice_input.transcript,
        )
        audit.append(f"STAGE_C: Routed to {dept_id}")

        # ── Determine action based on intent ────────────────────────
        action = self._decide_action(nlp_result.intent)
        audit.append(f"ACTION: {action.value}")

        elapsed = (time.perf_counter() - start) * 1000
        return RoutingResult(
            session_id=voice_input.session_id,
            is_emergency=nlp_result.emergency_flag,
            action=action,
            routing_data=RoutingData(
                dept_id=dept_id,
                priority=nlp_result.urgency,
                summary=nlp_result.summary,
            ),
            language=nlp_result.language.value,
            intent=nlp_result.intent.value,
            issue_category=nlp_result.issue_category.value,
            confidence=nlp_result.confidence,
            audit_log=audit,
            processing_time_ms=round(elapsed, 2),
        )

    # ── Stage C: Deterministic Department Mapping ───────────────────────

    @staticmethod
    def _stage_c_route_department(
        issue_category: IssueCategory,
        transcript: str,
    ) -> str:
        """
        Map issue_category → dept_id.

        1. Direct dict lookup by category.
        2. If category is GENERAL, try SQLite FTS5 on transcript keywords.
        3. Fallback to GENERAL_ADMIN.
        """
        # 1. Direct category lookup
        dept_id = _CATEGORY_DEPT_MAP.get(issue_category.value)
        if dept_id and dept_id != GENERAL_ADMIN_ID:
            return dept_id

        # 2. FTS5 keyword fallback
        fts_result = _fts5_lookup(transcript)
        if fts_result:
            return fts_result

        # 3. Hard fallback
        return GENERAL_ADMIN_ID

    # ── Action decision ─────────────────────────────────────────────────

    @staticmethod
    def _decide_action(intent) -> ActionType:
        """
        Map intent → action.
        
        Handles both old IntentType (from old router) and new from nlp_classifier.
        """
        # Handle new intent types from nlp_classifier
        intent_str = intent.value if hasattr(intent, 'value') else str(intent)
        
        action_map = {
            "NEW_COMPLAINT": ActionType.CREATE_TICKET,
            "STATUS_QUERY": ActionType.CREATE_TICKET,
            "FEEDBACK": ActionType.CREATE_TICKET,
            "PRANK": ActionType.DISCONNECT,
            "ABUSE": ActionType.DISCONNECT,
            "OTHER": ActionType.REPROMPT_USER,
        }
        
        return action_map.get(intent_str, ActionType.REPROMPT_USER)
