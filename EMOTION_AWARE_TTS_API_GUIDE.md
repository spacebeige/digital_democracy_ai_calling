# 🎙️ Emotion-Aware TTS FastAPI Endpoints Guide

**Status**: ✅ Complete & Integrated in `awaaz/api_server.py`

---

## 🚀 Quick Start

### Run the FastAPI Server
```bash
cd /Users/ashwinagarkhed/integration1/awaaz
python3 -m uvicorn api_server:app --reload --port 8000
```

Then visit: **http://localhost:8000/docs** (interactive API documentation)

---

## 📡 Three Main Endpoints

### 1️⃣ **Emotion-Aware TTS Synthesis**
**Endpoint**: `POST /api/v1/tts/emotion-aware`

Convert text to expressive speech with automatic emotion-based adjustments.

#### Parameters:
| Param | Type | Required | Example | Description |
|-------|------|----------|---------|-------------|
| `text` | string | ✅ | `मुझे शिकायत है` | Text in native language to synthesize |
| `language` | string | ✅ | `hi` | BCP-47 language code |
| `intent` | string | ❌ | `COMPLAINT` | `COMPLAINT` (fast, expressive) or `INQUIRY` (slow, measured) |
| `anger_score` | float | ❌ | `0.85` | Emotion intensity (0.0–1.0). Triggers expressive tone when > 0.6 |
| `speaker` | string | ❌ | `ritu` | Voice name (defaults to Ritu—female) |

#### Examples:

**Angry Complaint (Hindi)**
```bash
curl "http://localhost:8000/api/v1/tts/emotion-aware?text=मुझे बहुत शिकायत है&language=hi&intent=COMPLAINT&anger_score=0.85"
```
→ **Result**: Fast-paced (1.15x), expressive voice with "ritu"

**Calm Inquiry (Tamil)**
```bash
curl "http://localhost:8000/api/v1/tts/emotion-aware?text=நீங்கள் உதவ முடியுமா&language=ta&intent=INQUIRY&anger_score=0.2"
```
→ **Result**: Slow-paced (0.95x), measured, calm voice

**English Complaint**
```bash
curl "http://localhost:8000/api/v1/tts/emotion-aware?text=I need to speak to a manager immediately&language=en&intent=COMPLAINT&anger_score=0.7"
```
→ **Result**: Fast English speech with elevated emotional tone

#### Response:
```json
{
  "job_id": "5f0a1c2b-3d4e-5f6g-7h8i-9j0k1l2m3n4o",
  "status": "processing",
  "input_text": "मुझे बहुत शिकायत है",
  "language": "hi",
  "speaker": "ritu",
  "intent": "COMPLAINT",
  "anger_score": 0.85,
  "created_at": "2026-03-26T12:34:56.123456",
  "status_url": "/api/v1/tts/status/5f0a1c2b-3d4e-5f6g-7h8i-9j0k1l2m3n4o",
  "download_url": "/api/v1/tts/download/5f0a1c2b-3d4e-5f6g-7h8i-9j0k1l2m3n4o"
}
```

#### Supported Languages (24+):
| Code | Language | Pace | Emotion |
|------|----------|------|---------|
| `hi` | Hindi | 0.95 | natural |
| `ta` | Tamil | 0.80 | warm |
| `te` | Telugu | 0.85 | natural |
| `kn` | Kannada | 0.78 | calm |
| `ml` | Malayalam | 0.92 | warm |
| `mr` | Marathi | 0.90 | expressive |
| `pa` | Punjabi | 1.0 | energetic |
| `gu` | Gujarati | 1.0 | expressive |
| `bn` | Bengali | 0.92 | natural |
| `en` | English | 1.0 | professional |
| + 14 more regional languages... | | | |

---

### 2️⃣ **End-to-End Voice Analysis + Emotion-Aware Response**
**Endpoint**: `POST /api/v1/voice/end-to-end-analysis`

Complete pipeline: voice upload → NLP analysis → emotion-aware TTS response synthesis.

#### Parameters:
| Param | Type | Required | Example | Description |
|-------|------|----------|---------|-------------|
| `file` | file | ✅ | user_voice.wav | Audio file (WAV, MP3) |
| `response_text` | string | ✅ | `आपकी समस्या का समाधान` | Response to synthesize |
| `response_language` | string | ❌ | `hi` | Language for response (defaults to detected input language) |

#### Workflow:
1. **Upload** voice file
2. **Transcribe** using STT (speech-to-text)
3. **Analyze** with NLP to extract:
   - Detected intent (COMPLAINT, INQUIRY, etc.)
   - Anger score (0.0–1.0)
   - AI insight
4. **Synthesize** response with emotion-matched settings:
   - If user was angry → fast, expressive response
   - If user was calm → slow, measured response

#### Example:
```bash
curl -X POST "http://localhost:8000/api/v1/voice/end-to-end-analysis" \
  -F "file=@user_complaint.wav" \
  -F "response_text=आपकी समस्या दर्ज की जा रही है"
```

#### Response:
```json
{
  "pipeline_job_id": "e2e-abc-123",
  "user_voice": {
    "transcript": "मुझे बहुत गुस्सा आ रहा है",
    "language": "hi"
  },
  "nlp_analysis": {
    "detected_intent": "COMPLAINT",
    "anger_score": 0.82,
    "ai_insight": "User expresses frustration and urgency..."
  },
  "response_synthesis": {
    "tts_job_id": "tts-xyz-789",
    "response_text": "आपकी समस्या दर्ज की जा रही है",
    "response_language": "hi",
    "emotion_settings": {
      "intent": "COMPLAINT",
      "anger_score": 0.82,
      "voice": "ritu (female)",
      "expected_pace": "1.15x (fast, expressive)"
    },
    "download_url": "/api/v1/tts/download/tts-xyz-789",
    "status_url": "/api/v1/tts/status/tts-xyz-789"
  }
}
```

---

### 3️⃣ **System Information & Capabilities**
**Endpoint**: `GET /api/v1/system/emotion-aware-tts-info`

Returns full system configuration, supported languages, emotion mappings, and examples.

#### Example:
```bash
curl "http://localhost:8000/api/v1/system/emotion-aware-tts-info"
```

#### Response includes:
- ✅ All supported languages (24+)
- ✅ Emotion-to-voice adjustment mappings
- ✅ Language-specific pacing values
- ✅ Fallback provider chain (Sarvam → ElevenLabs → Groq → gTTS)
- ✅ Example requests for each scenario

---

## 🎯 Emotion-Based Adjustments

### COMPLAINT + High Anger (anger_score > 0.6)
```
Sarvam:         pace=1.15x  emotion=expressive
ElevenLabs:     stability=0.30  style=0.75
Groq:           speed=1.15x
Google Cloud:   speaking_rate=1.15
```
**Effect**: Faster, more expressive voice to match user's frustration

### INQUIRY + Low Anger (anger_score < 0.3)
```
Sarvam:         pace=0.95x  emotion=calm
ElevenLabs:     stability=0.60  style=0.20
Groq:           speed=0.95x
Google Cloud:   speaking_rate=0.95
```
**Effect**: Slower, measured voice for professional tone

### Neutral (No emotion flags)
```
Sarvam:         pace=1.0x   emotion=natural
ElevenLabs:     stability=0.45  style=0.35
Groq:           speed=1.0x
Google Cloud:   speaking_rate=1.0
```
**Effect**: Standard natural speech

---

## 📊 Supported Languages & Native Pacing

| Language | Code | Pace | Script | Best Use |
|----------|------|------|--------|----------|
| Hindi | `hi` | 0.95 | Devanagari | North India |
| Marathi | `mr` | 0.90 | Devanagari | Express emotion well |
| Tamil | `ta` | 0.80 | Tamil | Melodic, slower for clarity |
| Telugu | `te` | 0.85 | Telugu | Natural flow |
| Kannada | `kn` | 0.78 | Kannada | Careful pronunciation |
| Malayalam | `ml` | 0.92 | Malayalam | Melodic language |
| Bengali | `bn` | 0.92 | Bengali | Natural tone |
| Gujarati | `gu` | 1.0 | Gujarati | Expressive & lively |
| Punjabi | `pa` | 1.0 | Gurmukhi | Energetic tone |
| English | `en` | 1.0 | Latin | Professional |
| + 14 more regional variants... | | | | |

---

## 🔄 Provider Fallback Chain

If **Sarvam fails**, automatically fallback to:
1. **Sarvam** (optimal for Indic scripts)
2. **ElevenLabs** (Lily—female voice, premium)
3. **Groq** (Celeste—fast, free tier)
4. **gTTS** (offline fallback, no API key)
5. **Google Cloud TTS** (last resort)

---

## 🧪 Testing with cURL

### Test 1: Simple Hindi Complaint
```bash
curl -X POST "http://localhost:8000/api/v1/tts/emotion-aware?text=मुझे शिकायत है&language=hi&intent=COMPLAINT&anger_score=0.75"
```

### Test 2: Tamil Inquiry
```bash
curl -X POST "http://localhost:8000/api/v1/tts/emotion-aware?text=என்னைக் கூறுங்கள்&language=ta&intent=INQUIRY&anger_score=0.2"
```

### Test 3: English Professional
```bash
curl -X POST "http://localhost:8000/api/v1/tts/emotion-aware?text=Good morning, I need assistance&language=en&anger_score=0.3"
```

### Test 4: Check Status
```bash
curl "http://localhost:8000/api/v1/tts/status/{job_id}"
```

### Test 5: Download Audio
```bash
curl "http://localhost:8000/api/v1/tts/download/{job_id}" -o response.wav
```

### Test 6: System Info
```bash
curl "http://localhost:8000/api/v1/system/emotion-aware-tts-info" | jq .
```

---

## 📝 Integration Examples

### Python Client
```python
import requests

BASE_URL = "http://localhost:8000"

# Emotion-aware TTS
response = requests.post(
    f"{BASE_URL}/api/v1/tts/emotion-aware",
    params={
        "text": "मुझे विरोध करना है",
        "language": "hi",
        "intent": "COMPLAINT",
        "anger_score": 0.85
    }
)

job = response.json()
job_id = job["job_id"]

# Poll for completion
import time
while True:
    status = requests.get(f"{BASE_URL}/api/v1/tts/status/{job_id}").json()
    if status["status"] == "completed":
        audio_url = f"{BASE_URL}/api/v1/tts/download/{job_id}"
        print(f"Audio ready: {audio_url}")
        break
    time.sleep(1)
```

### JavaScript/Node.js Client
```javascript
const BASE_URL = "http://localhost:8000";

async function synthesizeEmotionalSpeech(text, language, intent, angerScore) {
  const response = await fetch(
    `${BASE_URL}/api/v1/tts/emotion-aware?text=${encodeURIComponent(text)}&language=${language}&intent=${intent}&anger_score=${angerScore}`,
    { method: "POST" }
  );
  
  const job = await response.json();
  const jobId = job.job_id;
  
  // Poll for completion
  let completed = false;
  while (!completed) {
    const status = await fetch(`${BASE_URL}/api/v1/tts/status/${jobId}`).then(r => r.json());
    if (status.status === "completed") {
      console.log(`Audio: ${BASE_URL}/api/v1/tts/download/${jobId}`);
      completed = true;
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

synthesizeEmotionalSpeech("मुझे मदद चाहिए", "hi", "COMPLAINT", 0.8);
```

---

## 🔐 Security Notes

- **File upload limit**: 50MB per file
- **Rate limiting**: Implement in production
- **API Keys**: Store `SARVAM_API_KEY`, `ELEVENLABS_API_KEY`, etc. in `.env`
- **CORS**: Configure as needed for cross-origin requests

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Language not supported" | Use BCP-47 codes (e.g., `hi`, `ta`, `te`) |
| "SARVAM_API_KEY missing" | Add to `.env` file in `awaaz/` directory |
| Audio not ready | Wait longer or check job status endpoint |
| Anger score not affecting pace | Ensure `anger_score > 0.6` for complaint mode |
| Wrong language detected | Specify `response_language` explicitly |

---

## 📖 References

- **Sarvam TTS Documentation**: https://sarvam.ai/docs
- **FastAPI Docs**: http://localhost:8000/docs (when server running)
- **AWAAZ System Guide**: See `SYSTEM_COMPLETE_DOCUMENTATION_v2.1.md`

---

**Version**: 1.0.0 (Emotion-Aware TTS)  
**Last Updated**: 26-Mar-2026  
**Author**: AWAAZ AI Team
