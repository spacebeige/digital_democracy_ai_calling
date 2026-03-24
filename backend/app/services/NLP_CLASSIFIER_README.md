# NLP Classifier: Language Detection, Intent Classification & Edge Cases

## Overview

The **NLP Classifier** is a production-ready module that intelligently processes citizen transcripts for:

- **Language Detection**: Hindi, English, Hinglish, Tamil, Telugu, Bengali, Marathi, Kannada, Malayalam, Punjabi
- **Intent Classification**: NEW_COMPLAINT, STATUS_QUERY, FEEDBACK, ABUSE, OTHER
- **Edge-Case Handling**: Emergency detection, silence/noise filtering, abuse flagging
- **Abuse Detection**: Lexicon-based + optional LLM confirmation
- **Structured Output**: JSON schema with confidence scores and audit trails

## Architecture

```
Transcript Input
    ↓
┌─────────────────────────────────────────┐
│ Stage 0: Edge-Case Pre-Checks (Rules)  │
│ ├─ Emergency (regex keywords)          │
│ ├─ Silence (length, filler-only)       │
│ └─ Abuse (lexicon match)                │
└──────────────┬──────────────────────────┘
    If PASS ↓
┌─────────────────────────────────────────┐
│ Stage 1: Sarvam-1 LLM Classification   │
│ ├─ Language detection                  │
│ ├─ Intent classification               │
│ ├─ Issue category mapping              │
│ ├─ Urgency scoring                     │
│ └─ Abuse flag (fallback)               │
└──────────────┬──────────────────────────┘
               ↓
    Structured NLPOutput
    (language, intent, category, 
     edge_case, confidence, audit_log)
```

## Setup & Configuration

### 1. Install Dependencies

Already in `backend/requirements.txt`:
```
httpx>=0.24.0          # Async HTTP for Sarvam API
pydantic>=2.0.0        # Data validation
tenacity>=8.0.0        # Retry logic
python-dotenv>=0.21.0  # Environment management
```

### 2. Configure Environment

**⚠️ IMPORTANT: Never commit API keys to code!**

Create `.env` file in backend root (ignored by `.gitignore`):

```env
# ─ Sarvam-1 API (Language understanding) ─
SARVAM_API_KEY=sk_your_actual_key_here
SARVAM_API_ENDPOINT=https://api.sarvam.ai/v1/chat/completions
SARVAM_TIMEOUT=10.0
SARVAM_MAX_RETRIES=3

# ─ NLP Classifier ─
USE_MOCK_NLP=false      # Set to 'true' for mock (dev mode)

# ─ Other services ─
STT_API=http://localhost:9000
TTS_API=http://localhost:9001
LLM_API=http://localhost:9002
```

**To get Sarvam API Key:**
1. Visit: https://www.sarvam.ai/
2. Sign up and create an API key
3. Copy to `.env` (NOT to code/chat!)
4. Rotate if exposed (security best practice)

### 3. Runtime Setup

**Load from environment (FastAPI startup):**

```python
from app.config import SARVAM_API_KEY, USE_MOCK_NLP
from app.services.nlp_classifier import NLPClassifier

# Initialized once at app startup
nlp_classifier = NLPClassifier(
    sarvam_api_key=SARVAM_API_KEY,
    use_mock=USE_MOCK_NLP,
)
```

## Usage

### Basic Python Usage

```python
from app.services.nlp_classifier import NLPClassifier, NLPInput
from uuid import uuid4
import asyncio

classifier = NLPClassifier(sarvam_api_key="your_key", use_mock=False)

async def classify_transcript():
    result = await classifier.classify(NLPInput(
        session_id=uuid4(),
        transcript="Water is leaking from my kitchen tap",
    ))
    
    print(f"Language: {result.language.value}")
    print(f"Intent: {result.intent.value}")
    print(f"Category: {result.issue_category.value}")
    print(f"Urgency: {result.urgency}/5")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Edge Case: {result.edge_case.value}")
    print(f"Processing Time: {result.processing_time_ms}ms")
    print(f"Audit Trail: {result.audit_log}")

asyncio.run(classify_transcript())
```

### FastAPI Integration

Already integrated in `SmartRouter`:

```python
# backend/app/services/smart_router.py
from app.services.nlp_classifier import NLPClassifier, NLPInput

router = SmartRouter(sarvam_api_key=None)  # Uses config
result = await router.process(voice_input)
```

## Features & Output

### Language Detection

Detects and normalizes:
- **Hindi** (Devanagari script)
- **English** (Latin script)
- **Hinglish** (Mixed Hindi + English)
- **Regional**: Tamil, Telugu, Bengali, Marathi, Kannada, Malayalam, Punjabi

Example:
```json
"language": "hinglish"  // "Mera ghar ke samne pothole hai"
```

### Intent Classification

Maps user intent to action:

| Intent | Meaning | Example |
|--------|---------|---------|
| NEW_COMPLAINT | Reporting civic issue | "Water is leaking" |
| STATUS_QUERY | Asking about complaint status | "What's the status?" |
| FEEDBACK | Appreciation or suggestion | "Thank you for help" |
| ABUSE | Profanity or hostile language | "This is bullshit" |
| OTHER | Unclear or off-topic | Random rambling |

### Issue Categories

Maps complaints to departments:

| Category | Keywords | Example |
|----------|----------|---------|
| Water | water, pani, tap, leak, pipe, nali | "Tap is broken" |
| Electricity | electric, bijli, power, light, meter | "No electricity" |
| Road | road, pothole, sadak, gaddha, street | "Pothole here" |
| Waste | garbage, kachra, waste, trash, safai | "Garbage pile" |
| Health | hospital, doctor, health, aspatal, dawai | "Need doctor" |
| Education | school, college, padhai, student, fees | "Fees too high" |
| General | (fallback for unknown) | "Not sure" |

### Urgency Scoring

Numeric scale 1-5:

| Score | Level | Trigger |
|-------|-------|---------|
| 5 | EMERGENCY | Fire, ambulance, accident, police |
| 4 | URGENT | "Please fix urgently", "immediately" |
| 3 | NORMAL | Standard complaint |
| 2 | LOW | Informational |
| 1 | MIN | Status query only |

### Edge Cases (Pre-checked)

**Emergency** → Fast path, transfer to human immediately
```
Keywords: fire, ambulance, police, accident, gas leak, critical, 
          injury, attack, violence, electrocution, snake, etc.
```

**Silence** → Prompt user for more details
```
Triggers:
- Empty or whitespace-only input
- < 3 words total
- < 5 characters
- Only filler words (um, huh, okay, hi, yes, etc.)
```

**Abuse** → Flag and escalate
```
Lexicon: bakwas, chutiya, madarchod, benchod, stupid, 
         bullshit, asshole, damn, moron, fuck, etc.
```

### Response Schema

```python
NLPOutput(
    session_id: UUID,           # Unique call ID
    transcript: str,            # Original input
    language: LanguageCode,     # Detected language
    intent: IntentType,         # Classification
    issue_category: IssueCategory,  # Department mapping
    urgency: int,               # 1-5 priority score
    abuse_flag: bool,           # Abuse detected?
    emergency_flag: bool,       # Emergency detected?
    edge_case: EdgeCaseType,    # EMERGENCY | SILENCE | ABUSE | VALID
    edge_case_reason: str,      # Why edge case triggered
    summary: str,               # Concise issue summary
    confidence: float,          # 0.0-1.0 trust score
    processing_time_ms: float,  # Latency
    audit_log: List[str],       # Decision trail
)
```

## Example Flows

### Flow 1: Normal Water Complaint (Hindi)

**Input:**
```
Transcript: "Mere ghar mein water leak ho gaya"
```

**Output:**
```json
{
  "language": "hi",
  "intent": "NEW_COMPLAINT",
  "issue_category": "Water",
  "urgency": 3,
  "abuse_flag": false,
  "emergency_flag": false,
  "edge_case": "VALID",
  "confidence": 0.85,
  "processing_time_ms": 342
}
```

### Flow 2: Emergency (Immediate Transfer)

**Input:**
```
Transcript: "There is a fire in my building!"
```

**Output:**
```json
{
  "language": "en",
  "intent": "NEW_COMPLAINT",
  "issue_category": "General",
  "urgency": 5,
  "abuse_flag": false,
  "emergency_flag": true,
  "edge_case": "EMERGENCY",
  "edge_case_reason": "Emergency keyword detected",
  "confidence": 1.0,
  "processing_time_ms": 12
}

Action: TRANSFER_HUMAN (no LLM call needed)
```

### Flow 3: Silence (Reprompt)

**Input:**
```
Transcript: "umm hello"
```

**Output:**
```json
{
  "language": "en",
  "intent": "OTHER",
  "issue_category": "General",
  "urgency": 1,
  "abuse_flag": false,
  "emergency_flag": false,
  "edge_case": "SILENCE",
  "edge_case_reason": "Filler-only content (um, huh, okay, hi, etc.)",
  "confidence": 0.1,
  "processing_time_ms": 5
}

Action: REPROMPT_USER ("Please tell us what you need help with")
```

### Flow 4: Abuse Detection

**Input:**
```
Transcript: "This is bullshit and stupid"
```

**Output:**
```json
{
  "language": "en",
  "intent": "ABUSE",
  "issue_category": "General",
  "urgency": 1,
  "abuse_flag": true,
  "emergency_flag": false,
  "edge_case": "ABUSE",
  "edge_case_reason": "Abuse keyword detected: bullshit",
  "confidence": 0.95,
  "processing_time_ms": 8
}

Action: WARN_AND_REPROMPT ("Please maintain courtesy. How can we help?")
```

## Supported Languages

| Code | Language | Script | Keywords Example |
|------|----------|--------|------------------|
| hi | Hindi | Devanagari | पानी, सड़क, बिजली |
| en | English | Latin | water, road, electricity |
| hinglish | Hinglish | Mixed | Mera, ghar, pothole |
| ta | Tamil | Tamil | நீர், சாலை |
| te | Telugu | Telugu | నీరు, రోడ్డు |
| bn | Bengali | Bengali | জল, রাস্তা |
| mr | Marathi | Devanagari | पाणी, रस्ता |
| kn | Kannada | Kannada | ನೀರು, ರಸ್ತೆ |
| ml | Malayalam | Malayalam | വെള്ളം, റോഡ് |
| pa | Punjabi | Gurmukhi | ਪਾਣੀ, ਸੜਕ |

## Performance

**Typical latency (with mock):**
- Emergency check: ~1-2ms
- Silence check: ~2-3ms
- Abuse check: ~3-5ms
- Full pipeline (mock): ~15-60ms

**With real Sarvam-1 API:**
- First request: ~200-500ms (API latency + retry backoff)
- Cached: ~50-200ms (depends on network)

**Retry Strategy:**
- 3 total attempts (3 retries)
- Exponential backoff: 0.5s, 1s, 2s
- Timeout: 10 seconds per request

## Development & Testing

### Run All Tests

```bash
cd backend
pip install pytest pytest-asyncio
pytest app/services/tests/test_nlp_classifier.py -v
```

### Run Specific Test Category

```bash
# Edge cases only
pytest app/services/tests/test_nlp_classifier.py::TestEmergencyDetection -v

# Language detection
pytest app/services/tests/test_nlp_classifier.py::TestLanguageDetection -v

# Full pipeline
pytest app/services/tests/test_nlp_classifier.py::TestFullNLPPipeline -v
```

### Manual Testing with Mock

```python
from app.services.nlp_classifier import NLPClassifier, NLPInput
import asyncio

classifier = NLPClassifier(use_mock=True)

test_cases = [
    "Water is leaking",
    "There is a fire!",
    "umm okay hi",
    "This is bullshit",
    "मेरे घर में पानी लीक है",
]

async def test_all():
    for transcript in test_cases:
        result = await classifier.classify(NLPInput(
            session_id=uuid4(),
            transcript=transcript,
        ))
        print(f"'{transcript}' → {result.intent.value} ({result.language.value})")

asyncio.run(test_all())
```

## Troubleshooting

### "SARVAM_API_KEY not set"

**Issue:** Warning during startup
**Solution:** Set env var in `.env`:
```env
SARVAM_API_KEY=sk_your_key_here
```

### "LLM classification failed" → Using fallback

**Issue:** Sarvam API unreachable or timeout
**Default behavior:** Use mock heuristics (still works, lower accuracy)
**Solution:** 
- Check internet connection
- Verify API key is valid
- Increase timeout: `SARVAM_TIMEOUT=15`

### "Abuse keyword detected"

**Issue:** False positive on legitimate words
**Solution:** Review/update lexicon in `nlp_classifier.py`:
```python
ABUSE_LEXICON = frozenset({
    # Add/remove as needed
})
```

### Emergency not detected

**Issue:** Custom emergency keywords missing
**Solution:** Add to pattern in `nlp_classifier.py`:
```python
EMERGENCY_PATTERN = re.compile(
    r"\b(existing_keywords|new_keyword|...)\b",
    re.IGNORECASE,
)
```

## Best Practices

1. **API Key Security**
   - Never hardcode keys
   - Never commit `.env` to git
   - Rotate if accidentally exposed
   - Use service accounts for production

2. **Caching (for high-volume)**
   - Cache identical transcripts for 1 hour
   - Reduces API calls 40-60%
   - Use Redis: `hashkey = md5(transcript)`

3. **Batch Processing**
   - If processing many transcripts, batch 10-50 at a time
   - Reduces overhead vs individual API calls

4. **Monitoring**
   - Log all edge cases for audit trail
   - Track confidence scores over time
   - Alert if abuse/emergency rates spike

5. **Language Hints**
   - Already have language code? Pass it:
     ```python
     NLPInput(transcript=..., detected_language="hi")
     ```
   - Speeds up detection & improves accuracy

## Related Files

- **Implementation**: [backend/app/services/nlp_classifier.py](../services/nlp_classifier.py)
- **Tests**: [backend/app/services/tests/test_nlp_classifier.py](../tests/test_nlp_classifier.py)
- **Integration (SmartRouter)**: [backend/app/services/smart_router.py](../services/smart_router.py)
- **Config**: [backend/app/config.py](../config.py)
- **API Keys**: `.env` (not in repo, local only)

---

**Last Updated:** March 22, 2026
**Status:** Production-Ready
**Supported Languages:** 10 (Hindi, English, Hinglish + regional)
**Edge Cases Handled:** 3 (Emergency, Silence, Abuse)
