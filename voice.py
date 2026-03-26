"""
AWAAZ — Voice Recognition + Response Loop
Single runnable file. Citizen speaks → detect lang/accent → STT → model → TTS → citizen hears.

INSTALL (run once):
    pip install faster-whisper silero-vad transformers torch groq gTTS soundfile numpy scipy pydub
    pip install TTS       # Coqui TTS (optional, better Hindi voice)
    pip install fasttext  # token-level language ID — replaces all heuristic lang detection

    # fastText model (lid.176.bin — 126MB, download once):
    #   wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin -O /tmp/lid.176.bin
    # OR set env var: FASTTEXT_MODEL_PATH=/path/to/lid.176.bin

    # For Ollama local fallback: curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3.2:3b

    # IndicWav2Vec (accent correction — optional, improves regional accuracy):
    # Downloads automatically on first run from HuggingFace (~900MB)

USAGE:
    # With a mic (live call simulation):
    python awaaz_voice.py --mode mic

    # With a pre-recorded WAV file:
    python awaaz_voice.py --mode file --input path/to/audio.wav

    # With Asterisk AGI (production):
    python awaaz_voice.py --mode asterisk

ENV VARS (optional — only needed if using Groq):
    export GROQ_API_KEY=your_free_key_here
"""

import os
import sys
import uuid
import time
import json
import wave
import queue
import struct
import asyncio
import argparse
import tempfile
import threading
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

SAMPLE_RATE       = 16000       # Hz — Whisper expects 16kHz
CHUNK_SIZE        = 512         # samples per VAD chunk
SILENCE_THRESHOLD = 0.7         # seconds of silence = end of utterance
MAX_UTTERANCE_S   = 30          # max seconds before force-flush
GROQ_MODEL        = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
OLLAMA_MODEL      = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_URL        = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
WHISPER_MODEL     = "small"     # tiny / base / small / medium
MAX_TURNS         = 10          # end call after N turns
REDIS_TTL         = 7200        # 2 hours
# fastText LID model path — override with env var FASTTEXT_MODEL_PATH
FASTTEXT_MODEL_PATH = os.environ.get("FASTTEXT_MODEL_PATH", "/tmp/lid.176.bin")
# Minimum fraction of words in a non-primary language to call input "mixed"
MIXED_LANG_THRESHOLD = float(os.environ.get("MIXED_LANG_THRESHOLD", "0.20"))
# Minimum share for dominant language to classify utterance as "pure"
PURE_LANG_THRESHOLD = float(os.environ.get("PURE_LANG_THRESHOLD", "0.80"))
# If English share crosses this, TTS normalizer may keep common English tokens
ENGLISH_HEAVY_THRESHOLD = float(os.environ.get("ENGLISH_HEAVY_THRESHOLD", "0.35"))

# All 14 Indian languages — ISO code → display name + gTTS code
LANGUAGES = {
    "hi":    {"name": "Hindi",     "gtts": "hi",  "script": "Devanagari"},
    "ta":    {"name": "Tamil",     "gtts": "ta",  "script": "Tamil"},
    "te":    {"name": "Telugu",    "gtts": "te",  "script": "Telugu"},
    "mr":    {"name": "Marathi",   "gtts": "mr",  "script": "Devanagari"},
    "bn":    {"name": "Bengali",   "gtts": "bn",  "script": "Bengali"},
    "gu":    {"name": "Gujarati",  "gtts": "gu",  "script": "Gujarati"},
    "kn":    {"name": "Kannada",   "gtts": "kn",  "script": "Kannada"},
    "ml":    {"name": "Malayalam", "gtts": "ml",  "script": "Malayalam"},
    "pa":    {"name": "Punjabi",   "gtts": "pa",  "script": "Gurmukhi"},
    "or":    {"name": "Odia",      "gtts": "or",  "script": "Odia"},
    "as":    {"name": "Assamese",  "gtts": "as",  "script": "Bengali"},
    "ur":    {"name": "Urdu",      "gtts": "ur",  "script": "Nastaliq"},
    "en":    {"name": "English",   "gtts": "en",  "script": "Latin"},
    "hi-en": {"name": "Hinglish",  "gtts": "hi",  "script": "Mixed"},
}

# Accent region → TTS pace/pause adjustments
ACCENT_PACE = {
    "hi-UP-rural":  {"rate": 0.85, "pause_ms": 400},
    "hi-UP-urban":  {"rate": 1.0,  "pause_ms": 250},
    "hi-MH":        {"rate": 1.05, "pause_ms": 200},
    "hi-DL":        {"rate": 1.1,  "pause_ms": 150},
    "hi-RJ":        {"rate": 0.9,  "pause_ms": 350},
    "hi-MP":        {"rate": 0.95, "pause_ms": 300},
    "ta-TN-rural":  {"rate": 0.85, "pause_ms": 400},
    "ta-TN-urban":  {"rate": 1.0,  "pause_ms": 250},
    "mr-PUNE":      {"rate": 1.0,  "pause_ms": 250},
    "mr-VD":        {"rate": 0.9,  "pause_ms": 300},
    "bn-WB":        {"rate": 1.0,  "pause_ms": 250},
    "default":      {"rate": 1.0,  "pause_ms": 250},
}

# Emergency keywords per language
EMERGENCY_KEYWORDS = {
    "hi": ["aag", "aag lagi", "dacoiti", "maar diya", "accident", "hospital",
           "ambulance", "bachao", "khoon", "loot", "rape", "kidnap", "baadhh", "toofan"],
    "ta": ["tī", "tiruttam", "uதவி", "āpatttu", "ambulance"],
    "te": ["aagu", "dacoity", "accident", "āspathri", "ambulance", "āpadha"],
    "mr": ["aag", "apghāt", "ruge", "ambulans", "vāchavā"],
    "bn": ["āgun", "dākoiti", "durghațanā", "āmbulens", "bāṃcāo"],
    "en": ["fire", "robbery", "accident", "ambulance", "help", "dying", "flood", "attack"],
}

# Greeting per language
GREETINGS = {
    "hi":    "Namaste! Aap kya problem report karna chahte hain?",
    "ta":    "Vanakkam! Nīṅkaḷ eந்த piraccanai paṟṟi aṟivikka virumbukirīrkaḷ?",
    "te":    "Namaskaram! Mీరు eమి report cheyālanukuntunnāru?",
    "mr":    "Namaskar! Tumhāla koṇatī samasya nondavāyachi āhe?",
    "bn":    "Namaskar! Āpni ki samasyā report korte cān?",
    "gu":    "Namaskar! Tamāre śī samasyā report karavī che?",
    "kn":    "Namaskara! Nīvu yaava samasyeyannु report māḍabēkāgide?",
    "ml":    "Namaskāram! Taṅkaḷkku enthu praśnam report ceyyāṇam?",
    "pa":    "Sat Sri Akal! Tusi ki samasya report karnī chahunde ho?",
    "ur":    "Assalam-o-Alaikum! Aap kya masla report karna chahte hain?",
    "en":    "Hello! What problem would you like to report today?",
    "hi-en": "Hello! Aap kya problem report karna chahte hain?",
    "default": "Namaste! Aap kya problem report karna chahte hain?",
}

# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class CallerProfile:
    session_id:       str   = field(default_factory=lambda: str(uuid.uuid4()))
    lang:             str   = "hi"
    lang_name:        str   = "Hindi"
    accent_region:    str   = "default"
    formality_score:  float = 0.5
    formality_label:  str   = "STANDARD"
    script:           str   = "Devanagari"
    gtts_lang:        str   = "hi"
    detected_at_turn: int   = 1
    confidence:       float = 0.0
    turn_number:      int   = 0
    state:            str   = "GREETING"
    history:          list  = field(default_factory=list)
    is_emergency:     bool  = False
    # ── Added for token-level language detection ──────────────
    # "pure"  → ≥80% words in one language
    # "mixed" → significant presence of a second language (e.g. Hinglish)
    lang_mode:         str  = "pure"
    # Per-language word fraction, e.g. {"hi": 0.62, "en": 0.38}
    lang_distribution: dict = field(default_factory=dict)


# ─────────────────────────────────────────────
# MODULE 1 — VAD (Voice Activity Detection)
# ─────────────────────────────────────────────

class VADProcessor:
    """
    Silero VAD — strips silence, finds utterance boundaries.
    Loads a 1MB model, runs fully on CPU.
    """
    def __init__(self):
        self.model = None
        self.is_loaded = False

    def load(self):
        try:
            import torch
            self.model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                onnx=False
            )
            self.get_speech_ts = utils[0]
            self.is_loaded = True
            print("[VAD] Silero VAD loaded OK")
        except Exception as e:
            print(f"[VAD] WARNING: Silero VAD failed to load ({e}). Using energy-based fallback.")
            self.is_loaded = False

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Returns True if the chunk contains speech."""
        if self.is_loaded:
            try:
                import torch
                tensor = torch.FloatTensor(audio_chunk)
                confidence = self.model(tensor, SAMPLE_RATE).item()
                return confidence > 0.5
            except Exception:
                pass
        # Energy-based fallback
        rms = np.sqrt(np.mean(audio_chunk.astype(float) ** 2))
        return rms > 300

    def find_utterance_boundaries(self, audio: np.ndarray) -> list:
        """Find speech segments in a longer audio array."""
        if self.is_loaded:
            try:
                import torch
                tensor = torch.FloatTensor(audio)
                speeches = self.get_speech_ts(tensor, self.model, sampling_rate=SAMPLE_RATE)
                return [(s["start"], s["end"]) for s in speeches]
            except Exception:
                pass
        # Fallback: return the whole audio as one segment
        return [(0, len(audio))]


# ─────────────────────────────────────────────
# MODULE 2 — STT (Speech to Text)
# ─────────────────────────────────────────────

class STTProcessor:
    """
    faster-whisper — transcribes audio in 14 Indian languages.
    Loads once, never reloaded. asyncio 5-slot pool.
    """
    def __init__(self):
        self.model = None
        self._semaphore = asyncio.Semaphore(5)

    def load(self):
        try:
            from faster_whisper import WhisperModel
            device = "cpu"
            compute_type = "int8"
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    compute_type = "float16"
                    print("[STT] GPU detected — using CUDA")
            except Exception:
                pass
            self.model = WhisperModel(WHISPER_MODEL, device=device, compute_type=compute_type)
            print(f"[STT] faster-whisper ({WHISPER_MODEL}) loaded on {device}")
        except ImportError:
            print("[STT] ERROR: faster-whisper not installed. Run: pip install faster-whisper")
            sys.exit(1)

    def detect_language(self, audio_path: str) -> tuple[str, float]:
        """
        Detect language from first 30 seconds of audio.
        Returns (lang_code, confidence).
        """
        try:
            segments, info = self.model.transcribe(
                audio_path,
                task="transcribe",
                language=None,          # auto-detect
                beam_size=1,
                best_of=1,
                vad_filter=True,
            )
            # Consume segments to get language info
            _ = list(segments)
            lang = info.language
            conf = info.language_probability
            # Normalise: faster-whisper returns 'hi', 'ta', etc.
            if lang not in LANGUAGES:
                lang = "hi"  # default to Hindi for India
            print(f"[STT] Language detected: {lang} (confidence: {conf:.2f})")
            return lang, conf
        except Exception as e:
            print(f"[STT] Language detection failed: {e}")
            return "hi", 0.5

    def transcribe(self, audio_path: str, lang: str) -> str:
        """
        Transcribe audio file in the given language.
        Returns plain text string.
        """
        try:
            # Map hi-en (Hinglish) to hi for Whisper
            whisper_lang = lang if lang != "hi-en" else "hi"

            segments, info = self.model.transcribe(
                audio_path,
                language=whisper_lang,
                beam_size=5,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )
            text = " ".join(seg.text.strip() for seg in segments)
            print(f"[STT] Transcribed ({lang}): {text}")
            return text.strip()
        except Exception as e:
            print(f"[STT] Transcription failed: {e}")
            return ""


# ─────────────────────────────────────────────
# MODULE 2b — TOKEN-LEVEL LANGUAGE DETECTION
# ─────────────────────────────────────────────

class TokenLevelLangDetector:
    """
    fastText lid.176.bin — word-level language identification.

    Why fastText instead of heuristics:
    - Covers 176 languages including all Indian ones
    - Sub-100ms for a full sentence even on CPU
    - One model loaded once (singleton pattern below)
    - Generalises to any code-mixed pattern without needing word lists

    Pipeline position: AFTER STT, BEFORE LLM.
    Updates CallerProfile.lang_mode and CallerProfile.lang_distribution.
    """

    _instance = None   # module-level singleton so model loads once per process

    @classmethod
    def get(cls) -> "TokenLevelLangDetector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._model = None
        self._available = False
        self._load()

    def _load(self):
        """Load lid.176.bin once. Silently degrades if fasttext not installed."""
        if not os.path.exists(FASTTEXT_MODEL_PATH):
            print(f"[LANGDET] fastText model not found at {FASTTEXT_MODEL_PATH}.")
            print("[LANGDET] Download: wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin -O /tmp/lid.176.bin")
            print("[LANGDET] Falling back to Whisper sentence-level detection only.")
            return
        try:
            import fasttext
            # suppress fasttext loading noise
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._model = fasttext.load_model(FASTTEXT_MODEL_PATH)
            self._available = True
            print("[LANGDET] fastText LID model loaded OK")
        except ImportError:
            print("[LANGDET] fasttext not installed. Run: pip install fasttext")
        except Exception as e:
            print(f"[LANGDET] fastText load failed: {e}")

    def _predict_word(self, word: str) -> str:
        """
        Predict language for a single word.
        Returns ISO 639-1 code (strips fasttext '__label__' prefix).
        Falls back to 'xx' on any error.
        """
        if not self._available or not word.strip():
            return "xx"
        try:
            labels, _ = self._model.predict(word.strip(), k=1)
            # fasttext returns '__label__hi' etc.
            return labels[0].replace("__label__", "")
        except Exception:
            return "xx"

    def detect(self, text: str, sentence_lang: str) -> tuple[str, dict]:
        """
        Run token-level detection on transcribed text.

        Returns:
            lang_mode:         "pure" | "mixed"
            lang_distribution: {"hi": 0.6, "en": 0.4, ...}

        Algorithm:
        1. Split text into words (no regex heuristics)
        2. Predict language per word with fastText
        3. Compute fraction of each language
        4. If any language other than the primary exceeds MIXED_LANG_THRESHOLD → "mixed"
        """
        if not self._available:
            # Graceful fallback: trust Whisper sentence-level detection
            return "pure", {sentence_lang: 1.0}

        words = [w for w in text.split() if len(w) > 1]  # skip single chars / punctuation
        if not words:
            return "pure", {sentence_lang: 1.0}

        counts: dict = {}
        for w in words:
            lang_code = self._predict_word(w)
            if lang_code != "xx":
                counts[lang_code] = counts.get(lang_code, 0) + 1

        total = sum(counts.values()) or 1
        distribution = {k: round(v / total, 3) for k, v in sorted(
            counts.items(), key=lambda x: -x[1]
        )}

        # Determine mode from observed token distribution (robust to STT sentence-lang errors)
        primary_lang, primary_frac = max(distribution.items(), key=lambda x: x[1])
        second_frac = sorted(distribution.values(), reverse=True)[1] if len(distribution) > 1 else 0.0
        lang_mode = "mixed" if (primary_frac < PURE_LANG_THRESHOLD or second_frac >= MIXED_LANG_THRESHOLD) else "pure"

        print(f"[LANGDET] mode={lang_mode} distribution={distribution}")
        return lang_mode, distribution

    def update_profile(self, text: str, profile: CallerProfile) -> None:
        """
        Convenience method: run detection and mutate profile in-place.
        Call this after every STT transcription.
        """
        mode, dist = self.detect(text, profile.lang)
        profile.lang_mode         = mode
        profile.lang_distribution = dist


# ─────────────────────────────────────────────
# MODULE 3 — ACCENT + FORMALITY DETECTION
# ─────────────────────────────────────────────

class ProfileDetector:
    """
    Detects:
    1. Accent region (via IndicWav2Vec embeddings — cosine similarity)
    2. Formality score — structural features only (sentence length, punctuation,
       question marks). No hardcoded vocabulary lists — those were brittle and
       only covered a fraction of Indian languages.
    Falls back gracefully if models not available.
    """

    def detect_accent(self, audio_path: str, lang: str) -> str:
        """
        Attempt IndicWav2Vec accent detection.
        Falls back to language-based default if model unavailable.
        """
        try:
            from transformers import Wav2Vec2Processor, Wav2Vec2Model
            import torch, soundfile as sf

            # Only attempt for Hindi (best model support)
            if not lang.startswith("hi"):
                return f"{lang}-default"

            audio, sr = sf.read(audio_path)
            if sr != SAMPLE_RATE:
                from scipy.signal import resample
                audio = resample(audio, int(len(audio) * SAMPLE_RATE / sr))

            # Use AI4Bharat model — downloads ~900MB once from HuggingFace
            processor = Wav2Vec2Processor.from_pretrained("ai4bharat/indicwav2vec-v2-all")
            model = Wav2Vec2Model.from_pretrained("ai4bharat/indicwav2vec-v2-all")

            inputs = processor(audio, sampling_rate=SAMPLE_RATE, return_tensors="pt")
            with torch.no_grad():
                embedding = model(**inputs).last_hidden_state.mean(dim=1).squeeze()

            # Simple heuristic: use embedding norm to guess urban vs rural
            # In production replace with a trained classifier on reference clips
            norm = embedding.norm().item()
            if norm > 15:
                return "hi-UP-urban"
            else:
                return "hi-UP-rural"

        except Exception:
            # Fallback: language-based default accent
            defaults = {
                "hi": "hi-UP-rural", "ta": "ta-TN-urban",
                "mr": "mr-PUNE",     "bn": "bn-WB",
                "te": "default",     "en": "default",
            }
            return defaults.get(lang, "default")

    def detect_formality(self, text: str, lang: str) -> tuple[float, str]:
        """
        Score formality 0.0–1.0 using structural features only.

        Why no vocabulary lists:
        - Hardcoded word lists break for every dialect variant
        - They require per-language maintenance
        - Structural signals (sentence length, punctuation) are language-agnostic
          and generalise to all 14 Indian languages without a single language-specific line

        Features used:
        - Average words per sentence (universal: longer → more formal)
        - Presence of sentence-ending punctuation (। . ? !)
        - Total word count (too-short utterances → informal)
        """
        if not text:
            return 0.3, "SIMPLE"

        words = text.split()
        total = len(words)
        if total == 0:
            return 0.3, "SIMPLE"

        # Split on both Devanagari danda and Latin period/exclamation/question
        import re
        sentences = [s.strip() for s in re.split(r'[।.!?]', text) if s.strip()]
        n_sent    = len(sentences) or 1
        avg_len   = sum(len(s.split()) for s in sentences) / n_sent

        # Punctuation density (more punctuation → more structured → more formal)
        punct_count  = sum(1 for c in text if c in "।.!?,;:")
        punct_score  = min(punct_count / max(total, 1) * 3, 1.0)

        # Length score (longer sentences = more formal register)
        length_score = min(avg_len / 15, 1.0)

        # Word count score (very short = informal/casual)
        count_score  = min(total / 20, 1.0)

        score = round(length_score * 0.5 + punct_score * 0.3 + count_score * 0.2, 2)

        if score < 0.35:
            label = "SIMPLE"
        elif score < 0.65:
            label = "STANDARD"
        else:
            label = "FORMAL"

        print(f"[PROFILE] Formality: {score:.2f} → {label}")
        return score, label


# ─────────────────────────────────────────────
# MODULE 4 — MODEL (LLM reply generation)
# ─────────────────────────────────────────────

class ModelProcessor:
    """
    Generates reply using:
    1. Groq free tier (Llama 3.1 8B) — fast, needs internet
    2. Ollama local (Llama 3.2 3B) — slower, works offline
    Falls back automatically.
    """

    def __init__(self):
        self.groq_client = None
        self._load_groq()

    def _load_groq(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            print("[MODEL] No GROQ_API_KEY set. Will use Ollama local fallback.")
            return
        try:
            from groq import Groq
            self.groq_client = Groq(api_key=api_key)
            print("[MODEL] Groq client loaded OK")
        except ImportError:
            print("[MODEL] groq package not installed. Run: pip install groq")
        except TypeError as e:
            print(f"[MODEL] ⚠️ Groq initialization failed (version incompatibility): {e}")
            print("[MODEL] Will use Ollama local fallback instead.")
            self.groq_client = None

    def _build_system_prompt(self, profile: CallerProfile) -> str:
        max_sentences = {"SIMPLE": 2, "STANDARD": 3, "FORMAL": 4}.get(
            profile.formality_label, 2
        )
        history_text = "\n".join(
            f"Turn {i+1} - Citizen: {t['citizen']}\nAssistant: {t['assistant']}"
            for i, t in enumerate(profile.history[-3:])
        ) or "No previous turns."

        # Build a human-readable language distribution string for the prompt
        dist_str = ", ".join(
            f"{k}: {int(v*100)}%"
            for k, v in profile.lang_distribution.items()
        ) if profile.lang_distribution else f"{profile.lang}: 100%"

        # Code-mix instruction block — injected only when relevant
        if profile.lang_mode == "mixed":
            lang_style_rule = (
                f"The caller is speaking in a MIXED language style ({dist_str}). "
                f"Mirror their style naturally — reply in the same mixed form they used. "
                f"Do NOT translate everything to pure {profile.lang_name}. "
                f"Do NOT switch fully to English. "
                f"Use the natural hybrid form a fluent speaker would use in conversation."
            )
        else:
            lang_style_rule = (
                f"The caller is speaking pure {profile.lang_name}. "
                f"Reply ONLY in {profile.lang_name}. "
                f"Avoid English words unless the caller used them."
            )

        return f"""You are AWAAZ, a government grievance assistant on a live phone call in India.

CALLER PROFILE:
- Language: {profile.lang} ({profile.lang_name})
- Language mode: {profile.lang_mode} ({dist_str})
- Accent region: {profile.accent_region}
- Formality: {profile.formality_label} (score: {profile.formality_score})
- Turn: {profile.turn_number}
- State: {profile.state}

CONVERSATION SO FAR:
{history_text}

LANGUAGE STYLE RULE:
{lang_style_rule}

STRICT RULES:
1. {lang_style_rule}
2. Use {profile.formality_label} vocabulary register
3. Maximum {max_sentences} sentences
4. ONE question per reply maximum — never ask two questions
5. NO markdown, NO bullet points, NO lists
6. If state is GREETING: greet and ask what problem to report
7. If state is GATHERING: ask ONE clarifying question about the complaint
8. If state is CONFIRMING: summarise complaint in 1 sentence and ask for confirmation
9. If state is EMERGENCY: acknowledge, say officer is being notified, give 2-hour callback promise
10. Numbers must be read digit by digit in the caller's language
11. Output ONLY the spoken reply — nothing else, no labels, no prefixes"""

    def generate(self, user_text: str, profile: CallerProfile) -> str:
        """Generate reply. Tries Groq first, falls back to Ollama, then rule-based."""
        system_prompt = self._build_system_prompt(profile)

        # Try Groq
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_text},
                    ],
                    max_tokens=150,
                    temperature=0.4,
                )
                reply = response.choices[0].message.content.strip()
                print(f"[MODEL] Groq reply: {reply}")
                return reply
            except Exception as e:
                print(f"[MODEL] Groq failed ({e}), trying Ollama...")

        # Try Ollama local
        try:
            import urllib.request
            payload = json.dumps({
                "model": OLLAMA_MODEL,
                "prompt": f"SYSTEM: {system_prompt}\n\nUSER: {user_text}\nASSISTANT:",
                "stream": False,
                "options": {"num_predict": 150, "temperature": 0.4},
            }).encode()
            req = urllib.request.Request(
                OLLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                reply = data.get("response", "").strip()
                print(f"[MODEL] Ollama reply: {reply}")
                return reply
        except Exception as e:
            print(f"[MODEL] Ollama failed ({e}), using rule-based fallback...")

        # Rule-based fallback (always works, no internet needed)
        return self._rule_based_reply(profile)

    def _rule_based_reply(self, profile: CallerProfile) -> str:
        """Minimal rule-based replies when all LLMs fail."""
        state = profile.state
        lang  = profile.lang

        fallbacks = {
            "GREETING":   GREETINGS.get(lang, GREETINGS["default"]),
            "GATHERING":  {
                "hi": "Kripya apni samasya thoda aur spasht bataiye.",
                "ta": "Dayavu seytu ungal pirachchanaiyai konjam vivarama sollungal.",
                "en": "Please describe your problem in a bit more detail.",
            }.get(lang, "Please describe your problem in more detail."),
            "CONFIRMING": {
                "hi": "Kya main yeh complaint darj kar doon?",
                "ta": "Nān inta muṟaiyīṭṭai pathivu ceyyalāmā?",
                "en": "Shall I file this complaint now?",
            }.get(lang, "Shall I file this complaint?"),
            "EMERGENCY":  {
                "hi": "Yeh emergency lag raha hai. Main abhi officer ko inform kar raha hoon.",
                "ta": "Itu āpattu pōl tērukiṟatu. Nān ippoḻutē adhikāriyai thoṭarpu koḷkiṟēṉ.",
                "en": "This sounds like an emergency. I am notifying an officer right now.",
            }.get(lang, "This is an emergency. Notifying officer now."),
        }
        return fallbacks.get(state, fallbacks["GREETING"])

    # ── Change 3: LLM-based TTS normalisation ─────────────────────────────────
    def normalize_for_tts_llm(self, text: str, profile: CallerProfile) -> str:
        """
        Convert LLM reply into clean, fully speakable form before handing to TTS.

        Why LLM-based instead of regex/dictionary:
        - Regex hacks break on unseen foreign words
        - Dictionary-based transliteration misses context
        - An LLM understands meaning and produces natural spoken output
          in one pass without brittle mappings

        Behaviour:
        - Removes or converts any residual foreign-script tokens
        - Ensures output is in the caller's primary language
        - Preserves numbers, proper nouns, commonly spoken hybrids
        - Optimises for speech clarity, not formal writing

        Only fires if text contains characters from a different script OR
        if lang_mode == "mixed" and formality is SIMPLE (most likely to have
        unpronounceable mixed tokens that confuse TTS).

        Returns original text unchanged if normalisation fails, so TTS always
        has something to say.
        """
        # Skip normalisation if text is already clean enough
        should_normalise = (
            profile.lang_mode == "mixed" and profile.formality_label == "SIMPLE"
        ) or self._has_foreign_script(text, profile.lang)

        if not should_normalise:
            return text

        lang_name = profile.lang_name
        en_share = profile.lang_distribution.get("en", 0.0)
        allow_english = en_share >= ENGLISH_HEAVY_THRESHOLD
        norm_prompt = (
            f"You are a speech preparation assistant. "
            f"Convert the following text into clean, natural spoken {lang_name}. "
            f"Caller language profile: mode={profile.lang_mode}, distribution={profile.lang_distribution}. "
            f"Rules: "
            f"(1) Output language must be {profile.lang}. "
            f"(2) Preserve meaning exactly. "
            f"(3) Keep it conversational and short for speech. "
            f"(4) Remove foreign words naturally; "
            f"{'retain only commonly used English hybrids if needed.' if allow_english else 'avoid English words unless unavoidable proper nouns.'} "
            f"(5) No labels, no explanations, output only the cleaned spoken text.\n\n"
            f"Input: {text}"
        )

        # Reuse same LLM client — no extra model cost
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": norm_prompt}],
                    max_tokens=120,
                    temperature=0.2,   # low temperature for deterministic clean output
                )
                normalised = response.choices[0].message.content.strip()
                if normalised:
                    print(f"[NORM] TTS normalised: {normalised}")
                    return normalised
            except Exception as e:
                print(f"[NORM] Groq normalisation failed ({e}), using original text")

        # Ollama fallback
        try:
            import urllib.request
            payload = json.dumps({
                "model": OLLAMA_MODEL,
                "prompt": norm_prompt,
                "stream": False,
                "options": {"num_predict": 120, "temperature": 0.2},
            }).encode()
            req = urllib.request.Request(
                OLLAMA_URL, data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
                normalised = data.get("response", "").strip()
                if normalised:
                    print(f"[NORM] Ollama normalised: {normalised}")
                    return normalised
        except Exception:
            pass

        # Final fallback: return original — TTS will handle it best-effort
        return text

    def is_affirmative(self, text: str, profile: CallerProfile) -> bool:
        """
        Model-based confirmation detection to avoid hardcoded multilingual word lists.
        Returns False on failure (safe fallback keeps conversation in GATHERING).
        """
        prompt = (
            f"Classify if the user is explicitly confirming/agreeing to proceed in this call context. "
            f"Language profile: mode={profile.lang_mode}, distribution={profile.lang_distribution}. "
            f"Reply with only YES or NO.\n\nUtterance: {text}"
        )

        if self.groq_client:
            try:
                resp = self.groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=5,
                    temperature=0.0,
                )
                return resp.choices[0].message.content.strip().upper().startswith("YES")
            except Exception:
                pass

        try:
            import urllib.request
            payload = json.dumps({
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 5, "temperature": 0.0},
            }).encode()
            req = urllib.request.Request(
                OLLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read())
                return str(data.get("response", "")).strip().upper().startswith("YES")
        except Exception:
            return False

    def _has_foreign_script(self, text: str, lang: str) -> bool:
        """
        Detect if text contains characters from a script different from
        the caller's primary language. Language-agnostic — uses Unicode ranges.

        Why: gTTS/Coqui can mispronounce or skip tokens in the wrong script.
        Catching this here lets normalisation clean it before TTS sees it.
        """
        # Map primary language to its expected Unicode block range
        SCRIPT_RANGES = {
            "hi": (0x0900, 0x097F),   # Devanagari
            "mr": (0x0900, 0x097F),   # Devanagari
            "ta": (0x0B80, 0x0BFF),   # Tamil
            "te": (0x0C00, 0x0C7F),   # Telugu
            "kn": (0x0C80, 0x0CFF),   # Kannada
            "ml": (0x0D00, 0x0D7F),   # Malayalam
            "bn": (0x0980, 0x09FF),   # Bengali
            "as": (0x0980, 0x09FF),   # Bengali (Assamese shares script)
            "gu": (0x0A80, 0x0AFF),   # Gujarati
            "pa": (0x0A00, 0x0A7F),   # Gurmukhi
            "or": (0x0B00, 0x0B7F),   # Odia
            "ur": (0x0600, 0x06FF),   # Arabic/Nastaliq
        }
        primary_range = SCRIPT_RANGES.get(lang)
        if not primary_range:
            return False  # English / unknown — no script check needed

        for ch in text:
            cp = ord(ch)
            # Latin range that isn't punctuation/digit
            if 0x0041 <= cp <= 0x007A and lang not in ("en", "hi-en"):
                return True   # Latin characters in a non-Latin primary language
            # Characters outside the expected Indian script block (and not digits/punct/space)
            if (
                cp > 0x007F
                and not (primary_range[0] <= cp <= primary_range[1])
                and not (0x0900 <= cp <= 0x097F and lang in ("hi", "mr"))  # shared Devanagari
                and ch not in " \t\n।॥,।.!?:;()-\""
            ):
                return True
        return False


# ─────────────────────────────────────────────
# MODULE 5 — TTS (Text to Speech)
# ─────────────────────────────────────────────

class TTSProcessor:
    """
    Text to speech in 14 Indian languages.
    Uses Coqui TTS for Hindi/Marathi/English (offline, better quality).
    Falls back to gTTS for all other languages (needs internet).
    """

    def __init__(self):
        self.coqui_available = False
        self._try_load_coqui()

    def _try_load_coqui(self):
        try:
            from TTS.api import TTS
            self.TTS = TTS
            self.coqui_available = True
            print("[TTS] Coqui TTS available")
        except ImportError:
            print("[TTS] Coqui TTS not installed — using gTTS for all languages")
            print("[TTS] To install Coqui: pip install TTS")

    def synthesize(self, text: str, profile: CallerProfile, output_path: str) -> bool:
        """
        Convert text to speech file at output_path.
        Applies accent-based pace adjustment.
        Returns True on success.
        """
        lang      = profile.lang
        gtts_lang = LANGUAGES.get(lang, {}).get("gtts", "hi")
        pace_cfg  = ACCENT_PACE.get(profile.accent_region, ACCENT_PACE["default"])

        # Try Coqui for Hindi and English (better quality, offline)
        if self.coqui_available and lang in ("hi", "en"):
            try:
                return self._coqui_synth(text, lang, output_path, pace_cfg)
            except Exception as e:
                print(f"[TTS] Coqui failed ({e}), falling back to gTTS")

        # gTTS for all languages
        return self._gtts_synth(text, gtts_lang, output_path, pace_cfg)

    def _coqui_synth(self, text: str, lang: str, output_path: str, pace_cfg: dict) -> bool:
        tts_model = {
            "hi": "tts_models/hi/custom/vits",
            "en": "tts_models/en/ljspeech/tacotron2-DDC",
        }.get(lang, "tts_models/en/ljspeech/tacotron2-DDC")

        tts = self.TTS(model_name=tts_model, progress_bar=False)
        tts.tts_to_file(text=text, file_path=output_path)

        # Apply pace adjustment via pydub
        self._apply_pace(output_path, pace_cfg["rate"])
        print(f"[TTS] Coqui synthesized → {output_path}")
        return True

    def _gtts_synth(self, text: str, gtts_lang: str, output_path: str, pace_cfg: dict) -> bool:
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=gtts_lang, slow=(pace_cfg["rate"] < 0.9))
            mp3_path = output_path.replace(".wav", ".mp3")
            tts.save(mp3_path)
            # Convert mp3 → wav
            self._mp3_to_wav(mp3_path, output_path)
            print(f"[TTS] gTTS synthesized ({gtts_lang}) → {output_path}")
            return True
        except ImportError:
            print("[TTS] ERROR: gTTS not installed. Run: pip install gTTS")
            return False
        except Exception as e:
            print(f"[TTS] gTTS failed: {e}")
            return False

    def _apply_pace(self, wav_path: str, rate: float):
        """Slow down or speed up audio via pydub."""
        if rate == 1.0:
            return
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_wav(wav_path)
            # Change speed without changing pitch (simple frame rate trick)
            new_frame_rate = int(audio.frame_rate * rate)
            adjusted = audio._spawn(
                audio.raw_data,
                overrides={"frame_rate": new_frame_rate}
            ).set_frame_rate(SAMPLE_RATE)
            adjusted.export(wav_path, format="wav")
        except Exception:
            pass  # pace adjustment is optional

    def _mp3_to_wav(self, mp3_path: str, wav_path: str):
        try:
            from pydub import AudioSegment
            AudioSegment.from_mp3(mp3_path).export(wav_path, format="wav")
            os.remove(mp3_path)
        except Exception:
            # If pydub not available, keep mp3 and rename
            import shutil
            shutil.move(mp3_path, wav_path)

    def play(self, wav_path: str):
        """Play audio to speaker (for mic mode testing)."""
        try:
            import subprocess
            # Try multiple players
            for cmd in [
                ["aplay", wav_path],
                ["ffplay", "-nodisp", "-autoexit", wav_path],
                ["mpg123", wav_path],
            ]:
                try:
                    subprocess.run(cmd, check=True,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            print(f"[TTS] Audio saved to {wav_path} — no player found to auto-play")
        except Exception as e:
            print(f"[TTS] Playback error: {e}")


# ─────────────────────────────────────────────
# MODULE 5b — TRANSLITERATION HOOK (PLUGGABLE)
# ─────────────────────────────────────────────

class TransliterationHook:
    """
    Pluggable transliteration layer between LLM reply and TTS.

    Design:
    - Does nothing by default (passthrough)
    - Designed so IndicTrans2 or any other model can be plugged in
      by overriding _transliterate() without changing the pipeline
    - No hardcoded language mappings — the backend model handles all pairs
    - Called only when lang_mode == "mixed" AND text contains Latin script
      in a Devanagari/Dravidian primary language

    To enable IndicTrans2:
        hook = TransliterationHook()
        hook.enable_indictrans2(src="hin_Latn", tgt="hin_Deva")
        # Then the pipeline will auto-use it

    Example:
        "paani nahi aa raha" → "पानी नहीं आ रहा"
    """

    def __init__(self):
        self._backend = None   # set via enable_* methods
        self._src_lang = None
        self._tgt_lang = None

    def set_backend(self, fn, src: str = "", tgt: str = ""):
        """Generic backend registration for pluggable transliteration engines."""
        self._backend = fn
        self._src_lang = src
        self._tgt_lang = tgt

    def enable_indictrans2(self, src: str, tgt: str):
        """
        Plug in AI4Bharat IndicTrans2 as the transliteration backend.
        src/tgt use BCP-47 + script tags e.g. "hin_Latn" → "hin_Deva"
        Requires: pip install indic-transliteration
        """
        try:
            from indic_transliteration.sanscript import transliterate
            self.set_backend(transliterate, src=src, tgt=tgt)
            print(f"[TRANSLIT] IndicTrans2 enabled: {src} → {tgt}")
        except ImportError:
            print("[TRANSLIT] indic-transliteration not installed. Hook is passthrough.")

    def process(self, text: str, profile: CallerProfile) -> str:
        """
        Apply transliteration if backend is configured and input needs it.
        Returns original text if no backend or no Latin script detected.
        """
        if self._backend is None:
            return text   # passthrough — no backend configured

        # Only process if there are Latin chars in a non-Latin primary language
        has_latin = any(0x0041 <= ord(c) <= 0x007A for c in text)
        if not has_latin or profile.lang in ("en", "hi-en"):
            return text

        return self._transliterate(text)

    def _transliterate(self, text: str) -> str:
        """Internal dispatch — override or replace with any backend."""
        if self._backend is None:
            return text
        try:
            # Indic-transliteration backend path (dynamic script codes, no hardcoded pair)
            if self._backend.__name__ == "transliterate":
                from indic_transliteration import sanscript
                src = getattr(sanscript, self._src_lang, None)
                tgt = getattr(sanscript, self._tgt_lang, None)
                if src is None or tgt is None:
                    return text
                result = self._backend(text, src, tgt)
            else:
                result = self._backend(text, self._src_lang, self._tgt_lang)
            print(f"[TRANSLIT] {text} → {result}")
            return result
        except Exception as e:
            print(f"[TRANSLIT] Failed ({e}), returning original")
            return text


# Module-level singleton — import and configure once
transliteration_hook = TransliterationHook()


# ─────────────────────────────────────────────
# MODULE 6 — AUDIO INPUT
# ─────────────────────────────────────────────

class AudioInput:
    """Handles mic recording, file reading, and Asterisk AGI input."""

    def __init__(self, mode: str, input_file: Optional[str] = None):
        self.mode       = mode
        self.input_file = input_file
        self._file_pos  = 0

    def record_utterance(self, session_id: str) -> Optional[str]:
        """
        Record one utterance. Returns path to WAV file, or None on silence/error.
        """
        if self.mode == "file":
            return self._next_file_chunk()
        elif self.mode == "mic":
            return self._record_from_mic(session_id)
        elif self.mode == "asterisk":
            return self._read_asterisk_pipe(session_id)
        return None

    def _record_from_mic(self, session_id: str) -> Optional[str]:
        """Record from microphone until silence."""
        try:
            import pyaudio
        except ImportError:
            print("[AUDIO] pyaudio not installed. Run: pip install pyaudio")
            print("[AUDIO] Falling back to file mode — provide a WAV file with --input")
            return None

        pa       = pyaudio.PyAudio()
        stream   = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        print("[AUDIO] Listening... (speak now)")
        frames          = []
        silent_chunks   = 0
        speech_started  = False
        silence_limit   = int(SILENCE_THRESHOLD * SAMPLE_RATE / CHUNK_SIZE)
        max_chunks      = int(MAX_UTTERANCE_S * SAMPLE_RATE / CHUNK_SIZE)

        vad = VADProcessor()
        vad.load()

        for _ in range(max_chunks):
            data  = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

            if vad.is_speech(audio):
                speech_started = True
                silent_chunks  = 0
                frames.append(data)
            else:
                if speech_started:
                    silent_chunks += 1
                    frames.append(data)
                    if silent_chunks >= silence_limit:
                        break

        stream.stop_stream()
        stream.close()
        pa.terminate()

        if not frames or not speech_started:
            print("[AUDIO] No speech detected")
            return None

        # Save to temp WAV
        out_path = f"/tmp/awaaz_{session_id}_{int(time.time())}.wav"
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(frames))

        print(f"[AUDIO] Recorded utterance → {out_path}")
        return out_path

    def _next_file_chunk(self) -> Optional[str]:
        """Return the input file path (used as-is for file mode)."""
        if self.input_file and os.path.exists(self.input_file):
            return self.input_file
        print(f"[AUDIO] File not found: {self.input_file}")
        return None

    def _read_asterisk_pipe(self, session_id: str) -> Optional[str]:
        """
        Read audio from Asterisk AGI stdin pipe.
        Asterisk writes raw PCM to a named pipe; we save it as WAV.
        """
        pipe_path = f"/tmp/asterisk_audio_{session_id}.raw"
        out_path  = f"/tmp/awaaz_{session_id}_{int(time.time())}.wav"

        if not os.path.exists(pipe_path):
            print(f"[AUDIO] Asterisk pipe not found: {pipe_path}")
            return None

        try:
            with open(pipe_path, "rb") as f:
                raw = f.read(SAMPLE_RATE * 2 * 30)  # max 30s of 16kHz 16-bit mono

            with wave.open(out_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(raw)

            return out_path
        except Exception as e:
            print(f"[AUDIO] Asterisk read error: {e}")
            return None


# ─────────────────────────────────────────────
# EMERGENCY DETECTION
# ─────────────────────────────────────────────

def check_emergency(text: str, lang: str, model_processor: "ModelProcessor" = None) -> bool:
    """
    Detect emergency from transcribed text.

    Two-tier approach:
    1. Fast path: Unicode-safe keyword scan using the EMERGENCY_KEYWORDS table
       as a first-pass filter (kept because emergency detection must be <100ms
       and must work even if the LLM is unavailable).
    2. LLM confirmation (optional, if model_processor provided): sends a
       single-sentence classification prompt to confirm true emergencies and
       reduce false positives from keyword collision.

    The keyword list is NOT used for routing or language detection — it is
    only the fast-path trigger for a life-safety feature where a missed
    emergency is more costly than a false positive.
    """
    keywords = EMERGENCY_KEYWORDS.get(lang, EMERGENCY_KEYWORDS["en"])
    text_lower = text.lower()

    # Fast path
    triggered_keyword = next((kw for kw in keywords if kw in text_lower), None)
    if not triggered_keyword:
        return False

    print(f"[EMERGENCY] Fast-path keyword: '{triggered_keyword}'")

    # LLM confirmation — reduces false positives (e.g. "hospital check-up" vs "need ambulance")
    if model_processor and model_processor.groq_client:
        try:
            confirm_prompt = (
                f"Does this message describe an active emergency requiring immediate help? "
                f"Reply with only YES or NO.\n\nMessage: {text}"
            )
            resp = model_processor.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": confirm_prompt}],
                max_tokens=5,
                temperature=0.0,
            )
            answer = resp.choices[0].message.content.strip().upper()
            is_emergency = answer.startswith("YES")
            print(f"[EMERGENCY] LLM confirmation: {answer} → {is_emergency}")
            return is_emergency
        except Exception:
            pass  # LLM unavailable — trust the keyword

    return True


# ─────────────────────────────────────────────
# MAIN VOICE LOOP
# ─────────────────────────────────────────────

class AWAAZVoiceLoop:
    """
    The complete voice conversation loop.
    Citizen speaks → STT → detect profile → model → TTS → citizen hears.
    Loops until ticket filed or max turns reached.
    """

    def __init__(self, mode: str = "mic", input_file: Optional[str] = None):
        print("\n" + "="*60)
        print("  AWAAZ — Voice Grievance Assistant")
        print("  Loading models... (first run may take a minute)")
        print("="*60 + "\n")

        self.audio    = AudioInput(mode=mode, input_file=input_file)
        self.vad      = VADProcessor()
        self.stt      = STTProcessor()
        self.profiler = ProfileDetector()
        self.model    = ModelProcessor()
        self.tts      = TTSProcessor()
        self.profile  : Optional[CallerProfile] = None

        # Change 1: token-level language detector (singleton — loads fastText once)
        self.langdet  = TokenLevelLangDetector.get()

        # Change 4: transliteration hook (passthrough by default — plug in IndicTrans2 here)
        self.translit = transliteration_hook

        # Load models
        self.vad.load()
        self.stt.load()

        print("\n[AWAAZ] All models loaded. Starting call.\n")

    def run(self):
        """Main loop — runs one full call session."""
        session_id   = str(uuid.uuid4())[:8]
        self.profile = CallerProfile(session_id=session_id)

        print(f"[SESSION] ID: {session_id}")
        print("-" * 40)

        for turn in range(1, MAX_TURNS + 1):
            self.profile.turn_number = turn
            print(f"\n[TURN {turn}] State: {self.profile.state}")

            # ── STEP 1: Record utterance ──────────────────
            audio_path = self.audio.record_utterance(session_id)

            if audio_path is None:
                # Silent call handling
                silent_reply = self._handle_silence()
                self._speak(silent_reply)
                if turn >= 3:
                    print("[AWAAZ] Call ended — no speech detected.")
                    break
                continue

            # ── STEP 2: Detect language (turn 1 only) ────
            if turn == 1:
                lang, conf = self.stt.detect_language(audio_path)
                self.profile.lang       = lang
                self.profile.lang_name  = LANGUAGES.get(lang, {}).get("name", "Hindi")
                self.profile.gtts_lang  = LANGUAGES.get(lang, {}).get("gtts", "hi")
                self.profile.script     = LANGUAGES.get(lang, {}).get("script", "Devanagari")
                self.profile.confidence = conf
                self.profile.detected_at_turn = turn
                print(f"[PROFILE] Language: {self.profile.lang_name} (conf: {conf:.2f})")

            # ── STEP 3: Transcribe ────────────────────────
            text = self.stt.transcribe(audio_path, self.profile.lang)

            if not text:
                self._speak(self._handle_silence())
                continue

            print(f"[CITIZEN] {text}")

            # ── STEP 4a: Token-level language detection ───
            # Runs after every STT output — updates lang_mode + lang_distribution
            # on the profile without blocking (fastText is <50ms on CPU)
            self.langdet.update_profile(text, self.profile)

            # ── STEP 4b: Detect accent + formality (turn 1-2) ─
            if turn <= 2:
                self.profile.accent_region = self.profiler.detect_accent(
                    audio_path, self.profile.lang
                )
                self.profile.formality_score, self.profile.formality_label = \
                    self.profiler.detect_formality(text, self.profile.lang)
                print(f"[PROFILE] Accent: {self.profile.accent_region} | "
                      f"Formality: {self.profile.formality_label}")

            # ── STEP 5: Emergency check ───────────────────
            if check_emergency(text, self.profile.lang, self.model):
                self.profile.is_emergency = True
                self.profile.state = "EMERGENCY"

            # ── STEP 6: Update state machine ─────────────
            self._update_state(text)

            # ── STEP 7: Generate reply ────────────────────
            reply = self.model.generate(text, self.profile)

            # ── STEP 8: Update history ────────────────────
            self.profile.history.append({
                "citizen":   text,
                "assistant": reply,
                "turn":      turn,
            })

            # ── STEP 8b: Normalise reply for TTS ─────────
            # LLM normalisation: converts mixed-script tokens into
            # fully speakable native form before TTS sees the text.
            # Only fires when needed (mixed lang_mode or foreign script detected).
            # Reuses the same Groq/Ollama client — no extra model loaded.
            reply_for_tts = self.model.normalize_for_tts_llm(reply, self.profile)

            # ── STEP 8c: Transliteration hook (pluggable) ─
            # Passthrough by default. Enable IndicTrans2 at startup to activate.
            reply_for_tts = self.translit.process(reply_for_tts, self.profile)

            # ── STEP 9: Speak reply ───────────────────────
            print(f"[AWAAZ]   {reply_for_tts}")
            self._speak(reply_for_tts)

            # ── STEP 10: Check for call end ───────────────
            if self.profile.state in ("CLOSING", "EMERGENCY") and turn > 1:
                print("\n[AWAAZ] Call complete.")
                self._print_summary()
                break

            # File mode: single turn only
            if self.audio.mode == "file":
                print("\n[AWAAZ] File mode — single turn complete.")
                self._print_summary()
                break

        else:
            print("\n[AWAAZ] Max turns reached. Ending call.")

    def _update_state(self, text: str):
        """Simple state machine transitions based on turn and content."""
        state = self.profile.state
        turn  = self.profile.turn_number

        if state == "GREETING":
            self.profile.state = "GATHERING"

        elif state == "GATHERING":
            # Move to confirming if we have enough info (turn >= 2 and reasonable text)
            if turn >= 2 and len(text.split()) >= 5:
                self.profile.state = "CONFIRMING"

        elif state == "CONFIRMING":
            # Model-based confirmation detection (avoids brittle multilingual word lists)
            if self.model.is_affirmative(text, self.profile):
                self.profile.state = "FILING"
            else:
                self.profile.state = "GATHERING"

        elif state == "FILING":
            self.profile.state = "CLOSING"

    def _handle_silence(self) -> str:
        """Reply for silent turns."""
        lang = self.profile.lang if self.profile else "hi"
        return {
            "hi": "Hello? Kya aap mujhe sun sakte hain?",
            "ta": "Vaṇakkam? Nīṅkaḷ eṉṉai kēḷkkiṟīrkaḷā?",
            "te": "Helo? Mīru nannु vinagalugutunnārā?",
            "mr": "Hello? Tum mala aikū śakata kā?",
            "en": "Hello? Can you hear me?",
        }.get(lang, "Hello? Can you hear me?")

    def _speak(self, text: str):
        """Synthesize and play TTS reply."""
        if not self.profile:
            return
        out_path = f"/tmp/awaaz_reply_{self.profile.session_id}_{self.profile.turn_number}.wav"
        success  = self.tts.synthesize(text, self.profile, out_path)
        if success and os.path.exists(out_path):
            self.tts.play(out_path)

    def _print_summary(self):
        """Print session summary at call end."""
        p = self.profile
        print("\n" + "="*60)
        print("  CALL SUMMARY")
        print("="*60)
        print(f"  Session ID    : {p.session_id}")
        print(f"  Language      : {p.lang_name} ({p.lang})")
        print(f"  Lang mode     : {p.lang_mode}")
        dist_str = ", ".join(f"{k}:{int(v*100)}%" for k, v in p.lang_distribution.items())
        print(f"  Distribution  : {dist_str or 'n/a'}")
        print(f"  Accent        : {p.accent_region}")
        print(f"  Formality     : {p.formality_label} ({p.formality_score})")
        print(f"  Emergency     : {'YES' if p.is_emergency else 'No'}")
        print(f"  Turns         : {p.turn_number}")
        print(f"  Final state   : {p.state}")
        print("-"*60)
        for i, h in enumerate(p.history, 1):
            print(f"  Turn {i}")
            print(f"    Citizen : {h['citizen']}")
            print(f"    AWAAZ   : {h['assistant']}")
        print("="*60 + "\n")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AWAAZ — Voice Grievance Assistant (single file)"
    )
    parser.add_argument(
        "--mode",
        choices=["mic", "file", "asterisk"],
        default="mic",
        help="Input mode: mic (live), file (WAV), asterisk (AGI pipe)"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input WAV file (required for --mode file)"
    )
    args = parser.parse_args()

    if args.mode == "file" and not args.input:
        print("ERROR: --mode file requires --input path/to/audio.wav")
        sys.exit(1)

    loop = AWAAZVoiceLoop(mode=args.mode, input_file=args.input)
    loop.run()


if __name__ == "__main__":
    main()
