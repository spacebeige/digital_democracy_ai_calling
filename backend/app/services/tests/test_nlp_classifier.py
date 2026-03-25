"""
Tests for NLP Classifier
Covers language detection, intent classification, edge case handling, and abuse detection.
"""

import pytest
from uuid import uuid4
from app.services.nlp_classifier import (
    NLPClassifier,
    NLPInput,
    LanguageCode,
    IntentType,
    IssueCategory,
    EdgeCaseType,
    EdgeCaseDetector,
    MockSarvamClient,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def classifier():
    """Initialize classifier with mock mode."""
    return NLPClassifier(sarvam_api_key=None, use_mock=True)


@pytest.fixture
def edge_detector():
    """Initialize edge case detector."""
    return EdgeCaseDetector()


@pytest.fixture
def mock_client():
    """Initialize mock Sarvam client."""
    return MockSarvamClient()


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestEmergencyDetection:
    """Test emergency keyword detection."""

    def test_english_fire_emergency(self, edge_detector):
        result = edge_detector.check_emergency("There is fire in my building!")
        assert result.detected is True
        assert result.case_type == EdgeCaseType.EMERGENCY

    def test_hindi_ambulance_emergency(self, edge_detector):
        result = edge_detector.check_emergency("मुझे एम्बुलेंस चाहिए")
        assert result.detected is True

    def test_hindi_emergency_keyword(self, edge_detector):
        result = edge_detector.check_emergency("मेरे घर में बहुत खतरनाक स्थिति है")
        assert result.detected is True

    def test_hinglish_accident(self, edge_detector):
        result = edge_detector.check_emergency("Mera bhai accident mein hai!")
        assert result.detected is True

    def test_non_emergency_complaint(self, edge_detector):
        result = edge_detector.check_emergency("Mere ghar ke samne pothole hai")
        assert result.detected is False


class TestSilenceDetection:
    """Test silence and empty input detection."""

    def test_empty_transcript(self, edge_detector):
        result = edge_detector.check_silence("")
        assert result.detected is True
        assert result.case_type == EdgeCaseType.SILENCE

    def test_whitespace_only(self, edge_detector):
        result = edge_detector.check_silence("   \n\t  ")
        assert result.detected is True

    def test_single_word(self, edge_detector):
        result = edge_detector.check_silence("hello")
        assert result.detected is True

    def test_two_words(self, edge_detector):
        result = edge_detector.check_silence("hello ji")
        assert result.detected is True

    def test_filler_only(self, edge_detector):
        result = edge_detector.check_silence("umm huh okay")
        assert result.detected is True

    def test_valid_three_words(self, edge_detector):
        result = edge_detector.check_silence("pothole in street")
        assert result.detected is False

    def test_very_short_chars(self, edge_detector):
        result = edge_detector.check_silence("ab")
        assert result.detected is True


class TestAbuseDetection:
    """Test abuse and toxicity detection."""

    def test_english_abuse_keyword(self, edge_detector):
        result = edge_detector.check_abuse("This is stupid and bullshit")
        assert result.detected is True
        assert result.case_type == EdgeCaseType.ABUSE

    def test_hindi_abuse_keyword(self, edge_detector):
        result = edge_detector.check_abuse("साला बकवास मत करो")
        assert result.detected is True

    def test_clean_complaint(self, edge_detector):
        result = edge_detector.check_abuse("Water is leaking from my tap")
        assert result.detected is False

    def test_hinglish_abuse(self, edge_detector):
        result = edge_detector.check_abuse("Tu chutiya hai, kya kar raha hai")
        assert result.detected is True


# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE DETECTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestLanguageDetection:
    """Test language detection."""

    @pytest.mark.asyncio
    async def test_english_detection(self, mock_client):
        result = await mock_client.classify("Water is leaking from the tap")
        assert result.language == LanguageCode.ENGLISH

    @pytest.mark.asyncio
    async def test_hindi_detection(self, mock_client):
        result = await mock_client.classify("मेरे घर के सामने सड़क में गड्ढा है")
        assert result.language == LanguageCode.HINDI

    @pytest.mark.asyncio
    async def test_hinglish_detection(self, mock_client):
        result = await mock_client.classify("Mera ghar mein water leak ho gaya")
        # Should detect mix of English + Hindi
        assert result.language in [LanguageCode.HINGLISH, LanguageCode.ENGLISH]


# ═══════════════════════════════════════════════════════════════════════════════
# INTENT CLASSIFICATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestIntentClassification:
    """Test intent classification."""

    @pytest.mark.asyncio
    async def test_new_complaint_intent(self, mock_client):
        result = await mock_client.classify("Water is leaking from my kitchen tap")
        assert result.intent == IntentType.NEW_COMPLAINT

    @pytest.mark.asyncio
    async def test_status_query_intent(self, mock_client):
        result = await mock_client.classify("What is the status of my complaint?")
        assert result.intent == IntentType.STATUS_QUERY

    @pytest.mark.asyncio
    async def test_feedback_intent(self, mock_client):
        result = await mock_client.classify("Thank you for your excellent work")
        assert result.intent == IntentType.FEEDBACK

    @pytest.mark.asyncio
    async def test_abuse_intent(self, mock_client):
        result = await mock_client.classify("This is stupid bullshit")
        assert result.intent == IntentType.ABUSE


# ═══════════════════════════════════════════════════════════════════════════════
# ISSUE CATEGORY MAPPING TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestIssueCategoryMapping:
    """Test issue category detection."""

    @pytest.mark.asyncio
    async def test_water_category(self, mock_client):
        result = await mock_client.classify("Water is leaking from the tap")
        assert result.issue_category == IssueCategory.WATER

    @pytest.mark.asyncio
    async def test_road_category(self, mock_client):
        result = await mock_client.classify("Pothole in the middle of the street")
        assert result.issue_category == IssueCategory.ROAD

    @pytest.mark.asyncio
    async def test_electricity_category(self, mock_client):
        result = await mock_client.classify("My electric meter is broken")
        assert result.issue_category == IssueCategory.ELECTRICITY

    @pytest.mark.asyncio
    async def test_waste_category(self, mock_client):
        result = await mock_client.classify("Garbage is not being collected")
        assert result.issue_category == IssueCategory.WASTE

    @pytest.mark.asyncio
    async def test_health_category(self, mock_client):
        result = await mock_client.classify("I need to visit a doctor")
        assert result.issue_category == IssueCategory.HEALTH

    @pytest.mark.asyncio
    async def test_education_category(self, mock_client):
        result = await mock_client.classify("School fees are too high")
        assert result.issue_category == IssueCategory.EDUCATION


# ═══════════════════════════════════════════════════════════════════════════════
# URGENCY SCORING TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestUrgencyScoring:
    """Test urgency score calculation."""

    @pytest.mark.asyncio
    async def test_emergency_urgency(self, mock_client):
        result = await mock_client.classify("There is a fire in my building!")
        assert result.urgency >= 4

    @pytest.mark.asyncio
    async def test_urgent_keyword_urgency(self, mock_client):
        result = await mock_client.classify("Please fix this urgently")
        assert result.urgency >= 3

    @pytest.mark.asyncio
    async def test_normal_complaint_urgency(self, mock_client):
        result = await mock_client.classify("There is a small pothole")
        assert result.urgency >= 1 and result.urgency <= 5


# ═══════════════════════════════════════════════════════════════════════════════
# FULL PIPELINE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestFullNLPPipeline:
    """Test complete NLP classification pipeline."""

    @pytest.mark.asyncio
    async def test_emergency_fast_path(self, classifier):
        """Emergency should be detected immediately."""
        nlp_input = NLPInput(
            session_id=uuid4(),
            transcript="There is a fire in my apartment!",
        )
        result = await classifier.classify(nlp_input)
        assert result.edge_case == EdgeCaseType.EMERGENCY
        assert result.emergency_flag is True

    @pytest.mark.asyncio
    async def test_silence_detection_in_pipeline(self, classifier):
        """Silence should be caught early."""
        nlp_input = NLPInput(
            session_id=uuid4(),
            transcript="",
        )
        result = await classifier.classify(nlp_input)
        assert result.edge_case == EdgeCaseType.SILENCE

    @pytest.mark.asyncio
    async def test_abuse_detection_in_pipeline(self, classifier):
        """Abuse should be detected and flagged."""
        nlp_input = NLPInput(
            session_id=uuid4(),
            transcript="This is bullshit and stupid",
        )
        result = await classifier.classify(nlp_input)
        assert result.edge_case == EdgeCaseType.ABUSE
        assert result.abuse_flag is True

    @pytest.mark.asyncio
    async def test_valid_water_complaint(self, classifier):
        """Valid water complaint should be classified correctly."""
        nlp_input = NLPInput(
            session_id=uuid4(),
            transcript="Water is leaking from my kitchen tap",
        )
        result = await classifier.classify(nlp_input)
        assert result.edge_case == EdgeCaseType.VALID
        assert result.intent == IntentType.NEW_COMPLAINT
        assert result.issue_category == IssueCategory.WATER
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_hindi_water_complaint(self, classifier):
        """Hindi complaint should be classified correctly."""
        nlp_input = NLPInput(
            session_id=uuid4(),
            transcript="मेरे घर में पानी का नल टूट गया है",
        )
        result = await classifier.classify(nlp_input)
        assert result.edge_case == EdgeCaseType.VALID
        assert result.language == LanguageCode.HINDI

    @pytest.mark.asyncio
    async def test_audit_trail_present(self, classifier):
        """Audit trail should be populated."""
        nlp_input = NLPInput(
            session_id=uuid4(),
            transcript="Water leak in kitchen",
        )
        result = await classifier.classify(nlp_input)
        assert len(result.audit_log) > 0

    @pytest.mark.asyncio
    async def test_processing_time_tracked(self, classifier):
        """Processing time should be tracked."""
        nlp_input = NLPInput(
            session_id=uuid4(),
            transcript="Water leak in kitchen",
        )
        result = await classifier.classify(nlp_input)
        assert result.processing_time_ms >= 0


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestInputValidation:
    """Test input validation."""

    def test_empty_transcript_validation(self):
        """Empty transcripts should be allowed at input level (caught by silence detector)."""
        nlp_input = NLPInput(
            session_id=uuid4(),
            transcript="",
        )
        assert nlp_input.transcript == ""

    def test_whitespace_only_validation(self):
        """Whitespace-only transcripts should be allowed at input level (caught by silence detector)."""
        nlp_input = NLPInput(
            session_id=uuid4(),
            transcript="   \n\t   ",
        )
        # Should be trimmed to empty string
        assert nlp_input.transcript == ""


# ═══════════════════════════════════════════════════════════════════════════════
# HINGLISH & REGIONAL LANGUAGE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestRegionalLanguages:
    """Test regional language detection and handling."""

    @pytest.mark.asyncio
    async def test_tamil_script_detection(self, mock_client):
        result = await mock_client.classify("நீர் கசிவு உள்ளது")
        # Tamil script should be detected
        assert result.language == LanguageCode.TAMIL

    @pytest.mark.asyncio
    async def test_hinglish_mixed_detection(self, mock_client):
        result = await mock_client.classify(
            "Mera ghar ke samne sadak mein bohot badi pothole hai"
        )
        # Mix of English + transliterated Hindi
        assert result.language in [LanguageCode.ENGLISH, LanguageCode.HINGLISH]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
