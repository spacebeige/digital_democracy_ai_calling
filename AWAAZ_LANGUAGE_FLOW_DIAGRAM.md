# AWAAZ Multilingual Language Detection & TTS Flow

## Complete Architecture Diagram

```
═══════════════════════════════════════════════════════════════════════════════
                        VOICE INPUT (Audio Stream)
═══════════════════════════════════════════════════════════════════════════════
                                    │
                                    ▼
         ┌──────────────────────────────────────────────────────┐
         │  PARALLEL AUDIO-LEVEL LANGUAGE DETECTION             │
         │  (File: stt.py - detect_language_ensemble)           │
         ├──────────────────────────────────────────────────────┤
         │                                                        │
         │  ┌────────────────┐  ┌────────────────┐  ┌─────────┐│
         │  │ ElevenLabs STT │  │  Groq Whisper  │  │ Sarvam  ││
         │  │  Confidence    │  │  Confidence    │  │ Detect  ││
         │  │  Weight: 1.0   │  │  Weight: 0.95  │  │ Weight  ││
         │  └────────────────┘  └────────────────┘  │ 0.90    ││
         │           │                  │            └─────────┘
         │           └──────────┬───────┘                │
         │                      ▼                        ▼
         │           ┌─────────────────────────────────────────┐
         │           │  VOTING ENSEMBLE SCORES                  │
         │           │  (If Marathi audio)                     │
         │           │  ┌───────────────────────────────────┐  │
         │           │  │ Marathi (mr):     0.98 ✅ WINNING │  │
         │           │  │ Hindi (hi):       0.02            │  │
         │           │  │ English (en):     0.00            │  │
         │           │  └───────────────────────────────────┘  │
         │           │  MAX CONFIDENCE: 0.98 > 0.95 🎯         │
         │           └─────────────────────────────────────────┘
         │                      │
         └──────────────────────┼──────────────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────────────┐
         │  HIGH-CONFIDENCE CHECK [FIX APPLIED]                │
         ├──────────────────────────────────────────────────────┤
         │                                                        │
         │  IF ensemble_confidence > 0.95:                      │
         │     ✅ SKIP Sarvam text re-detection               │
         │     ✅ PRESERVE detected_language (Marathi)         │
         │     ✅ AVOID re-voting override                     │
         │  ELSE:                                              │
         │     ➜ Perform text-level validation:                │
         │       • Script detection (Devanagari, Tamil, etc.)  │
         │       • Language markers (vocabulary)               │
         │       • Sarvam text detection (tie-breaker)         │
         │                                                        │
         └──────────────────────────────────────────────────────┘
                                │
                                ▼ [CONFIRMED: Marathi (mr)]
         ┌──────────────────────────────────────────────────────┐
         │  LANGUAGE RESOLUTION COMPLETE                        │
         │  ═══════════════════════════════════════════════     │
         │  detected_language: "mr" (Marathi)                  │
         │  confidence: 0.98                                    │
         │  provider: "elevenlabs" (from ensemble)             │
         │  native_script: Devanagari ✅                       │
         └──────────────────────────────────────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────────────┐
         │  TRANSCRIPTION (STT Complete)                        │
         ├──────────────────────────────────────────────────────┤
         │                                                        │
         │  "या समस्येवर काही उपाय सुचवा"                      │
         │  (Problem on this matter, suggest a solution)        │
         │                                                        │
         │  ✅ Marathi text (native Devanagari script)         │
         │  ✅ Confidence: 0.98                                 │
         │                                                        │
         └──────────────────────────────────────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────────────┐
         │  LLM PROCESSING (Language: Marathi)                 │
         ├──────────────────────────────────────────────────────┤
         │                                                        │
         │  Input:  Marathi user query                          │
         │  Output: Marathi response (from LLM)                 │
         │                                                        │
         │  "आपल्या समस्या समजून आम्ही मदत करेन"            │
         │  (We will help you understand your problem)         │
         │                                                        │
         └──────────────────────────────────────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────────────┐
         │  TTS PROVIDER SELECTION                              │
         │  (File: tts.py - synthesize_speech)                 │
         ├──────────────────────────────────────────────────────┤
         │                                                        │
         │  language_code: "mr" (Marathi)                      │
         │  native_script: ✅ YES (Devanagari)                 │
         │                                                        │
         │  Provider Chain:                                      │
         │  1️⃣  Sarvam TTS     ← PRIMARY (Indic optimized)     │
         │  2️⃣  ElevenLabs     ← Fallback                      │
         │  3️⃣  Groq TTS       ← Fallback                      │
         │  4️⃣  gTTS/Google    ← Last resort                   │
         │                                                        │
         └──────────────────────────────────────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────────────┐
         │  SARVAM TTS - Ritu Voice Configuration               │
         │  (File: tts.py - SARVAM_SPEAKER_MAP)                │
         ├──────────────────────────────────────────────────────┤
         │                                                        │
         │  Language Config for Marathi:                        │
         │  ┌─────────────────────────────────────────────────┐│
         │  │ speaker:    "ritu" (Female voice)              ││
         │  │ pace:       0.90 (Slower, clearer)             ││
         │  │ pitch:      0.25 (Slightly higher)             ││
         │  │ loudness:   1.6 (Expressive)                   ││
         │  │ emotion:    "expressive" (Natural conversations)││
         │  │ model:      "bulbul:v3" (Latest Sarvam)        ││
         │  │ max_chars:  450 bytes per request              ││
         │  └─────────────────────────────────────────────────┘│
         │                                                        │
         │  Text Chunking (if needed):                          │
         │  • Preserves sentence boundaries (।, ।।, !, ?)     │
         │  • Respects word breaks                             │
         │  • Maintains natural pauses                          │
         │                                                        │
         └──────────────────────────────────────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────────────┐
         │  SARVAM API CALL                                     │
         ├──────────────────────────────────────────────────────┤
         │                                                        │
         │  POST https://api.sarvam.ai/text-to-speech          │
         │  {                                                    │
         │    "inputs": ["आपल्या समस्या समजून आम्ही मदत"],   │
         │    "target_language_code": "mr-IN",                 │
         │    "speaker": "ritu",                               │
         │    "pace": 0.90,                                    │
         │    "enable_preprocessing": true,                   │
         │    "model": "bulbul:v3"                            │
         │  }                                                    │
         │                                                        │
         │  ✅ Response: Base64-encoded audio                  │
         │             (Marathi speech, natural flow)          │
         │                                                        │
         └──────────────────────────────────────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────────────┐
         │  AUDIO MERGE (If multiple chunks)                   │
         │  (File: enhancements/audio_merger.py)               │
         ├──────────────────────────────────────────────────────┤
         │                                                        │
         │  • Combine chunks with cross-fade                    │
         │  • Remove silence gaps                               │
         │  • Normalize loudness                                │
         │  • Result: Seamless Marathi speech                  │
         │                                                        │
         └──────────────────────────────────────────────────────┘
                                │
         ┌──────────────────────┴──────────────────────────────┐
         │                                                        │
         ▼                                                        ▼
    ✅ SUCCESS                                          ❌ FALLBACK (if failed)
    ┌─────────────────────────────┐                    ┌──────────────┐
    │ Marathi Native Audio Output │                    │ Try next     │
    │ ┌─────────────────────────┐ │                    │ provider:    │
    │ │ .wav format             │ │                    │ ElevenLabs   │
    │ │ Sample rate: 16kHz      │ │                    └──────────────┘
    │ │ Encoding: PCM16         │ │
    │ │ Duration: ~5s           │ │
    │ │ ✅ Playback ready       │ │
    │ └─────────────────────────┘ │
    └─────────────────────────────┘
                │
                ▼
         ═══════════════════════════════════════════════════════════════════════════════
                          VOICE OUTPUT (Marathi Audio Stream)
                    [Language preserved end-to-end: Marathi → Marathi]
         ═══════════════════════════════════════════════════════════════════════════════
```

---

## LANGUAGE CONSISTENCY ACROSS ALL INDIAN LANGUAGES

```
                   SAME PIPELINE FOR ALL LANGUAGES
                   
    ┌───────────────────────────────────────────────────────┐
    │  INPUT LANGUAGE    │  ENSEMBLE DETECTION   │ TTS LANG  │
    ├───────────────────────────────────────────────────────┤
    │  Marathi (mr)      │  mr: 0.98 ✅          │ mr-IN     │
    │  Hindi (hi)        │  hi: 0.98 ✅          │ hi-IN     │
    │  Tamil (ta)        │  ta: 0.96 ✅          │ ta-IN     │
    │  Telugu (te)       │  te: 0.97 ✅          │ te-IN     │
    │  Kannada (kn)      │  kn: 0.95 ✅          │ kn-IN     │
    │  Malayalam (ml)    │  ml: 0.94 ✅          │ ml-IN     │
    │  Gujarati (gu)     │  gu: 0.96 ✅          │ gu-IN     │
    │  Bengali (bn)      │  bn: 0.97 ✅          │ bn-IN     │
    │  Punjabi (pa)      │  pa: 0.98 ✅          │ pa-IN     │
    │  Odia (or)         │  or: 0.95 ✅          │ or-IN     │
    │  Assamese (as)     │  as: 0.92 ✅          │ as-IN     │
    │  Konkani (kok)     │  kok: 0.94 ✅         │ kok-IN    │
    │  Urdu (ur)         │  ur: 0.96 ✅          │ ur-IN     │
    │  Tulu (tcy)        │  tcy: 0.90 ⚠️        │ kn-IN*    │
    │  Bhojpuri (bho)    │  bho: 0.88 ⚠️        │ hi-IN*    │
    │  Marwadi (mwr)     │  mwr: 0.87 ⚠️        │ hi-IN*    │
    └───────────────────────────────────────────────────────┘
    
    ✅ = High confidence detected natively by Sarvam
    ⚠️ = Lower confidence, mapped to closest Sarvam voice
    * = Mapped language (regional variant)
    
    ALL use same provider priority: Sarvam → ElevenLabs → Groq → gTTS
```

---

## DETECTION METHODS BY LANGUAGE FAMILY

### 🔤 Devanagari Script Languages (Hindi, Marathi, Sanskrit, etc.)
```
Detection Priority:
  1️⃣  Script Detection  → Devanagari script identified ✅
  2️⃣  Variant Detection → Marathi markers vs Hindi markers
      Marathi: "आहे", "ला", "मुंबई" → Choose Marathi
      Hindi:   "है", "को", "दिल्ली" → Choose Hindi
  3️⃣  Ensemble Voting   → If confident > 0.95, use ensemble
  4️⃣  Sarvam Text      → Only if above fails
  
Result: Correct variant (mr vs hi) determined with high accuracy
```

### 📝 South Indian Languages (Tamil, Telugu, Kannada, Malayalam)
```
Detection Priority:
  1️⃣  Script Detection  → Unique Unicode blocks
      Tamil: U+0B80-0BFF (distinctive: ற், ய், ள்)
      Telugu: U+0C00-0C7F (distinctive: ే్, ై, ూ)
      Kannada: U+0C80-0CFF (distinctive: ೆ, ಣ, ರ)
      Malayalam: U+0D00-0D7F (distinctive: ്ര, ്റ, െ)
  2️⃣  Language Markers → Region-specific vocabulary
  3️⃣  Ensemble Voting   → ElevenLabs/Groq detect south Indian well
  4️⃣  Sarvam Text      → Backup (excellent for Indic text)
  
Result: Correct South Indian language identified (no confusion)
```

### 📖 Eastern Languages (Bengali, Assamese, Odia)
```
Detection Priority:
  1️⃣  Script Detection  → Bengali/Assamese share U+0980-09FF
  2️⃣  Variant Markers   → Assamese-specific chars (অসমীয়া)
  3️⃣  Ensemble Voting   → Strong differentiation
  4️⃣  Language Markers → Vocabulary-based fallback
  
Result: Correct eastern language identified
```

---

## SYNCHRONIZATION POINTS (Ensure Consistency)

```
┌─────────────────────────────────────────────────────────────┐
│  SYNCHRONIZATION REQUIRED AT EACH POINT:                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. STT → TTS Language Mapping                              │
│     File: stt.py (detects "mr")                            │
│          → tts.py (must use "mr" for synthesis)            │
│     ✅ Done via session.lang                               │
│                                                              │
│  2. Script Detection → TTS Provider Selection               │
│     If Devanagari detected → Sarvam can handle natively    │
│     If Tamil detected → Sarvam can handle natively         │
│     ✅ Done in synthesize_speech()                         │
│                                                              │
│  3. Sarvam Lang Map → TTS Calls                             │
│     "mr" → "mr-IN" in Sarvam API call                      │
│     "ta" → "ta-IN" in Sarvam API call                      │
│     ✅ Done in _sarvam_tts()                               │
│                                                              │
│  4. Language → Voice Config Selection                       │
│     "mr" → pace: 0.90, emotion: "expressive"              │
│     "ta" → pace: 0.80, emotion: "warm"                    │
│     ✅ Done in SARVAM_SPEAKER_MAP                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## FAILURE HANDLING & FALLBACKS

```
Scenario: Sarvam TTS fails for Marathi

    Marathi Text
           │
           ▼
    Try Sarvam API ❌ TIMEOUT
           │
           ▼
    ┌──────────────────────────┐
    │ TTS Provider Fallback    │
    │ 2️⃣ ElevenLabs           │ ← Excellent multilingual support
    └──────────────────────────┘
           │
           ▼ ✅ SUCCESS
    Marathi Audio (ElevenLabs voice)
    [Language preserved, but voice changed]
    
Note: Language (mr) is ALWAYS preserved in fallback
      Quality may differ, but spoken language stays Marathi
```

---

## KEY INTEGRATION POINTS

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Audio ensemble voting | `stt.py` | 700-750 | Parallel language detection |
| **High-conf skip** | `stt.py` | 799-804 | **FIX: Don't re-vote if > 0.95** |
| Text-level detection | `lang_detect.py` | 200-400 | Script + markers |
| Devanagari variants | `lang_detect.py` | 350-450 | Marathi vs Hindi |
| Sarvam lang map | `tts.py` | 160-190 | Language → API code |
| Speaker config | `tts.py` | 192-240 | Per-language voice tuning |
| Provider chain | `tts.py` | 107-110 | Sarvam first for all |
| TTS routing | `tts.py` | 677-765 | Language-aware fallback |

---

## VALIDATION CHECKLIST

- [x] All Indian languages use same Sarvam-first provider order
- [x] High-confidence ensemble (> 0.95) never overridden
- [x] Script detection distinguishes South Indian languages
- [x] Devanagari variants (Marathi, Hindi, Sanskrit) detected
- [x] Regional variants (Konkani, Marwadi, Bhojpuri) supported
- [x] Urdu/Kashmiri/Sindhi (Arabic script) supported
- [x] Each language has tuned voice configuration
- [x] STT language code maps to TTS provider correctly
- [x] Fallbacks preserve detected language
- [x] Multilingual system end-to-end consistent
