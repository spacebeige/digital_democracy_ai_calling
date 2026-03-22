# Layer 3: The Brain - Call Router Module

## Overview

The Call Router is a production-ready Python module that implements "Layer 3: The Brain" of an automated helpline system. It receives transcribed text from the Speech-to-Text (STT) layer and intelligently routes calls to appropriate departments.

**Key Features:**
- ⚡ **Emergency Pre-filtering** via regex (fast-path for high-priority keywords)
- 🧠 **Sarvam-1 LLM Integration** for Indic language understanding
- 🎯 **Intent Classification** (Complaint, Inquiry, Noise, Vague)
- 🏷️ **Entity Extraction** (Problem, Location, Department)
- 📊 **Urgency Scoring** (Low, Medium, High, Emergency)
- 🔀 **Smart Department Routing** using keyword matching and similarity
- 🛡️ **Comprehensive Validation** with Pydantic
- 🔄 **Retry Logic & Error Handling** for LLM calls

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ STT Output (Transcribed Text)                       │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │ Emergency Pre-filter? │────Yes──→ Route to 911
         │ (Regex Fast Path)     │
         └────────┬──────────────┘
                  │ No
         ┌────────▼──────────┐
         │ Noise Detection?  │────Yes──→ Flag for Re-prompt
         │ (<3 words, filler)│
         └────────┬──────────┘
                  │ No
         ┌────────▼──────────────────────┐
         │ Sarvam-1 LLM Processing       │
         │ • Intent Classification        │
         │ • Entity Extraction           │
         │ • Urgency Scoring             │
         └────────┬───────────────────────┘
                  │
         ┌────────▼──────────────────┐
         │ Smart Routing Logic       │
         │ • Keyword Matching         │
         │ • Entity-based Mapping     │
         │ • Department Selection    │
         └────────┬─────────────────┘
                  │
    ┌─────────────▼──────────────┐
    │ Validated Routing Decision │
    │ (RouterOutput)             │
    └─────────────────────────────┘
```

---

## Installation

### 1. Add Dependencies

Update `backend/requirements.txt`:

```
requests>=2.28.0
pydantic>=2.0.0
python-dotenv>=0.21.0
pytest>=7.0.0  # For testing
```

Install:
```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration

Create or update `.env` file in the backend root:

```env
# Sarvam API Configuration
SARVAM_API_KEY=your_api_key_here
SARVAM_API_ENDPOINT=https://api.sarvam.ai/classify
SARVAM_TIMEOUT=10
SARVAM_MAX_RETRIES=3

# Other services
REDIS_HOST=localhost
STT_API=http://localhost:9000
TTS_API=http://localhost:9001
LLM_API=http://localhost:9002
```

**To get Sarvam API Key:**
- Visit: https://www.sarvam.ai/
- Sign up and create an API key
- Supported languages: Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Punjabi, English

---

## Usage

### Basic Usage (Python)

```python
from app.services.call_router import CallRouter, RouterInput

# Initialize router (uses mock LLM if SARVAM_API_KEY not set)
router = CallRouter(use_mock=False)  # Set False for real Sarvam API

# Process a call
result = router.process_call(RouterInput(
    session_id="call_12345",
    transcription_text="Mere ghar ke samne sadak mein pothole hai",
    language_code="hi",
))

# Access results
print(f"Department: {result.department_name}")
print(f"Urgency: {result.urgency}")
print(f"Confidence: {result.confidence_score:.2%}")
print(f"Summary: {result.summary}")
```

### FastAPI Endpoint

The router is exposed via FastAPI endpoints at `/v1/router`:

#### Route a Call

```bash
curl -X POST http://localhost:8000/v1/router/route-call \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "call_001",
    "transcription_text": "Water is leaking from the tap in my kitchen",
    "language_code": "en"
  }'
```

**Response:**
```json
{
  "session_id": "call_001",
  "is_emergency": false,
  "intent": "COMPLAINT",
  "urgency": "HIGH",
  "dept_id": "DEPT_WATER_001",
  "department_name": "Water & Sewerage",
  "summary": "Complaint reported: Water.",
  "entities": {
    "problem": "water",
    "location": "kitchen",
    "department": "Water & Sewerage"
  },
  "confidence_score": 0.85,
  "raw_transcript": "Water is leaking from the tap in my kitchen",
  "processing_time_ms": 342.5
}
```

#### Batch Route Calls

```bash
curl -X POST http://localhost:8000/v1/router/route-call/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"session_id": "call_001", "transcription_text": "...", "language_code": "en"},
    {"session_id": "call_002", "transcription_text": "...", "language_code": "hi"}
  ]'
```

#### Health Check

```bash
curl http://localhost:8000/v1/router/health
```

---

## Core Components

### 1. Pydantic Schemas

#### `RouterInput`
Input specification for call routing:
```python
RouterInput(
    session_id="unique_call_id",
    transcription_text="User's spoken text (transcribed)",
    language_code="hi|en|ta|te|ka|ml|bn|mr|pa"
)
```

#### `RouterOutput`
Structured output with routing decision:
```python
RouterOutput(
    session_id="unique_call_id",
    is_emergency=False,
    intent=IntentType.COMPLAINT,
    urgency=UrgencyLevel.HIGH,
    dept_id="DEPT_WATER_001",
    department_name="Water & Sewerage",
    summary="Issue description",
    entities=EntityExtraction(...),
    confidence_score=0.85,
    raw_transcript="...",
    processing_time_ms=342.5
)
```

### 2. Emergency Detection

**Regex-based fast path:**
```python
EMERGENCY_KEYWORDS = [
    "fire", "emergency", "ambulance", "police", "injury", "accident",
    "danger", "critical", "urgent", "violence", "attack", "gas leak",
    "electrical fire", "snake", "electrocution"
]
```

Emergency calls bypass LLM and route to `DEPT_EMERGENCY_911`.

### 3. Intent Classification

```
COMPLAINT  - User is reporting an issue/grievance
INQUIRY    - User is asking a question
NOISE      - Detected only fillers (uh, um, hello)
VAGUE      - Call has <3 words or insufficient signal
```

### 4. Department Mapping

Supported departments:

| Department ID | Name | Keywords |
|---|---|---|
| DEPT_WATER_001 | Water & Sewerage | water, tap, pipe, leak, sewer, drain |
| DEPT_ROADS_001 | Roads & Infrastructure | road, pothole, street, pavement, traffic |
| DEPT_SANITATION_001 | Sanitation & Waste | garbage, waste, trash, dust, clean |
| DEPT_ELECTRICITY_001 | Electricity & Power | electric, power, light, bulb, meter, circuit |
| DEPT_HEALTH_001 | Health & Medical | health, hospital, doctor, clinic, vaccine |
| DEPT_EDUCATION_001 | Education | school, college, student, fees, admission |
| DEPT_GENERAL_001 | General Grievances | fallback/unknown |

### 5. Sarvam-1 LLM Integration

#### RealSarvamAPIClient
```python
from app.services.call_router import RealSarvamAPIClient

client = RealSarvamAPIClient(
    api_key="your_key",
    api_endpoint="https://api.sarvam.ai/classify",
    timeout=10,
    max_retries=3
)

result = client.classify_intent(
    text="Mera ghar mein water leak ho gaya",
    language_code="hi"
)
# Returns: {intent, entities, urgency, confidence}
```

**Features:**
- Exponential backoff retry logic
- Configurable timeout
- Language detection
- Error handling & logging

#### MockSarvamAPIClient
For development/testing without API key:
```python
from app.services.call_router import MockSarvamAPIClient

client = MockSarvamAPIClient()
# Uses heuristic-based classification instead of LLM
```

---

## Error Handling

### Input Validation

```python
from pydantic import ValidationError
from app.services.call_router import RouterInput

try:
    invalid_input = RouterInput(
        session_id="call_001",
        transcription_text="",  # Empty!
        language_code="en"
    )
except ValidationError as e:
    print(f"Invalid input: {e}")
```

### LLM Processing Errors

```python
from app.services.call_router import CallRouter, RouterInput

try:
    result = router.process_call(router_input)
except RuntimeError as e:
    print(f"LLM failed after retries: {e}")
    # Fallback to rule-based routing
except Exception as e:
    print(f"Unexpected error: {e}")
```

### API Error Handling (FastAPI)

```python
# HTTPException automatically raised for:
# 400 - Validation errors
# 503 - LLM service unavailable
# 500 - Internal server errors
```

---

## Testing

### Run Unit Tests

```bash
cd backend
pytest app/services/tests/test_call_router.py -v
```

### Run Examples

```bash
python -m app.services.tests.test_call_router
```

### Test Coverage

- ✅ Emergency detection
- ✅ Noise/vague filtering
- ✅ Department routing
- ✅ Entity extraction
- ✅ Multilingual support (en, hi)
- ✅ Confidence scoring
- ✅ Error handling
- ✅ Performance metrics
- ✅ Edge cases

---

## Performance Characteristics

| Operation | Latency |
|---|---|
| Emergency pre-filter | ~1ms |
| Noise detection | ~2ms |
| Mock LLM processing | ~10-50ms |
| Real Sarvam API call | ~200-500ms (with retries) |
| **Total (with Mock)** | ~15-60ms |
| **Total (with Real API)** | ~220-600ms |

### Optimization Tips

1. **Cache frequently matched departments** for known keywords
2. **Batch process calls** for analytics using `/v1/router/route-call/batch`
3. **Use mock client** in development to reduce test latency
4. **Implement Redis caching** for recent routing patterns
5. **Set appropriate timeout** for Sarvam API based on your SLA

---

## Configuration Reference

### Environment Variables

```env
# Required for real LLM
SARVAM_API_KEY=your_api_key

# Optional
SARVAM_API_ENDPOINT=https://api.sarvam.ai/classify
SARVAM_TIMEOUT=10  # seconds
SARVAM_MAX_RETRIES=3
```

### Router Initialization

```python
# With real API
router = CallRouter(
    llm_client=RealSarvamAPIClient(
        api_key="your_key",
        timeout=10,
        max_retries=3
    )
)

# With mock (development)
router = CallRouter(use_mock=True)

# Auto-detect based on API key
router = CallRouter(use_mock=False)  # Raises error if no API key
```

---

## Production Deployment Checklist

- [ ] Set `SARVAM_API_KEY` in production environment
- [ ] Configure proper logging levels
- [ ] Set up monitoring for `/v1/router/health` endpoint
- [ ] Test multilingual support for your region
- [ ] Add custom keywords to `DEPARTMENT_REGISTRY` if needed
- [ ] Set up error alerts for LLM failures
- [ ] Load test with expected call volume
- [ ] Document department-specific abbreviations for your region
- [ ] Set up database to store routing decisions for analytics
- [ ] Implement metrics collection (confidence_score, processing_time_ms)

---

## Troubleshooting

### "LLM service unavailable" Error

**Cause:** Sarvam API is down or timeout exceeded

**Solution:**
1. Check network connectivity
2. Verify `SARVAM_API_KEY` is correct
3. Increase `SARVAM_TIMEOUT` in `.env`
4. Check Sarvam API status page

### Low Confidence Scores

**Cause:** Vague or short transcriptions

**Solution:**
1. Ensure STT quality is good
2. Add more context to transcription
3. Add custom keywords for your departments

### Wrong Department Routing

**Cause:** Keywords don't match your region's terminology

**Solution:**
1. Add regional keywords to `DEPARTMENT_REGISTRY`
2. Adjust LLM prompt (if using custom Sarvam model)
3. Use real Sarvam API instead of mock

### Performance Issues

**Cause:** High LLM latency

**Solution:**
1. Use mock client for non-critical paths
2. Implement caching
3. Batch process calls
4. Use read replicas for database

---

## Advanced: Customization

### Add Custom Department

```python
from app.services.call_router import DEPARTMENT_REGISTRY

DEPARTMENT_REGISTRY["DEPT_CUSTOM_001"] = {
    "name": "My Custom Department",
    "keywords": ["keyword1", "keyword2", "राज्य"],  # Supports Unicode
    "aliases": ["CUSTOM", "MYCUSTOM"],
}
```

### Add Custom Emergency Keywords

```python
import re
from app.services.call_router import EMERGENCY_KEYWORDS_PATTERN

# Extend the pattern
EMERGENCY_KEYWORDS_PATTERN = re.compile(
    r'\b(fire|emergency|ambulance|police|'
    r'your_custom_keyword|आपातकाल)\b',
    re.IGNORECASE
)
```

### Custom Sarvam Prompt

```python
class CustomSarvamAPIClient(RealSarvamAPIClient):
    def classify_intent(self, text: str, language_code: str):
        # Add custom prompt engineering here
        payload = {
            "text": text,
            "language": language_code,
            "task": "intent_classification_with_ner",
            "system_prompt": "You are a grievance classification expert..."
        }
        # ... rest of implementation
```

---

## License & Support

This module is part of the Digital Democracy AI project.

For issues or questions:
1. Check the troubleshooting section above
2. Review test cases in `test_call_router.py`
3. Check logs in `app/services/call_router.py`
4. Contact the backend team

---

## References

- [Sarvam AI Documentation](https://www.sarvam.ai/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [requests Library](https://requests.readthedocs.io/)
