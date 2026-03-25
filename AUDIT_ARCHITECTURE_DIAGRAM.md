# Project Audit - Visual Architecture Map

**Complete System Topology & Data Flow**

---

## 🏗️ System Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CITIZEN CALLER                                   │
│                      (Phone, Language = Any)                             │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │
                        Audio Stream: PCM16 16kHz
                                       │
┌──────────────────────────────────────v──────────────────────────────────┐
│                    LAYER 0: CALL RECEPTION                              │
│  Asterisk PBX (config: awaaz/asterisk_dialplan.conf)                    │
│  ├─ ARI API (Port 8088, awaaz/src/ari_client.py)                       │
│  ├─ AudioSocket (Port 8090, awaaz/src/audiosocket_handler.py)          │
│  └─ STAsis App: "awaaz" → Routes to AWAAZ pipeline                     │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │
┌──────────────────────────────────────v──────────────────────────────────┐
│               LAYER 1-2: VOICE PROCESSING PIPELINE (AWAAZ)              │
│                         awaaz/main.py or api_server.py                  │
│                                                                          │
│  ┌─ VAD (Voice Activity Detection)                                      │
│  │  └─ awaaz/src/vad.py (WebRTC, 700ms silence timeout)                │
│  │                                                                       │
│  ├─ Audio Chunking (512 samples, ~32ms)                                │
│  │  └─ awaaz/src/audiosocket_handler.py                                │
│  │                                                                       │
│  ├─ **EARLY LANGUAGE DETECTION** ← (From audio, before transcription)  │
│  │  └─ awaaz/src/pipeline/lang_detect.py                              │
│  │     ├─ Script-based: Unicode ranges (0x0900-097F = Hindi, etc)     │
│  │     ├─ fastText: Token-level (if available)                        │
│  │     └─ Result: language_code (ta, hi, en, etc)                     │
│  │                                                                       │
│  ├─ **GREETING GENERATION** (Turn #1 only)                             │
│  │  └─ greeting_integration.py + audio_language_greeting_service.py   │
│  │     ├─ Detect caller's language                                    │
│  │     ├─ Select greeting in that language                            │
│  │     └─ Generate TTS → Play back                                    │
│  │        "வணக்கம்! உங்கள் புகாரை பதிவு செய்கிறேன்."                │
│  │                                                                       │
│  └─ Process → Store in session_store (awaaz/src/session_store.py)     │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │
                    Complete utterance audio (30s max)
                                       │
┌──────────────────────────────────────v──────────────────────────────────┐
│             LAYER 2: SPEECH-TO-TEXT (STT) TRANSCRIPTION                |
│                                                                          │
│  Primary: awaaz/src/pipeline/stt.py (Whisper small model)              │
│  ├─ Model: faster-whisper (small)                                      │
│  ├─ Language detection: Whisper's acoustic features                    │
│  ├─ Output: {text, language_code, confidence, phonetic_text}          │
│  └─ All 23 Indian languages + English supported                        │
│                                                                          │
│  Fallback: Sarvam Cloud API (if primary fails)                         │
│  └─ awaaz/src/pipeline/stt.py → SarvamLanguageTools                   │
│                                                                          │
│  Backend wrapper: backend/app/services/stt_service.py                  │
│  └─ HTTP POST to STT_API (configured in backend/.env)                 │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │
                  Text output + detected language_code
                      Example: "नमस्ते, मेरे घर के सामने..."
                              Language: "hi" (Hindi)
                                       │
┌──────────────────────────────────────v──────────────────────────────────┐
│                UNIFIED NLP PROCESSING (Optional Pre-Layer3)             │
│                                                                          │
│  Language Detection (Text-based): unified_stt_service.py               │
│  ├─ detect_language(text) → language_code                             │
│  ├─ Supports 22 official Indian languages + English                   │
│  └─ Script detection as primary method                                │
│                                                                          │
│  Optional: Post-call analysis via post_call_analyzer.py                │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │
┌──────────────────────────────────────v──────────────────────────────────┐
│           LAYER 3: INTELLIGENT CALL ROUTING (THE BRAIN)                │
│              backend/app/services/call_router.py                       │
│                                                                          │
│  Input:  RouterInput {session_id, transcription_text, language_code}  │
│                                                                          │
│  ┌─ STEP 1: Emergency Keyword Detection (Fast path)                   │
│  │  └─ Regex patterns: EMERGENCY_KEYWORDS dict                        │
│  │     Hindi: ["आग", "आग लगी", "मदद", "खून", "घायल", ...]         │
│  │     English: ["fire", "emergency", "help", "911", ...]             │
│  │     Result: is_emergency = True/False                              │
│  │                                                                       │
│  ├─ STEP 2: Intent Classification (via Sarvam NLP API)                │
│  │  └─ Call Sarvam-1 model (awaaz/src/pipeline/nlp.py)               │
│  │     Intent: COMPLAINT | INQUIRY | NOISE | VAGUE                   │
│  │                                                                       │
│  ├─ STEP 3: Entity Extraction (via NLP)                               │
│  │  └─ Extract: problem (what?), location (where?), implied_dept      │
│  │     Example: problem="पानी की समस्या", location="अपार्टमेंट 3A"   │
│  │                                                                       │
│  ├─ STEP 4: Urgency Scoring (Heuristic + Keyword matching)            │
│  │  └─ Calculate urgency: LOW|MEDIUM|HIGH|EMERGENCY (0-100)          │
│  │     Logic: URGENT_KEYWORDS dict + sentiment analysis               │
│  │                                                                       │
│  └─ STEP 5: Department Assignment (Deterministic routing)             │
│     └─ DEPARTMENT_REGISTRY: keywords → dept_id → dept_name            │
│        Example: keywords=["water","pani"] → DEPT_WATER_001           │
│                                                                          │
│  Output: RouterOutput {is_emergency, intent, urgency, dept_id, dept_name,
│                        entities, summary, confidence_score}             │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │
                  Routing decision: {dept_id, urgency, intent}
                                       │
                    ┌───────────────┬──────────────┬────────────┐
                    │               │              │            │
                    v               v              v            v
            Emergency Case   Normal Case   Database      Session
            (Call Police,    (Typical      Save           Update
             Fire, etc)      Complaint)    (DB Router)    (Store)
                    │               │              │            │
                    └───────────────┼──────────────┼────────────┘
                                    │
┌───────────────────────────────────v──────────────────────────────────┐
│       LAYER 2b: DATABASE PERSISTENCE & ROUTING HISTORY              │
│                                                                       │
│  Option 1: SQLite (Development, default)                            │
│  └─ backend/app/database.py → complaints.db                        │
│     Tables: complaints, complaint_logs                             │
│                                                                       │
│  Option 2: PostgreSQL/Neon (Production)                             │
│  └─ database_router.py + psycopg2                                   │
│     Connection: DATABASE_URL env var                                │
│     Example: postgresql://user:pass@host.neon.tech/db              │
│                                                                       │
│  Saved Data:                                                         │
│  ├─ session_id, transcript, language_code, urgency_level           │
│  ├─ keywords (array), department_assigned, department_notes        │
│  ├─ created_at, updated_at, complaint_logs (audit trail)           │
│  └─ Enables: 1) Audit trail  2) Analytics  3) Escalation           │
└───────────────────────────────────v──────────────────────────────────┘
                                    │
┌───────────────────────────────────v──────────────────────────────────┐
│        LAYER 2c: LLM RESPONSE GENERATION (Smart Reply)              │
│              backend/app/services/llm_service.py                    │
│                                                                       │
│  Input: {transcript, language_code, urgency, dept, entities}        │
│                                                                       │
│  LLM Provider (Priority):                                            │
│  1. Groq API (llama-3.1-8b-instant) - Fast, free tier available     │
│  2. Ollama local (llama3.2:3b) - Offline fallback                   │
│  3. Mock LLM (start_all.py) - Testing                               │
│                                                                       │
│  Prompt Engineering:                                                 │
│  ├─ Language: Response in caller's language                         │
│  ├─ Tone: Formal, reassuring                                        │
│  ├─ Content: Confirm receipt, what happens next, reference number   │
│  └─ Example Output (Hindi):                                         │
│     "आपकी शिकायत दर्ज की गई है। संदर्भ: #12345                     │
│      जल विभाग आपसे 24 घंटे में संपर्क करेगा।"                    │
│                                                                       │
│  Output: response_text (plain text, ready for TTS)                  │
└───────────────────────────────────v──────────────────────────────────┘
                                    │
┌───────────────────────────────────v──────────────────────────────────┐
│        LAYER 2d: TEXT-TO-SPEECH (TTS) RESPONSE GENERATION            │
│          backend/app/services/tts_service.py                        │
│          awaaz/src/pipeline/tts.py                                  │
│                                                                       │
│  Input: response_text + language_code                               │
│                                                                       │
│  TTS Engine (Priority):                                              │
│  1. Coqui TTS (Local) - Hindi, Marathi, English                     │
│     └─ awaaz/src/pipeline/tts.py                                   │
│  2. Google Cloud TTS (Cloud) - Enterprise-grade                     │
│  3. gTTS fallback - 23 Indian languages via Google                  │
│  4. Mock TTS (start_all.py) - Testing                               │
│                                                                       │
│  Output:                                                              │
│  ├─ WAV/MP3 audio file (mono, 16kHz)                               │
│  ├─ Embedded with language-specific phonetic tuning                 │
│  └─ Base64-encoded for HTTP response                               │
└───────────────────────────────────v──────────────────────────────────┘
                                    │
                   Audio stream (WAV/MP3, MP3 16kHz)
                                    │
┌───────────────────────────────────v──────────────────────────────────┐
│        LAYER 1b: PLAYBACK MANAGER (Agent Response)                  │
│              awaaz/src/playback_manager.py                          │
│                                                                       │
│  ├─ Convert audio to Asterisk format (μ-law)                       │
│  ├─ Stream via ARI API back to Asterisk                            │
│  └─ Asterisk plays to caller's phone                               │
└───────────────────────────────────v──────────────────────────────────┘
                                    │
                    Agent response plays to CITIZEN
                   "शिकायत दर्ज की गई। जल विभाग..."
                                    │
                    Citizen may continue (next turn)
                            OR
                        Call ends
```

---

## 📡 API Integration Points

```
┌─────────────────────────────────────────────────────────┐
│            FastAPI Backend (Port 8000)                  │
│          backend/app/main.py + routes/                 │
└──────────┬──────────────────────────────────────────────┘
           │
    ┌──────┴──────┬──────────────┬────────────────┐
    v             v              v                v
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│ /calls/ │  │/complaints/│ ├─ /router/ │ │ /analysis/  │
│(main)   │  │(mgmt)    │ └─/analysis/ │ │ (post-call) │
│         │  │          │              │ │             │
│Endpoints:   │Endpoints:│  Endpoints:   │ Endpoints:   │
│ POST    │  │POST /   │  │POST /route│ │ POST /    │
│handle-turn  │GET /{id}│  │GET /logs  │ │ analyze   │
│ GET /health │         │  │           │ │           │
└────┬────┘  └────┬─────┘  └────┬──────┘ └──────┬─────┘
     │            │              │               │
     └────────────┴──────────────┴───────────────┘
                      │
        Backend services layer
        ├─ stt_service.py (→ STT_API:9000)
        ├─ tts_service.py (→ TTS_API:9001)
        ├─ llm_service.py (→ LLM_API:9002)
        ├─ call_router.py (Layer 3 routing)
        └─ nlp_classifier.py (Intent classification)
                      │
        ┌─────────────┼─────────────┐
        v             v             v
    ┌─────────┐ ┌──────────┐ ┌────────────┐
    │ STT API │ │ TTS API  │ │ LLM API    │
    │:9000    │ │  :9001   │ │  :9002     │
    │         │ │          │ │            │
    │Whisper  │ │ Coqui    │ │ Groq/      │
    │         │ │ gTTS     │ │ Ollama     │
    │         │ │ Google   │ │            │
    └─────────┘ └──────────┘ └────────────┘
```

---

## 🗄️ Database Schema Diagram

```
┌──────────────────────────────────────────────────────────┐
│              COMPLAINTS TABLE (Main)                      │
├──────────────────────────────────────────────────────────┤
│ Primary Key: id (INT)                                    │
├──────────────────────────────────────────────────────────┤
│ ├─ session_id (VARCHAR) - Unique call ID                │
│ ├─ transcript (TEXT) - Full caller speech (STT output)  │
│ ├─ language_code (VARCHAR) - Detected language (hi/ta)  │
│ ├─ language_name (VARCHAR) - Full name (Hindi/Tamil)    │
│ ├─ urgency_level (VARCHAR) - LOW/MEDIUM/HIGH/EMERGENCY  │
│ ├─ urgency_score (INT) - 0-100 numeric score            │
│ ├─ keywords (TEXT[]) - Extracted keywords array         │
│ ├─ department_assigned (VARCHAR) - DEPT_*_001           │
│ ├─ department_notes (TEXT) - Router notes               │
│ ├─ created_at (TIMESTAMP) - When created                │
│ └─ updated_at (TIMESTAMP) - Last modified               │
└──────────────────────────────────────────────────────────┘
             │
             │ Foreign Key
             v
┌──────────────────────────────────────────────────────────┐
│           COMPLAINT_LOGS TABLE (Audit Trail)             │
├──────────────────────────────────────────────────────────┤
│ ├─ id (INT) Primary Key                                  │
│ ├─ complaint_id (INT) Foreign Key                        │
│ ├─ action (VARCHAR) - What happened (routed, escalated) │
│ ├─ details (TEXT) - Additional context                  │
│ └─ timestamp (TIMESTAMP) - When happened                │
└──────────────────────────────────────────────────────────┘
```

---

## 🔄 Session Management

```
┌─────────────────────────────────────────────────────────┐
│           SESSION STORE (awaaz/src/session_store.py)    │
├─────────────────────────────────────────────────────────┤
│ session_id: str (unique call identifier, 13-char)      │
│ turn_number: int (1, 2, 3, ... up to MAX_TURNS=10)    │
│ state: str (GREETING, LISTENING, PROCESSING, etc)     │
│ language: str (detected: hi, ta, en, etc)             │
│ transcript_so_far: str (accumulated)                   │
│ routing_decision: RouterOutput (from Layer 3)         │
│ caller_audio_buffer: bytes (for replay/analysis)      │
│ complaint_id: int (if already persisted to DB)        │
│ context: Dict (call context for LLM)                  │
│ created_at: datetime (call start time)                │
│ last_activity: datetime (last update)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 File Dependency Map

```
USER ENTRY POINTS
├─ backend/app/main.py → FastAPI app {FastAPI}
├─ awaaz/main.py → Voice pipeline main loop
├─ awaaz/api_server.py → FastAPI wrapper for voice
├─ interactive_voice_to_layer3_enhanced.py → Live testing
├─ run_integrated_live_flow.py → End-to-end demo
├─ start_all.py → Mock services orchestrator
└─ greeting_integration.py → Greeting integration

CORE BUSINESS LOGIC
├─ backend/app/services/call_router.py ← LAYER 3 (Routing)
├─ awaaz/src/pipeline/stt.py ← Speech-to-text
├─ awaaz/src/pipeline/tts.py ← Text-to-speech
├─ awaaz/src/pipeline/nlp.py ← NLP processing
├─ awaaz/src/pipeline/lang_detect.py ← Language detection
├─ backend/app/services/llm_service.py ← LLM response gen
├─ audio_language_greeting_service.py ← Greeting service
└─ database_router.py ← Neon DB connection

SUPPORT MODULES
├─ backend/app/database.py ← SQLAlchemy ORM
├─ backend/app/config.py ← Configuration
├─ backend/app/models.py ← DB models
├─ unified_stt_service.py ← STT abstraction
├─ unified_tts_service.py ← TTS abstraction
├─ awaaz/src/audiosocket_handler.py ← Audio streaming
├─ awaaz/src/vad.py ← Voice activity detection
├─ awaaz/src/ari_client.py ← Asterisk integration
└─ awaaz/src/session_store.py ← Call state management

INFRASTRUCTURE & TESTING
├─ ai-services/speech_to_text/whisper_server.py ← STT server
├─ ai-services/text_to_speech/coqui_tts.py ← TTS server
├─ ai-services/llm/sarvam_client.py ← LLM client
├─ test_*.py (many test files)
├─ verify_system.py ← System checks
└─ requirements.txt, requirements-db.txt ← Dependencies
```

---

## 🌐 Environment Variables Map

```
Backend Configuration (backend/.env)
├─ STT_API=http://localhost:9000
├─ TTS_API=http://localhost:9001
├─ LLM_API=http://localhost:9002
├─ REDIS_HOST=localhost
├─ SARVAM_API_KEY={your-api-key}
├─ SARVAM_API_ENDPOINT=https://api.sarvam.ai/v1/chat/completions
└─ USE_MOCK_NLP=false (true for development)

Voice Pipeline Configuration (awaaz/.env)
├─ GROQ_API_KEY={your-groq-key}
├─ FASTTEXT_MODEL_PATH=/tmp/lid.176.bin
├─ OLLAMA_URL=http://localhost:11434/api/generate
├─ OLLAMA_MODEL=llama3.2:3b
├─ MIXED_LANG_THRESHOLD=0.20
├─ PURE_LANG_THRESHOLD=0.80
└─ ENGLISH_HEAVY_THRESHOLD=0.35

Database Configuration (Can be in any .env)
├─ DATABASE_URL=postgresql://user:pass@host/db (Neon)
├─ DB_HOST=host.neon.tech
├─ DB_PORT=5432
├─ DB_NAME=database_name
├─ DB_USER=user
└─ DB_PASSWORD=password

Asterisk Configuration (awaaz/config.yaml)
├─ asterisk.host=127.0.0.1
├─ asterisk.ari_port=8088
├─ asterisk.ari_username=asterisk
├─ asterisk.ari_password=asterisk
├─ audiosocket.port=8090
└─ [More VAD, STT, TTS settings]
```

---

**Generated**: March 25, 2026 | **Audit Status**: ✅ Complete
