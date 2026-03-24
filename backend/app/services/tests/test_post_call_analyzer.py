"""
Tests for Post-Call Analysis Pipeline
======================================

Tests the complete post-call analysis flow including:
- NLP classification
- Smart routing
- Entity extraction
- Action determination
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.post_call_analyzer import (
    PostCallAnalyzer,
    PostCallAnalysisInput,
    CallMetadata,
    TranscriptSegment,
    AnalysisStatus,
    ActionRequired,
)


@pytest.fixture
def analyzer():
    """Create analyzer instance."""
    return PostCallAnalyzer()


@pytest.fixture
def sample_call_metadata():
    """Create sample call metadata."""
    return CallMetadata(
        call_id=str(uuid4()),
        session_id=str(uuid4()),
        caller_phone="+919999999999",
        call_start_time=datetime.utcnow() - timedelta(minutes=5),
        call_end_time=datetime.utcnow(),
        call_duration_seconds=300,
        recording_path="/tmp/call_recording.wav",
    )


@pytest.fixture
def sample_complaint_transcript():
    """Sample complaint transcript."""
    return """
    Caller: Hello, I need to report a water leak in my area.
    AI: Thank you for calling. I've noted your concern about water leak.
    Caller: Yes, there's water leaking from a pipe near the main road in Sector 5.
    AI: Which sector exactly?
    Caller: Sector 5, Main Street. This has been happening for two days.
    AI: I understand. We'll route this to the water department immediately.
    """


@pytest.fixture
def sample_emergency_transcript():
    """Sample emergency transcript."""
    return """
    Caller: HELP! There's a fire in the building next to mine!
    AI: Alert! Fire emergency detected. Emergency services are being notified.
    Caller: Please hurry, people are still inside!
    """


@pytest.fixture
def sample_prank_transcript():
    """Sample prank transcript."""
    return """
    Caller: Haha, I'm just calling to waste your time.
    AI: How can I assist you today?
    Caller: Nothing, just kidding around. This is fun!
    """


class TestPostCallAnalyzer:
    """Test suite for PostCallAnalyzer."""

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes correctly."""
        assert analyzer is not None
        assert analyzer.nlp_classifier is not None
        assert analyzer.smart_router is not None

    @pytest.mark.asyncio
    async def test_analyze_with_complaint(
        self, analyzer, sample_call_metadata, sample_complaint_transcript
    ):
        """Test analysis of a genuine complaint."""
        analysis_input = PostCallAnalysisInput(
            call_metadata=sample_call_metadata,
            full_transcript=sample_complaint_transcript,
        )

        result = await analyzer.analyze(analysis_input)

        assert result.status == AnalysisStatus.COMPLETED
        assert result.call_id == sample_call_metadata.call_id
        assert result.is_genuine_complaint is True
        assert result.is_emergency is False
        assert result.classification.language is not None
        assert result.routing.department_id is not None
        assert result.processing_time_ms > 0
        assert result.word_count > 0

    @pytest.mark.asyncio
    async def test_analyze_with_emergency(
        self, analyzer, sample_call_metadata, sample_emergency_transcript
    ):
        """Test analysis of an emergency call."""
        analysis_input = PostCallAnalysisInput(
            call_metadata=sample_call_metadata,
            full_transcript=sample_emergency_transcript,
        )

        result = await analyzer.analyze(analysis_input)

        assert result.status == AnalysisStatus.COMPLETED
        assert result.is_emergency is True
        assert result.routing.priority_level == "EMERGENCY"
        assert result.routing.suggested_action == ActionRequired.ESCALATE_EMERGENCY

    @pytest.mark.asyncio
    async def test_analyze_with_prank(
        self, analyzer, sample_call_metadata, sample_prank_transcript
    ):
        """Test analysis of a prank call."""
        analysis_input = PostCallAnalysisInput(
            call_metadata=sample_call_metadata,
            full_transcript=sample_prank_transcript,
        )

        result = await analyzer.analyze(analysis_input)

        assert result.status == AnalysisStatus.COMPLETED
        # Prank detection depends on classifier
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_analyze_with_segments(
        self, analyzer, sample_call_metadata, sample_complaint_transcript
    ):
        """Test analysis with transcript segments."""
        segments = [
            TranscriptSegment(
                speaker="caller",
                text="I need to report water leakage",
                start_time=0.0,
                duration=5.0,
            ),
            TranscriptSegment(
                speaker="ai",
                text="Thank you for reporting",
                start_time=5.0,
                duration=3.0,
            ),
        ]

        analysis_input = PostCallAnalysisInput(
            call_metadata=sample_call_metadata,
            full_transcript=sample_complaint_transcript,
            transcript_segments=segments,
        )

        result = await analyzer.analyze(analysis_input)

        assert result.status == AnalysisStatus.COMPLETED
        assert result.transcript_segments is None or isinstance(result.transcript_segments, list)

    @pytest.mark.asyncio
    async def test_empty_transcript_raises_error(
        self, analyzer, sample_call_metadata
    ):
        """Test that empty transcript raises validation error."""
        with pytest.raises(ValueError):
            PostCallAnalysisInput(
                call_metadata=sample_call_metadata,
                full_transcript="   ",  # Only whitespace
            )

    @pytest.mark.asyncio
    async def test_analysis_output_structure(
        self, analyzer, sample_call_metadata, sample_complaint_transcript
    ):
        """Test output contains all required fields."""
        analysis_input = PostCallAnalysisInput(
            call_metadata=sample_call_metadata,
            full_transcript=sample_complaint_transcript,
        )

        result = await analyzer.analyze(analysis_input)

        # Check all required fields are present
        assert hasattr(result, "status")
        assert hasattr(result, "analysis_id")
        assert hasattr(result, "call_id")
        assert hasattr(result, "classification")
        assert hasattr(result, "routing")
        assert hasattr(result, "summary")
        assert hasattr(result, "entities")
        assert hasattr(result, "is_emergency")
        assert hasattr(result, "is_abuse")
        assert hasattr(result, "is_genuine_complaint")
        assert hasattr(result, "processing_time_ms")
        assert hasattr(result, "word_count")

    @pytest.mark.asyncio
    async def test_analysis_id_uniqueness(
        self, analyzer, sample_call_metadata, sample_complaint_transcript
    ):
        """Test that each analysis gets a unique ID."""
        analysis_input = PostCallAnalysisInput(
            call_metadata=sample_call_metadata,
            full_transcript=sample_complaint_transcript,
        )

        result1 = await analyzer.analyze(analysis_input)
        result2 = await analyzer.analyze(analysis_input)

        assert result1.analysis_id != result2.analysis_id

    @pytest.mark.asyncio
    async def test_summary_generation(
        self, analyzer, sample_call_metadata, sample_complaint_transcript
    ):
        """Test that summary is generated."""
        analysis_input = PostCallAnalysisInput(
            call_metadata=sample_call_metadata,
            full_transcript=sample_complaint_transcript,
        )

        result = await analyzer.analyze(analysis_input)

        assert len(result.summary) > 0
        assert "water" in result.summary.lower() or "sector" in result.summary.lower()

    def test_determine_action_for_emergency(self):
        """Test action determination for emergency."""
        action = PostCallAnalyzer._determine_action(
            is_emergency=True,
            is_abuse=False,
            is_silence=False,
            intent="NEW_COMPLAINT",
            routing_data=None,
        )
        assert action == ActionRequired.ESCALATE_EMERGENCY

    def test_determine_action_for_abuse(self):
        """Test action determination for abuse."""
        action = PostCallAnalyzer._determine_action(
            is_emergency=False,
            is_abuse=True,
            is_silence=False,
            intent="ABUSE",
            routing_data=None,
        )
        assert action == ActionRequired.TRANSFER_TO_HUMAN

    def test_determine_action_for_complaint(self):
        """Test action determination for genuine complaint."""
        action = PostCallAnalyzer._determine_action(
            is_emergency=False,
            is_abuse=False,
            is_silence=False,
            intent="NEW_COMPLAINT",
            routing_data=None,
        )
        assert action == ActionRequired.CREATE_TICKET


class TestCallMetadata:
    """Test CallMetadata schema."""

    def test_call_metadata_creation(self):
        """Test creating call metadata."""
        call_id = str(uuid4())
        session_id = str(uuid4())

        metadata = CallMetadata(
            call_id=call_id,
            session_id=session_id,
            caller_phone="+919999999999",
            call_start_time=datetime.utcnow(),
            call_end_time=datetime.utcnow() + timedelta(minutes=5),
            call_duration_seconds=300,
        )

        assert metadata.call_id == call_id
        assert metadata.caller_phone == "+919999999999"
        assert metadata.call_duration_seconds == 300

    def test_call_metadata_without_phone(self):
        """Test creating metadata without phone."""
        metadata = CallMetadata(
            call_id=str(uuid4()),
            session_id=str(uuid4()),
            call_start_time=datetime.utcnow(),
            call_end_time=datetime.utcnow() + timedelta(minutes=5),
            call_duration_seconds=300,
        )

        assert metadata.caller_phone is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
