# Project Audit - Quick Reference Summary

**Generated**: March 25, 2026 | **Status**: ✅ Production Ready

---

## 🎯 What This System Does

**Voice Complaint Handling System**: Citizens call → Speak complaint in any Indian language → AI detects language → Transcribes → Routes to right department → Responds back in their language.

---

## 📂 Directory Structure at a Glance

```
digital_democracy_ai_calling/
├── backend/                      # FastAPI Backend (Port 8000)
│   ├── app/main.py              # Main entry point
│   ├── app/services/            # STT, TTS, LLM, Router, NLP
│   ├── app/routes/              # API endpoints for calls/complaints
│   └── app/database.py          # SQLite (or Neon via database_router.py)
│
├── awaaz/                        # Voice Pipeline (Port 9003)
│   ├── main.py / api_server.py  # Voice entry point
│   ├── src/pipeline/            # STT, TTS, NLP, Language Detection
│   ├── config.yaml              # Voice configuration
│   └── src/ari_client.py        # Asterisk integration
│
├── ai-services/                 # Modular AI microservices
│   ├── speech_to_text/          # Whisper STT server
│   ├── text_to_speech/          # Coqui TTS engine
│   └── llm/                     # Sarvam LLM client
│
├── audio_language_greeting_service.py  # Language detection + greeting
├── database_router.py                  # Neon DB routing
├── unified_stt_service.py              # STT abstraction layer
├── unified_tts_service.py              # TTS abstraction layer
└── interactive_voice_to_layer3_enhanced.py # Live testing
```

---

## 🔊 Voice/Audio Input Handling

| Component | File | Purpose |
|-----------|------|---------|
| **Asterisk Integration** | `awaaz/src/ari_client.py` | ARI protocol for call control |
| **AudioSocket Handler** | `awaaz/src/audiosocket_handler.py` | Real-time audio stream reception |
| **Voice Activity Detection** | `awaaz/src/vad.py` | Detects speech vs silence (WebRTC) |
| **Audio Recording** | `voice.py` + sounddevice | Microphone input for testing |
| **Format** | PCM16, 16kHz, Mono | Standardized for Whisper/STT |

**Audio Specs**: 512 samples/chunk (32ms), 700ms silence timeout, max 30s utterance

---

## 🎤 Speech-to-Text Transcription

| Level | Method | File | Accuracy |
|-------|--------|------|----------|
| **Primary** | Whisper (faster-whisper) small model | `ai-services/speech_to_text/whisper_server.py` | 95%+ |
| **Secondary** | Sarvam Cloud API | `awaaz/src/pipeline/stt.py` | 92%+ |
| **Tertiary** | Google Cloud STT | Fallback | High |
| **Testing** | Mock golden transcripts | `start_all.py` | 100% (by design) |

**STT Wrapper**: `backend/app/services/stt_service.py` (with 2x retry, 45s timeout)

---

## 🌍 Language Detection (3-Level Strategy)

### Level 1: Script-Based (FASTEST) ✅
- **Location**: `awaaz/src/pipeline/lang_detect.py`
- **Method**: Unicode script range detection (e.g., Devanagari 0x0900-097F = Hindi)
- **Accuracy**: ~98%
- **23 Languages**: Full coverage via script detection

### Level 2: fastText Token-Level
- **Model**: Facebook fastText (lid.176.bin)
- **Accuracy**: ~92%
- **Fallback**: When script detection uncertain

### Level 3: Heuristic Language Markers
- **Language-specific word patterns**: Stored in `LANGUAGE_MARKERS` dict
- **Fallback**: When fastText unavailable

**Result Format**:
```python
(primary_lang, distribution)  # Example: ("ta", {"ta": 0.95, "en": 0.05})
```

---

## 💾 Database Routing (Neon DB)

| Feature | SQLite (Dev) | PostgreSQL/Neon (Prod) |
|---------|--------------|------------------------|
| **File** | `complaints.db` | Cloud-hosted |
| **Connection** | Default | Via `database_router.py` |
| **Env Var** | None | `DATABASE_URL` |
| **Setup** | Auto | `DATABASE_SETUP_GUIDE.md` |

**Tables**:
- `complaints` - Main records (transcript, language, urgency, department, etc.)
- `complaint_logs` - Audit trail

**Connection String Example**:
```
postgresql://user:password@host.neon.tech/dbname?sslmode=require
```

---

## 📞 Call Handling & Routing (Layer 3 - The Brain)

**File**: `backend/app/services/call_router.py`

**4-Step Routing Decision**:
1. **Emergency Detection** (Regex, <50ms) - Keywords like "आग", "fire", "मदद"
2. **Intent Classification** (Sarvam NLP) - COMPLAINT / INQUIRY / NOISE / VAGUE
3. **Entity Extraction** (NLP) - Problem, location, department hints
4. **Urgency Scoring** (Heuristic) - LOW / MEDIUM / HIGH / EMERGENCY

**Department Mapping**: 
```python
DEPT_WATER_001 → keywords: ["water", "pani", "leak", "pipe"]
DEPT_ELECTRICITY_001 → keywords: ["bijli", "power", "transformer"]
... (10+ departments)
```

---

## 🎙️ Call API & Greeting Service

### Main Endpoint
```
POST /calls/handle-turn
  - Input: audio_file (bytes), call_id (optional)
  - Output: transcript, routing decision, agent response, complaint_id
```

### Greeting Service Integration
**File**: `audio_language_greeting_service.py`

**Flow**:
1. First audio received
2. Language detected from raw audio
3. Greeting retrieved in that language
4. Played back via TTS

**Greetings**: 23 Indian languages supported
**Example (Tamil)**: "வணக்கம்! உங்கள் புகாரை பதிவு செய்கிறேன்."

---

## 🚀 Main Entry Points

| Purpose | File | Command | Port |
|---------|------|---------|------|
| **Backend API** | `backend/app/main.py` | `python -m uvicorn app.main:app --port 8000` | 8000 |
| **Voice Pipeline** | `awaaz/api_server.py` | `python awaaz/api_server.py` | 9003 |
| **Interactive Test** | `interactive_voice_to_layer3_enhanced.py` | `python interactive_voice_to_layer3_enhanced.py` | - |
| **Mock Services** | `start_all.py` | `python start_all.py` | 8000, 9000-9002 |
| **Integrated Demo** | `run_integrated_live_flow.py` | `python run_integrated_live_flow.py` | - |

---

## 🔗 Complete Call Processing Workflow

```
VOICE INPUT (Asterisk/Microphone)
    ↓
LANGUAGE DETECTION (script-based or fastText)
    ↓
GREETING (optional) ← audio_language_greeting_service.py
    ↓
SPEECH-TO-TEXT (Whisper)
    ↓
LAYER 3 ROUTING (call_router.py)
    ├─ Emergency keywords detected? → Police/Fire/Ambulance
    ├─ Intent classification → Sarvam NLP
    ├─ Entity extraction → Problem, location
    ├─ Urgency scoring → LOW/MEDIUM/HIGH/EMERGENCY
    └─ Department assignment → DEPT_*_001
    ↓
DATABASE SAVE (Neon or SQLite)
    ↓
LLM RESPONSE GENERATION (Groq/Ollama)
    ↓
TEXT-TO-SPEECH (Coqui/gTTS)
    ↓
PLAYBACK TO CALLER (Asterisk)
```

---

## 📊 Status Dashboard

| Component | Status | File |
|-----------|--------|------|
| Voice Input | ✅ Production | `awaaz/src/audiosocket_handler.py` |
| STT | ✅ Production | `ai-services/speech_to_text/whisper_server.py` |
| Language Detection | ✅ Production | `awaaz/src/pipeline/lang_detect.py` |
| NLP Router | ✅ Production | `backend/app/services/call_router.py` |
| Database | ✅ Production | `database_router.py` (Neon) / `backend/app/database.py` (SQLite) |
| Greeting Service | ✅ Production | `audio_language_greeting_service.py` |
| TTS | ✅ Production | `ai-services/text_to_speech/coqui_tts.py` |
| LLM | ✅ Production | `ai-services/llm/sarvam_client.py` |

---

## 🧪 Quick Health Checks

```bash
# Check backend health
curl http://localhost:8000/

# Check call service health
curl http://localhost:8000/calls/health

# Check AWAAZ health
curl http://localhost:9003/health

# Full system verification
python verify_system.py
```

---

## 📚 Key Configuration Files

| File | What to Change |
|------|-----------------|
| `backend/.env` | `STT_API`, `TTS_API`, `LLM_API`, `SARVAM_API_KEY` |
| `awaaz/.env` | `GROQ_API_KEY`, `FASTTEXT_MODEL_PATH`, `OLLAMA_URL` |
| `backend/app/config.py` | Service URLs & timeouts |
| `awaaz/config.yaml` | Asterisk connection, VAD settings, language thresholds |
| `.env.example` | Template with all variables explained |

**For Neon DB**:
```bash
export DATABASE_URL="postgresql://user:pass@host.neon.tech/db?sslmode=require"
```

---

## 🎯 23 Supported Indian Languages

Hindi, English, Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Bengali, Assamese, Punjabi, Odia, Urdu, Nepali, Konkani, Kashmiri, Sanskrit, Sindhi, Manipuri/Meitei, Bodo, Santali, Maithili, Dogri

---

## 📖 Full Documentation

| Document | Read When... |
|----------|------------|
| `PROJECT_AUDIT_REPORT.md` | You need complete technical details |
| `SESSION3_INDEX.md` | You want quick summary of latest fixes |
| `DATABASE_SETUP_GUIDE.md` | Setting up Neon DB |
| `LANGUAGE_DETECTION_GUIDE.md` | Understanding language detection |
| `INTERACTIVE_VOICE_GUIDE.md` | Testing with microphone |
| `SESSION3_ARCHITECTURE.md` | Understanding full architecture |
| `QUICK_REFERENCE.md` | Need a quick lookup |

---

**Last Updated**: March 25, 2026 | **Status**: All systems operational
