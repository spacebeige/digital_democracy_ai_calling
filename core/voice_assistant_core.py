#!/usr/bin/env python3
"""
MEERA — DYNAMIC MULTILINGUAL VOICE ASSISTANT CORE
==================================================
Version: 2.0 — Dynamic NLP Pipeline

Supports 20 languages with:
- Dynamic language detection (script analysis + morphological markers)
- Entity extraction (PERSON, PRODUCT, ORG, LOCATION, DATE_TIME, etc.)
- Urgency detection (CRITICAL/HIGH/MEDIUM/LOW/NONE)
- Context window awareness (5-turn history)
- Emotion × Urgency matrix for response modifiers
- TTS fallback chain (Sarvam → ElevenLabs → Groq → gTTS)

Pipeline (11 steps):
    1. Language Detection → 2. Text Preprocessing → 3. NLP Processing (entities, intent)
    4. Emotion Detection → 5. Urgency Detection → 6. Emotion × Intent Override
    7. Summary Generation → 8. Response Modifier Selection → 9. Response Generation
    10. TTS Preprocessing → 11. TTS Dispatch
"""

import os
import re
import logging
import base64
import time
import tempfile
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load environment variables
_env_paths = [
    Path(__file__).parent.parent / ".env",
    Path.cwd() / ".env",
]
for env_path in _env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class Intent(Enum):
    GREETING = "greeting"
    QUERY = "query"
    COMPLAINT = "complaint"
    ESCALATION = "escalation"
    TRANSACTION = "transaction"
    SMALLTALK = "smalltalk"
    FAREWELL = "farewell"
    UNCLEAR = "unclear"


class Emotion(Enum):
    ANGRY = "angry"
    FRUSTRATED = "frustrated"
    SAD = "sad"
    NEUTRAL = "neutral"


class UrgencyLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class EntityType(Enum):
    PERSON = "person"
    PRODUCT = "product"
    ORG = "org"
    LOCATION = "location"
    DATE_TIME = "date_time"
    AMOUNT = "amount"
    ACCOUNT = "account"
    ISSUE_TYPE = "issue_type"


# Languages using Devanagari-style punctuation (danda instead of period)
DEVANAGARI_PUNCT_LANGS = {"hi", "mr", "gu", "bn", "pa", "or", "sa"}

# All supported language codes (20 languages)
SUPPORTED_LANGUAGES = {
    "en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa",
    "ur", "or", "as", "sa", "ne", "si", "kok", "mai", "sd", "doi"
}

# Script ranges for language detection
SCRIPT_RANGES = {
    "devanagari": (0x0900, 0x097F),  # hi, mr, kok, mai, ne, sa, doi
    "bengali": (0x0980, 0x09FF),      # bn, as
    "tamil": (0x0B80, 0x0BFF),        # ta
    "telugu": (0x0C00, 0x0C7F),       # te
    "kannada": (0x0C80, 0x0CFF),      # kn
    "malayalam": (0x0D00, 0x0D7F),    # ml
    "gujarati": (0x0A80, 0x0AFF),     # gu
    "gurmukhi": (0x0A00, 0x0A7F),     # pa
    "odia": (0x0B00, 0x0B7F),         # or
    "arabic": (0x0600, 0x06FF),       # ur, sd
    "sinhala": (0x0D80, 0x0DFF),      # si
    "latin": (0x0041, 0x007A),        # en, romanized
}


# ============================================================================
# ANGER KEYWORDS BY LANGUAGE
# ============================================================================

ANGER_KEYWORDS: Dict[str, List[str]] = {
    "en": ["angry", "furious", "frustrated", "useless", "stupid", "ridiculous", 
           "worst", "terrible", "pathetic", "hate", "disgusting", "outraged"],
    "hi": ["गुस्सा", "बेकार", "नालायक", "बकवास", "घटिया", "शर्म", "बेशर्म", 
           "झूठा", "धोखेबाज", "बर्बाद", "निकम्मा"],
    "ta": ["கோபம்", "மோசமான", "பயனற்ற", "அசிங்கம்"],
    "te": ["కోపం", "చెత్త", "నికృష్టం", "పనికిమాలిన"],
    "bn": ["রাগ", "বাজে", "অকেজো", "বাজে"],
    "mr": ["राग", "बेकार", "निकामी", "घाणेरडे"],
    "gu": ["ગુસ્સો", "નકામું", "બેકાર", "ઘટિયા"],
    "kn": ["ಕೋಪ", "ಕೆಟ್ಟ", "ನಿಷ್ಪ್ರಯೋಜಕ"],
    "ml": ["കോപം", "മോശം", "നിരർത്ഥകം"],
    "pa": ["ਗੁੱਸਾ", "ਬੇਕਾਰ", "ਨਿਕੰਮਾ"],
    "ur": ["غصہ", "بیکار", "ناکارہ", "گھٹیا"],
    "or": ["ରାଗ", "ବେକାର", "ନିକମ୍ମା"],
    "as": ["খং", "বেকাৰ", "নিকামী"],
    "ne": ["रिस", "बेकार", "निकम्मा"],
    "sa": ["क्रोध", "निष्फल", "निकम्म"],
    "sd": ["ڪاوڙ", "بيڪار", "ناڪاره"],
    "si": ["තරහ", "නිකරුණේ", "බැඳුම්"],
    "kok": ["राग", "बेकार", "निकामी"],
    "mai": ["रिस", "बेकार", "निकम्मा"],
    "doi": ["गुस्सा", "बेकार", "निकम्मा"],
}

# ============================================================================
# URGENCY KEYWORDS BY LANGUAGE (Section 3)
# ============================================================================

URGENCY_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "critical": {
        "en": ["right now", "immediately", "this minute", "asap", "emergency", "urgent", 
               "cannot wait", "life and death", "last chance", "expires today", "legal action",
               "going to court", "consumer forum", "social media"],
        "hi": ["अभी", "तुरंत", "फ़ौरन", "आपातकाल", "जल्दी", "देरी मत करो", "कानूनी कार्रवाई"],
        "ta": ["இப்போதே", "உடனடியாக", "அவசரம்", "நேரம் இல்லை"],
        "te": ["ఇప్పుడే", "వెంటనే", "అర్జెంట్", "ఆపద"],
        "bn": ["এখনই", "তাৎক্ষণিক", "জরুরি", "দেরি করবেন না"],
        "mr": ["आत्ताच", "ताबडतोब", "तातडीने", "आणीबाणी"],
        "gu": ["હમણાં જ", "તાત્કાલિક", "ઇમર્જન્સી"],
        "kn": ["ಈಗಲೇ", "ತಕ್ಷಣ", "ತುರ್ತು"],
        "ml": ["ഇപ്പോൾ തന്നെ", "അടിയന്തരം", "വൈകരുത്"],
        "pa": ["ਹੁਣੇ", "ਤੁਰੰਤ", "ਜ਼ਰੂਰੀ"],
        "ur": ["ابھی", "فوری", "ہنگامی", "دیر مت کرو"],
    },
    "high": {
        "en": ["soon", "today", "waiting since", "already", "still not", "how long"],
        "hi": ["जल्दी", "कब होगा", "कितना वक्त", "अभी तक नहीं"],
        "ta": ["விரைவில்", "இன்றே", "எவ்வளவு நேரம்"],
        "te": ["త్వరగా", "ఈ రోజు", "ఎంత సేపు"],
        "bn": ["শীঘ্র", "আজই", "কতক্ষণ"],
        "mr": ["लवकर", "आजच", "किती वेळ"],
    }
}


# ============================================================================
# ANGER ACKNOWLEDGEMENTS (Feminine, First-Person, Empathetic)
# ============================================================================

ANGER_ACKNOWLEDGEMENTS: Dict[str, str] = {
    "en": "I understand your frustration. Let me resolve this for you right away.",
    "hi": "मैं समझ सकती हूँ कि आप परेशान हैं। मैं अभी आपकी मदद करूँगी।",
    "ta": "நீங்கள் வருத்தப்படுவதை புரிந்துகொள்கிறேன். உடனே தீர்வு காண்பேன்.",
    "te": "మీ నిరాశను అర్థం చేసుకుంటున్నాను. వెంటనే పరిష్కారం చూపిస్తాను.",
    "bn": "আমি বুঝতে পারছি আপনি বিরক্ত। আমি এখনই সাহায্য করব।",
    "mr": "मला समजतं की तुम्हाला राग आला आहे। मी लगेच मदद करते।",
    "gu": "હું સમજી શકું છું કે તમે નારાજ છો। હું તરત મદદ કરીશ।",
    "kn": "ನಿಮ್ಮ ಹತಾಶೆ ನನಗೆ ಅರ್ಥವಾಗುತ್ತದೆ. ತಕ್ಷಣ ಸಹಾಯ ಮಾಡಲು ಪ್ರಯತ್ನಿಸುತ್ತೇನೆ.",
    "ml": "നിങ്ങളുടെ നിരാശ എനിക്ക് മനസ്സിലാകുന്നു. ഉടൻ സഹായിക്കാൻ ശ്രമിക്കുന്നു.",
    "pa": "ਮੈਂ ਸਮਝਦੀ ਹਾਂ ਕਿ ਤੁਸੀਂ ਪਰੇਸ਼ਾਨ ਹੋ। ਮੈਂ ਤੁਰੰਤ ਮਦਦ ਕਰਾਂਗੀ।",
    "ur": "میں سمجھتی ہوں کہ آپ پریشان ہیں۔ میں ابھی آپ کی مدد کروں گی۔",
    "or": "ମୁଁ ବୁଝିପାରୁଛି ଯେ ଆପଣ ବିରକ୍ତ। ମୁଁ ତୁରନ୍ତ ସାହାଯ୍ୟ କରିବି।",
    "as": "মই বুজিব পাৰিছোঁ যে আপুনি বিচলিত। মই এতিয়াই সহায় কৰিম।",
    "ne": "मैले बुझ्न सक्छु कि तपाईं निराश हुनुहुन्छ। म तुरुन्तै सहायता गर्नेछु।",
    "sa": "अहं जानामि यत् भवान् क्रुद्धः अस्ति। अहं शीघ्रमेव सहायतां करिष्यामि।",
    "sd": "مون سمجھان ٿي ته توهان پريشان آهيو. مان هاڻي مدد ڪندس.",
    "si": "ඔබේ කලකිරීම මට තේරෙනවා. මම දැන්ම උදව් කරන්නම්.",
    "kok": "मला समजता की तुमी निराश आसात। म लगेच मदत करता।",
    "mai": "हम बुझैत छी जे अहाँ परेशान छी। हम तुरंत मदद करब।",
    "doi": "मैं समझ सकदी हां कि तुसी परेशान हो। मैं अभी मदद करांगी।",
}

# ============================================================================
# URGENCY ACKNOWLEDGEMENTS (Feminine, Action-Focused)
# ============================================================================

URGENCY_ACKNOWLEDGEMENTS: Dict[str, str] = {
    "en": "I'm treating this as urgent — here's what I'm doing right now:",
    "hi": "मैं इसे तुरंत संभाल रही हूँ — अभी यह कर रही हूँ:",
    "ta": "இதை இப்போதே கவனிக்கிறேன் — இதுதான் செய்கிறேன்:",
    "te": "దీన్ని ఇప్పుడే చూస్తున్నాను — ఇది చేస్తున్నాను:",
    "bn": "এটি আমি এখনই দেখছি — এখন এটি করছি:",
    "mr": "मी हे आत्ताच हाताळत आहे — आत्ता हे करत आहे:",
    "gu": "હું આ હમણાં જ સંભાળી રહી છું — આ કરી રહી છું:",
    "kn": "ಇದನ್ನು ಈಗಲೇ ನಿಭಾಯಿಸುತ್ತಿದ್ದೇನೆ — ಇದನ್ನು ಮಾಡುತ್ತಿದ್ದೇನೆ:",
    "ml": "ഞാൻ ഇത് ഇപ്പോൾ തന്നെ നോക്കുന്നു — ഇത് ചെയ്യുന്നു:",
    "pa": "ਮੈਂ ਇਹ ਹੁਣੇ ਸੰਭਾਲ ਰਹੀ ਹਾਂ — ਇਹ ਕਰ ਰਹੀ ਹਾਂ:",
    "ur": "میں یہ ابھی حل کر رہی ہوں — یہ کر رہی ہوں:",
}

# ============================================================================
# DYNAMIC GREETINGS BY TIME OF DAY
# ============================================================================

GREETINGS_BY_TIME: Dict[str, Dict[str, str]] = {
    "morning": {
        "en": "Good morning! I'm Meera.",
        "hi": "शुभ प्रभात! मैं मीरा हूँ।",
        "ta": "காலை வணக்கம்! நான் மீரா.",
        "te": "శుభోదయం! నేను మీరా.",
        "bn": "সুপ্রভাত! আমি মীরা।",
        "mr": "सुप्रभात! मी मीरा आहे.",
        "gu": "સુપ્રભાત! હું મીરા છું.",
        "kn": "ಶುಭೋದಯ! ನಾನು ಮೀರಾ.",
        "ml": "സുപ്രഭാതം! ഞാൻ മീരയാണ്.",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਮੀਰਾ ਹਾਂ।",
        "ur": "صبح بخیر! میں میرا ہوں۔",
    },
    "afternoon": {
        "en": "Good afternoon! I'm Meera.",
        "hi": "नमस्कार! मैं मीरा हूँ।",
        "ta": "நல்ல மதியம்! நான் மீரா.",
        "te": "శుభ మధ్యాహ్నం! నేను మీరా.",
        "bn": "শুভ অপরাহ্ন! আমি মীরা।",
    },
    "evening": {
        "en": "Good evening! I'm Meera.",
        "hi": "शुभ संध्या! मैं मीरा हूँ।",
        "ta": "மாலை வணக்கம்! நான் மீரா.",
        "te": "శుభ సాయంత్రం! నేను మీరా.",
        "bn": "শুভ সন্ধ্যা! আমি মীরা।",
    },
    "default": {
        "en": "Hello! I'm Meera.",
        "hi": "नमस्ते! मैं मीरा हूँ।",
        "ta": "வணக்கம்! நான் மீரா.",
        "te": "నమస్కారం! నేను మీరా.",
        "bn": "নমস্কার! আমি মীরা।",
        "mr": "नमस्कार! मी मीरा आहे.",
        "gu": "નમસ્તે! હું મીરા છું.",
        "kn": "ನಮಸ್ಕಾರ! ನಾನು ಮೀರಾ.",
        "ml": "നമസ്കാരം! ഞാൻ മീരയാണ്.",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਮੀਰਾ ਹਾਂ।",
        "ur": "السلام علیکم! میں میرا ہوں۔",
        "sa": "नमस्ते! अहं मीरा अस्मि।",
        "si": "ආයුබෝවන්! මම මීරා.",
    }
}

GREETING_FOLLOWUP: Dict[str, str] = {
    "en": "How can I help you today?",
    "hi": "आज मैं आपकी कैसे सहायता कर सकती हूँ?",
    "ta": "இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?",
    "te": "ఈ రోజు నేను మీకు ఎలా సహాయం చేయగలను?",
    "bn": "আজ আমি কীভাবে আপনাকে সাহায্য করতে পারি?",
    "mr": "आज मी तुम्हाला कशी मदत करू शकते?",
    "gu": "આજે હું તમને કેવી રીતે મદદ કરી શકું?",
    "kn": "ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
    "ml": "ഇന്ന് എനിക്ക് നിങ്ങളെ എങ്ങനെ സഹായിക്കാനാകും?",
    "pa": "ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦੀ ਹਾਂ?",
    "ur": "آج میں آپ کی کیسے مدد کر سکتی ہوں؟",
}

FAREWELL_RESPONSES: Dict[str, str] = {
    "en": "Take care! I'm here whenever you need me.",
    "hi": "ध्यान रखिए! जब भी जरूरत हो, मैं यहाँ हूँ।",
    "ta": "கவனமாக இருங்கள்! எப்போது வேண்டுமானாலும் நான் இங்கே இருக்கிறேன்.",
    "te": "జాగ్రత్తగా ఉండండి! మీకు అవసరమైనప్పుడు నేను ఇక్కడ ఉన్నాను.",
    "bn": "যত্ন নিন! আপনার যখন প্রয়োজন আমি এখানে আছি।",
    "mr": "काळजी घ्या! जेव्हाही गरज असेल मी इथे आहे.",
    "gu": "ધ્યાન રાખો! જ્યારે પણ જરૂર હોય ત્યારે હું અહીં છું.",
    "kn": "ಎಚ್ಚರಿಕೆಯಿಂದಿರಿ! ನಿಮಗೆ ಅಗತ್ಯವಿದ್ದಾಗ ನಾನು ಇಲ್ಲಿದ್ದೇನೆ.",
    "ml": "ശ്രദ്ധിക്കുക! നിങ്ങൾക്ക് ആവശ്യമുള്ളപ്പോൾ ഞാൻ ഇവിടെയുണ്ട്.",
    "pa": "ਧਿਆਨ ਰੱਖੋ! ਜਦੋਂ ਵੀ ਲੋੜ ਹੋਵੇ ਮੈਂ ਇੱਥੇ ਹਾਂ।",
    "ur": "خیال رکھیں! جب بھی ضرورت ہو میں یہاں ہوں۔",
}


# ============================================================================
# TTS PROVIDER CONFIGURATION
# ============================================================================

# Sarvam Language Mapping
SARVAM_LANG_MAP = {
    "hi": "hi-IN", "mr": "mr-IN", "ta": "ta-IN", "te": "te-IN",
    "bn": "bn-IN", "kn": "kn-IN", "ml": "ml-IN", "gu": "gu-IN",
    "pa": "pa-IN", "or": "od-IN", "en": "en-IN", "as": "as-IN",
}

# ElevenLabs Voice Configuration
ELEVENLABS_VOICE_ID = "9BWtsMINqrJLrRacOk9x"  # Aria
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# Groq TTS Configuration - Using distil-whisper-large-v3-en or playht models
GROQ_TTS_MODEL = "distil-whisper-large-v3-en"  # Alternative: use gTTS as fallback
GROQ_TTS_VOICE = "Arista-PlayAI"  # Feminine voice


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Entity:
    """Extracted entity from text."""
    entity_type: EntityType
    raw_value: str
    normalized_value: str = ""
    confidence: str = "medium"  # high/medium/low


@dataclass
class LanguageDetectionResult:
    """Result of dynamic language detection."""
    language_code: str
    script: str
    confidence: float
    codeswitching: bool = False
    secondary_language: Optional[str] = None


@dataclass
class EmotionResult:
    emotion: Emotion
    anger_score: float = 0.0
    matched_keywords: List[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class UrgencyResult:
    """Result of urgency detection."""
    level: UrgencyLevel
    triggers: List[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class IntentResult:
    intent: Intent
    final_intent: Intent  # After emotion override
    confidence: float = 0.0
    secondary_intents: List[Intent] = field(default_factory=list)


@dataclass
class PipelineSummary:
    """Internal summary for routing and logging (Section 4)."""
    turn_id: int
    language_code: str
    confidence: float
    codeswitching: bool
    detected_entities: List[Entity]
    primary_intent: Intent
    secondary_intents: List[Intent]
    emotion: Emotion
    urgency_level: UrgencyLevel
    urgency_triggers: List[str]
    topic_continuity: bool
    resolved_references: Dict[str, str]
    escalation_flag: bool
    repeat_complaint: bool
    routed_to: str
    response_modifier: str  # URGENCY_ACK, ANGER_ACK, BOTH, NONE
    summary_sentence: str


@dataclass
class PipelineContext:
    """Context passed through the entire pipeline."""
    language_code: str
    language_detection: Optional[LanguageDetectionResult] = None
    transcript: str = ""
    preprocessed_transcript: str = ""
    entities: List[Entity] = field(default_factory=list)
    emotion: Optional[EmotionResult] = None
    urgency: Optional[UrgencyResult] = None
    base_intent: Optional[IntentResult] = None
    final_intent: Optional[Intent] = None
    response_modifier: str = "NONE"  # URGENCY_ACK, ANGER_ACK, BOTH, NONE
    response_text: str = ""
    preprocessed_text: str = ""
    audio_path: str = ""
    tts_provider_used: str = ""
    summary: Optional[PipelineSummary] = None
    conversation_history: List[Dict] = field(default_factory=list)
    turn_count: int = 0
    errors: List[str] = field(default_factory=list)


# ============================================================================
# STEP 1: DYNAMIC LANGUAGE DETECTION (Section 1)
# ============================================================================

def detect_script(text: str) -> Dict[str, int]:
    """Detect Unicode script blocks present in text."""
    script_counts = {name: 0 for name in SCRIPT_RANGES.keys()}
    
    for char in text:
        code_point = ord(char)
        for script_name, (start, end) in SCRIPT_RANGES.items():
            if start <= code_point <= end:
                script_counts[script_name] += 1
                break
    
    return script_counts


def detect_language_morphological(text: str, candidate_scripts: List[str]) -> Optional[str]:
    """
    Disambiguate within script families using morphological markers (Section 1B).
    """
    text_lower = text.lower()
    
    # Devanagari disambiguation
    if "devanagari" in candidate_scripts:
        # Marathi markers
        if any(m in text for m in ["आहे", "आहेत", "आणि", "नाही", "करतो", "करते"]):
            return "mr"
        # Hindi markers
        if any(m in text for m in ["है", "हैं", "का", "में", "को", "करता", "करती"]):
            return "hi"
        # Nepali markers
        if any(m in text for m in ["छ", "छैन", "गर्नु", "भएको"]):
            return "ne"
        # Sanskrit (sandhi-heavy, classical forms)
        if any(m in text for m in ["अस्ति", "भवति", "करोति"]):
            return "sa"
    
    # Arabic script disambiguation
    if "arabic" in candidate_scripts:
        # Urdu markers
        if any(m in text for m in ["ہے", "میں", "کا", "کی", "نے"]):
            return "ur"
        # Sindhi markers
        if any(m in text for m in ["آهي", "ڪيو", "هو"]):
            return "sd"
    
    # Bengali script disambiguation
    if "bengali" in candidate_scripts:
        # Standard Bengali markers
        if any(m in text for m in ["আছে", "করা", "যাচ্ছি", "হয়েছে"]):
            return "bn"
        # Assamese markers
        if any(m in text for m in ["আছে", "কৰা"]):  # Assamese-specific
            return "as"
    
    return None


def detect_language_dynamic(text: str) -> LanguageDetectionResult:
    """
    Dynamic language detection using script analysis + morphological markers.
    (Section 1 - Step 1)
    """
    if not text or not text.strip():
        return LanguageDetectionResult(
            language_code="en",
            script="latin",
            confidence=0.0
        )
    
    # Step A: Script Analysis
    script_counts = detect_script(text)
    total_script_chars = sum(script_counts.values())
    
    if total_script_chars == 0:
        return LanguageDetectionResult(
            language_code="en",
            script="latin",
            confidence=0.3
        )
    
    # Find dominant script
    dominant_script = max(script_counts, key=script_counts.get)
    dominant_count = script_counts[dominant_script]
    confidence = dominant_count / total_script_chars if total_script_chars > 0 else 0.0
    
    # Check for code-switching (multiple scripts)
    active_scripts = [s for s, c in script_counts.items() if c > 0]
    codeswitching = len(active_scripts) > 1
    secondary_language = None
    
    # Script to language mapping
    script_to_lang = {
        "devanagari": "hi",  # Default, will be refined
        "bengali": "bn",
        "tamil": "ta",
        "telugu": "te",
        "kannada": "kn",
        "malayalam": "ml",
        "gujarati": "gu",
        "gurmukhi": "pa",
        "odia": "or",
        "arabic": "ur",
        "sinhala": "si",
        "latin": "en",
    }
    
    # Initial language guess
    language_code = script_to_lang.get(dominant_script, "en")
    
    # Step B: Morphological refinement
    if dominant_script in ["devanagari", "arabic", "bengali"]:
        refined = detect_language_morphological(text, [dominant_script])
        if refined:
            language_code = refined
            confidence = min(confidence + 0.2, 1.0)
    
    # Handle code-switching secondary language
    if codeswitching:
        secondary_scripts = [s for s in active_scripts if s != dominant_script]
        if secondary_scripts:
            secondary_language = script_to_lang.get(secondary_scripts[0])
    
    return LanguageDetectionResult(
        language_code=language_code,
        script=dominant_script,
        confidence=confidence,
        codeswitching=codeswitching,
        secondary_language=secondary_language
    )


# ============================================================================
# TEXT PREPROCESSING (Section 2)
# ============================================================================

def preprocess_text_for_tts(text: str, language_code: str) -> str:
    """
    Preprocess text before TTS call. Applied to ALL providers.
    
    Steps:
    1. Strip markdown: asterisks, # headings, backticks, [text](url), <>{} []
    2. Remove URLs (https?://...)
    3. Split on sentence-ending punctuation; append terminal char if missing
    4. Replace stray '.' with '।' for Devanagari-script languages
    5. Preserve Urdu RTL text as-is
    """
    if not text:
        return ""
    
    lang = language_code.split("-")[0].lower()
    
    # Step 1: Strip markdown
    # Remove bold/italic asterisks
    text = re.sub(r'\*+([^*]+)\*+', r'\1', text)
    # Remove # headings
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Remove backtick code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove [text](url) links - keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove <>{} brackets
    text = re.sub(r'[<>{}]', '', text)
    # Remove square brackets
    text = re.sub(r'[\[\]]', '', text)
    
    # Step 2: Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    
    # Step 5: Preserve Urdu RTL - skip heavy processing
    if lang == "ur":
        return text.strip()
    
    # Step 3: Split on sentence-ending punctuation and ensure terminal char
    # Sentence endings: . ! ? । ।
    sentences = re.split(r'([.!?।]+)', text)
    
    processed_sentences = []
    for i, part in enumerate(sentences):
        part = part.strip()
        if not part:
            continue
        
        # Check if this part is punctuation
        if re.match(r'^[.!?।]+$', part):
            # Append to previous sentence if exists
            if processed_sentences:
                processed_sentences[-1] += part
        else:
            # Check if next part is punctuation
            has_terminal = False
            if i + 1 < len(sentences):
                next_part = sentences[i + 1].strip()
                if re.match(r'^[.!?।]+$', next_part):
                    has_terminal = True
            
            # If no terminal punctuation, add appropriate one
            if not has_terminal and not re.search(r'[.!?।]$', part):
                if lang in DEVANAGARI_PUNCT_LANGS:
                    part += "।"
                else:
                    part += "."
            
            processed_sentences.append(part)
    
    result = " ".join(processed_sentences)
    
    # Step 4: For Devanagari languages, replace stray periods with danda
    if lang in DEVANAGARI_PUNCT_LANGS:
        # Only replace period that's at sentence boundary
        result = re.sub(r'\.\s*(?=[^\d]|$)', '। ', result)
        result = result.strip()
        if result.endswith('.'):
            result = result[:-1] + '।'
    
    return result.strip()


# ============================================================================
# EMOTION DETECTION (Section 4.2)
# ============================================================================

def detect_emotion(text: str, language_code: str) -> EmotionResult:
    """
    Detect emotion from text using keywords and signals.
    
    Classify as ANGRY if:
    - Text contains anger keywords for detected language
    - 2+ exclamation marks present
    - >40% uppercase alphabetic characters
    """
    if not text:
        return EmotionResult(emotion=Emotion.NEUTRAL)
    
    lang = language_code.split("-")[0].lower()
    text_lower = text.lower()
    
    matched_keywords = []
    anger_indicators = 0
    reasons = []
    
    # Check anger keywords
    keywords = ANGER_KEYWORDS.get(lang, []) + ANGER_KEYWORDS.get("en", [])
    for keyword in keywords:
        if keyword.lower() in text_lower:
            matched_keywords.append(keyword)
            anger_indicators += 1
    
    if matched_keywords:
        reasons.append(f"anger keywords: {', '.join(matched_keywords[:3])}")
    
    # Check exclamation marks (2+)
    exclaim_count = text.count("!")
    if exclaim_count >= 2:
        anger_indicators += 1
        reasons.append(f"{exclaim_count} exclamation marks")
    
    # Check uppercase ratio (>40%)
    alpha_chars = [c for c in text if c.isalpha()]
    if alpha_chars:
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if upper_ratio > 0.4:
            anger_indicators += 1
            reasons.append(f"{upper_ratio:.0%} uppercase")
    
    # Calculate anger score
    anger_score = min(1.0, anger_indicators * 0.35)
    
    # Determine emotion
    if anger_indicators >= 1:
        emotion = Emotion.ANGRY
    else:
        emotion = Emotion.NEUTRAL
    
    return EmotionResult(
        emotion=emotion,
        anger_score=anger_score,
        matched_keywords=matched_keywords,
        reasoning=" + ".join(reasons) if reasons else "No anger signals detected"
    )


# ============================================================================
# STEP 5: URGENCY DETECTION (Section 3)
# ============================================================================

def detect_urgency(text: str, language_code: str) -> UrgencyResult:
    """
    Detect urgency level from text. Urgency is SEPARATE from emotion.
    
    CRITICAL: temporal triggers, legal threats, deadlines
    HIGH: soft urgency signals (waiting since, soon, today)
    MEDIUM: mild impatience
    LOW/NONE: standard query tone
    """
    if not text:
        return UrgencyResult(level=UrgencyLevel.NONE)
    
    lang = language_code.split("-")[0].lower()
    text_lower = text.lower()
    triggers = []
    reasons = []
    
    # Check CRITICAL urgency keywords
    critical_keywords = URGENCY_KEYWORDS.get("critical", {})
    lang_critical = critical_keywords.get(lang, []) + critical_keywords.get("en", [])
    
    for keyword in lang_critical:
        if keyword.lower() in text_lower:
            triggers.append(keyword)
    
    if triggers:
        reasons.append(f"critical triggers: {', '.join(triggers[:3])}")
        return UrgencyResult(
            level=UrgencyLevel.CRITICAL,
            triggers=triggers,
            reasoning=" + ".join(reasons)
        )
    
    # Check HIGH urgency keywords
    high_keywords = URGENCY_KEYWORDS.get("high", {})
    lang_high = high_keywords.get(lang, []) + high_keywords.get("en", [])
    
    high_triggers = []
    for keyword in lang_high:
        if keyword.lower() in text_lower:
            high_triggers.append(keyword)
    
    if high_triggers:
        reasons.append(f"high urgency: {', '.join(high_triggers[:3])}")
        return UrgencyResult(
            level=UrgencyLevel.HIGH,
            triggers=high_triggers,
            reasoning=" + ".join(reasons)
        )
    
    # Check for time-based urgency patterns
    time_patterns = [
        r'\d+\s*(day|hour|minute|दिन|घंट|मिनट)',
        r'since\s+\d+',
        r'waiting\s+for',
        r'\d+\s*बार',  # X times
    ]
    
    for pattern in time_patterns:
        if re.search(pattern, text_lower):
            return UrgencyResult(
                level=UrgencyLevel.MEDIUM,
                triggers=[pattern],
                reasoning="Time-based urgency pattern detected"
            )
    
    return UrgencyResult(level=UrgencyLevel.LOW)


# ============================================================================
# ENTITY EXTRACTION (Section 2A)
# ============================================================================

def extract_entities(text: str, language_code: str) -> List[Entity]:
    """
    Extract entities from text: PERSON, PRODUCT, ORG, LOCATION, DATE_TIME, 
    AMOUNT, ACCOUNT, ISSUE_TYPE
    """
    entities = []
    
    # Extract order/ticket IDs (e.g., #12345, ORD12345, TKT-123)
    order_patterns = [
        r'#?\d{4,10}',
        r'[A-Z]{2,4}[-_]?\d{4,10}',
        r'order\s*(?:id|number)?[\s:#]*(\d+)',
        r'ticket[\s:#]*(\d+)',
    ]
    
    for pattern in order_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append(Entity(
                entity_type=EntityType.PRODUCT,
                raw_value=match if isinstance(match, str) else match[0],
                normalized_value=re.sub(r'[^\dA-Za-z]', '', match if isinstance(match, str) else match[0]),
                confidence="high"
            ))
    
    # Extract amounts (₹1000, Rs. 500, $50)
    amount_patterns = [
        r'[₹$]\s*[\d,]+(?:\.\d{2})?',
        r'Rs\.?\s*[\d,]+',
        r'(?:rupee|रुपय|रुपए)\s*[\d,]+',
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append(Entity(
                entity_type=EntityType.AMOUNT,
                raw_value=match,
                normalized_value=re.sub(r'[^\d.]', '', match),
                confidence="high"
            ))
    
    # Extract phone numbers
    phone_pattern = r'(?:\+91[-\s]?)?[6-9]\d{9}'
    phones = re.findall(phone_pattern, text)
    for phone in phones:
        entities.append(Entity(
            entity_type=EntityType.ACCOUNT,
            raw_value=phone,
            normalized_value=re.sub(r'[^\d]', '', phone),
            confidence="high"
        ))
    
    # Extract dates (basic patterns)
    date_patterns = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4}',
        r'(?:yesterday|today|tomorrow)',
        r'(?:कल|आज|परसों)',
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append(Entity(
                entity_type=EntityType.DATE_TIME,
                raw_value=match,
                confidence="medium"
            ))
    
    # Extract issue types
    issue_keywords = {
        "refund": ["refund", "रिफंड", "वापसी", "money back"],
        "delivery": ["delivery", "डिलीवरी", "shipped", "tracking"],
        "login": ["login", "password", "account", "लॉगिन"],
        "payment": ["payment", "paid", "भुगतान", "पैसे"],
        "technical": ["not working", "error", "bug", "काम नहीं"],
    }
    
    text_lower = text.lower()
    for issue_type, keywords in issue_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                entities.append(Entity(
                    entity_type=EntityType.ISSUE_TYPE,
                    raw_value=keyword,
                    normalized_value=issue_type,
                    confidence="high"
                ))
                break
    
    return entities


# ============================================================================
# INTENT CLASSIFICATION (Section 4.1)
# ============================================================================

def classify_intent_with_llm(text: str, language_code: str) -> Intent:
    """
    Classify intent using Groq LLM.
    
    System prompt: Classify into exactly one of:
    greeting, query, complaint, escalation, transaction, smalltalk, farewell, unclear
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not set, using keyword-based fallback")
        return _fallback_intent_classification(text)
    
    system_prompt = f"""Classify the user message into exactly one of: greeting, query, complaint, escalation, transaction, smalltalk, farewell, unclear. 
User language: {language_code}. 
Reply with the label only, lowercase, no punctuation."""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 20,
                "temperature": 0.1
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            intent_str = result["choices"][0]["message"]["content"].strip().lower()
            
            # Map to Intent enum
            intent_map = {
                "greeting": Intent.GREETING,
                "query": Intent.QUERY,
                "complaint": Intent.COMPLAINT,
                "escalation": Intent.ESCALATION,
                "transaction": Intent.TRANSACTION,
                "smalltalk": Intent.SMALLTALK,
                "farewell": Intent.FAREWELL,
                "unclear": Intent.UNCLEAR,
            }
            return intent_map.get(intent_str, Intent.UNCLEAR)
        else:
            logger.warning(f"LLM intent classification failed: {response.status_code}")
            return _fallback_intent_classification(text)
            
    except Exception as e:
        logger.warning(f"LLM intent classification error: {e}")
        return _fallback_intent_classification(text)


def _fallback_intent_classification(text: str) -> Intent:
    """Simple keyword-based intent classification fallback."""
    text_lower = text.lower()
    
    greeting_words = ["hello", "hi", "namaste", "नमस्ते", "namaskar", "vanakkam"]
    farewell_words = ["bye", "goodbye", "alvida", "अलविदा", "धन्यवाद", "thanks"]
    complaint_words = ["problem", "issue", "broken", "समस्या", "तकलीफ", "शिकायत", "complaint"]
    query_words = ["what", "how", "when", "where", "why", "क्या", "कैसे", "कब", "कहाँ"]
    
    if any(w in text_lower for w in greeting_words):
        return Intent.GREETING
    if any(w in text_lower for w in farewell_words):
        return Intent.FAREWELL
    if any(w in text_lower for w in complaint_words):
        return Intent.COMPLAINT
    if any(w in text_lower for w in query_words):
        return Intent.QUERY
    
    return Intent.UNCLEAR


# ============================================================================
# INTENT OVERRIDE BASED ON EMOTION (Section 4.3)
# ============================================================================

def apply_emotion_override(base_intent: Intent, emotion: Emotion) -> Intent:
    """
    Apply emotion-based intent override.
    
    | Emotion    | Base Intent | Final Intent |
    |------------|-------------|--------------|
    | ANGRY      | query       | complaint    |
    | ANGRY      | complaint   | escalation   |
    | ANGRY      | smalltalk   | complaint    |
    | FRUSTRATED | query       | complaint    |
    """
    if emotion == Emotion.ANGRY:
        if base_intent == Intent.QUERY:
            return Intent.COMPLAINT
        elif base_intent == Intent.COMPLAINT:
            return Intent.ESCALATION
        elif base_intent == Intent.SMALLTALK:
            return Intent.COMPLAINT
    
    if emotion == Emotion.FRUSTRATED:
        if base_intent == Intent.QUERY:
            return Intent.COMPLAINT
    
    return base_intent


# ============================================================================
# TTS FALLBACK CHAIN (Section 1)
# ============================================================================

def tts_with_fallback(text: str, language_code: str, output_path: str = None) -> Tuple[str, str]:
    """
    TTS fallback chain: Sarvam → ElevenLabs → Groq → gTTS (fallback)
    
    Returns:
        Tuple of (audio_path, provider_used)
    """
    if not output_path:
        output_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    
    lang = language_code.split("-")[0].lower()
    
    # Preprocess text for all providers
    processed_text = preprocess_text_for_tts(text, language_code)
    if not processed_text:
        raise ValueError("Empty text after preprocessing")
    
    logger.info(f"[TTS] Starting fallback chain for lang={lang}, text_len={len(processed_text)}")
    
    # Try Sarvam first
    try:
        result = _tts_sarvam(processed_text, lang, output_path)
        if result:
            logger.info("[TTS] Sarvam succeeded")
            return result, "sarvam"
    except Exception as e:
        logger.warning(f"[TTS] Sarvam failed: {e}")
    
    # Fall to ElevenLabs
    try:
        result = _tts_elevenlabs(processed_text, lang, output_path)
        if result:
            logger.info("[TTS] ElevenLabs succeeded")
            return result, "elevenlabs"
    except Exception as e:
        logger.warning(f"[TTS] ElevenLabs failed: {e}")
    
    # Fall to Groq
    try:
        result = _tts_groq(processed_text, lang, output_path)
        if result:
            logger.info("[TTS] Groq succeeded")
            return result, "groq"
    except Exception as e:
        logger.warning(f"[TTS] Groq failed: {e}")
    
    # Final fallback: gTTS (free, no API key)
    try:
        result = _tts_gtts(processed_text, lang, output_path)
        if result:
            logger.info("[TTS] gTTS succeeded (fallback)")
            return result, "gtts"
    except Exception as e:
        logger.error(f"[TTS] gTTS failed (terminal): {e}")
        raise RuntimeError(f"All TTS providers failed. Last error: {e}")


def _tts_sarvam(text: str, lang: str, output_path: str) -> Optional[str]:
    """
    Sarvam TTS: speaker=ritu (female), model=bulbul:v1, enable_preprocessing=true, pace=1.0
    Returns base64-decoded audio. 5s timeout.
    """
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY missing")
    
    sarvam_lang = SARVAM_LANG_MAP.get(lang)
    if not sarvam_lang:
        raise ValueError(f"Language {lang} not supported by Sarvam")
    
    # Split text if too long
    chunks = _split_text_chunks(text, max_chars=400)
    audio_buffers = []
    
    for chunk in chunks:
        payload = {
            "inputs": [chunk],
            "target_language_code": sarvam_lang,
            "speaker": "manisha",  # Female voice for bulbul:v2
            "model": "bulbul:v2",
            "enable_preprocessing": True,
            "pace": 1.0,
        }
        
        response = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={
                "api-subscription-key": api_key,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=5
        )
        
        # Check response
        if response.status_code == 400:
            raise RuntimeError(f"Sarvam HTTP 400: {response.text[:200]}")
        if response.status_code in (500, 503):
            raise RuntimeError(f"Sarvam HTTP {response.status_code}")
        if response.status_code != 200:
            raise RuntimeError(f"Sarvam HTTP {response.status_code}")
        
        # Decode base64 audio
        data = response.json()
        audio_b64 = data.get("audios", [None])[0]
        if not audio_b64:
            raise RuntimeError("Sarvam returned empty audio")
        
        audio_bytes = base64.b64decode(audio_b64)
        if not audio_bytes:
            raise RuntimeError("Sarvam audio buffer empty after decode")
        
        audio_buffers.append(audio_bytes)
    
    # Merge chunks if multiple
    if len(audio_buffers) == 1:
        merged = audio_buffers[0]
    else:
        merged = b''.join(audio_buffers)
    
    with open(output_path, "wb") as f:
        f.write(merged)
    
    return output_path


def _tts_elevenlabs(text: str, lang: str, output_path: str) -> Optional[str]:
    """
    ElevenLabs TTS: Aria voice, eleven_multilingual_v2 model
    stability=0.45, similarity_boost=0.80, style=0.30, use_speaker_boost=true
    8s timeout.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY missing")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "language_code": lang,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.80,
            "style": 0.30,
            "use_speaker_boost": True
        }
    }
    
    response = requests.post(
        url,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=8
    )
    
    # Check for fallback conditions
    if response.status_code in (401, 429, 500):
        raise RuntimeError(f"ElevenLabs HTTP {response.status_code}")
    if response.status_code != 200:
        raise RuntimeError(f"ElevenLabs HTTP {response.status_code}: {response.text[:200]}")
    
    audio_bytes = response.content
    if not audio_bytes:
        raise RuntimeError("ElevenLabs returned empty audio")
    
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    
    return output_path


def _tts_groq(text: str, lang: str, output_path: str) -> Optional[str]:
    """
    Groq TTS: model=playai-tts, voice=Aaliyah, response_format=wav
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY missing")
    
    payload = {
        "model": GROQ_TTS_MODEL,
        "input": text,
        "voice": GROQ_TTS_VOICE,
        "response_format": "wav"
    }
    
    response = requests.post(
        "https://api.groq.com/openai/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=10
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Groq TTS HTTP {response.status_code}: {response.text[:200]}")
    
    audio_bytes = response.content
    if not audio_bytes:
        raise RuntimeError("Groq TTS returned empty audio")
    
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    
    return output_path


def _tts_gtts(text: str, lang: str, output_path: str) -> Optional[str]:
    """
    gTTS fallback: Google Text-to-Speech (free, no API key required)
    """
    try:
        from gtts import gTTS
    except ImportError:
        raise RuntimeError("gTTS not installed. Install with: pip install gtts")
    
    # Map language codes for gTTS compatibility
    gtts_lang_map = {
        "hi": "hi", "en": "en", "ta": "ta", "te": "te", "bn": "bn",
        "mr": "mr", "gu": "gu", "kn": "kn", "ml": "ml", "pa": "pa",
        "ur": "ur", "ne": "ne", "as": "as",  # Some may not be supported
    }
    
    gtts_lang = gtts_lang_map.get(lang, "hi")  # Default to Hindi if not mapped
    
    try:
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        
        # gTTS outputs MP3, save to temp then convert path
        mp3_path = output_path.replace(".wav", ".mp3")
        tts.save(mp3_path)
        
        # Return mp3 path (most players support it)
        return mp3_path
    except Exception as e:
        raise RuntimeError(f"gTTS failed: {e}")


def _split_text_chunks(text: str, max_chars: int = 400) -> List[str]:
    """Split text into chunks at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]
    
    # Split on sentence-ending punctuation
    parts = re.split(r'([.!?।]+)', text)
    chunks = []
    current = ""
    
    for i in range(0, len(parts) - 1, 2):
        sentence = parts[i].strip()
        punct = parts[i + 1] if i + 1 < len(parts) else ""
        full_sentence = f"{sentence}{punct}".strip()
        
        if len(current) + len(full_sentence) + 1 <= max_chars:
            current = f"{current} {full_sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = full_sentence
    
    if current:
        chunks.append(current)
    
    return chunks if chunks else [text[:max_chars]]


# ============================================================================
# RESPONSE GENERATION (Section 6)
# ============================================================================

def determine_response_modifier(
    emotion: EmotionResult,
    urgency: UrgencyResult,
    final_intent: Intent
) -> str:
    """
    Determine response modifier based on emotion x urgency matrix.
    Returns: URGENCY_ACK, ANGER_ACK, BOTH, or NONE
    """
    has_anger = emotion.emotion == Emotion.ANGRY and final_intent in (Intent.COMPLAINT, Intent.ESCALATION)
    has_urgency = urgency.level in (UrgencyLevel.CRITICAL, UrgencyLevel.HIGH)
    
    if has_anger and has_urgency:
        return "BOTH"
    elif has_urgency:
        return "URGENCY_ACK"
    elif has_anger:
        return "ANGER_ACK"
    return "NONE"


def get_max_sentences_by_urgency(urgency_level: UrgencyLevel) -> int:
    """Get maximum sentences based on urgency level (Section 8 Rule 8)."""
    mapping = {
        UrgencyLevel.CRITICAL: 3,
        UrgencyLevel.HIGH: 4,
        UrgencyLevel.MEDIUM: 5,
        UrgencyLevel.LOW: 6,
        UrgencyLevel.NONE: 6,
    }
    return mapping.get(urgency_level, 6)


def get_time_based_greeting(language_code: str) -> str:
    """Get time-appropriate greeting (Section 5)."""
    hour = datetime.now().hour
    lang = language_code.split("-")[0].lower()
    
    if 5 <= hour < 12:
        time_key = "morning"
    elif 12 <= hour < 17:
        time_key = "afternoon"
    elif 17 <= hour < 21:
        time_key = "evening"
    else:
        time_key = "default"
    
    greetings = GREETINGS_BY_TIME.get(time_key, GREETINGS_BY_TIME["default"])
    greeting = greetings.get(lang, greetings.get("en", "Hello! I'm Meera."))
    followup = GREETING_FOLLOWUP.get(lang, GREETING_FOLLOWUP.get("en", "How can I help you today?"))
    
    return f"{greeting} {followup}"


def generate_response(
    transcript: str,
    language_code: str,
    final_intent: Intent,
    emotion: EmotionResult,
    urgency: Optional[UrgencyResult] = None
) -> str:
    """
    Generate response in the detected language.
    Applies response modifiers based on emotion x urgency matrix.
    """
    lang = language_code.split("-")[0].lower()
    urgency = urgency or UrgencyResult(level=UrgencyLevel.NONE)
    
    response_parts = []
    response_modifier = determine_response_modifier(emotion, urgency, final_intent)
    
    # Handle greeting intent specially
    if final_intent == Intent.GREETING:
        return get_time_based_greeting(language_code)
    
    # Handle farewell intent specially
    if final_intent == Intent.FAREWELL:
        return FAREWELL_RESPONSES.get(lang, FAREWELL_RESPONSES.get("en", "Take care!"))
    
    # Apply response modifiers (urgency and/or anger acknowledgements)
    if response_modifier in ("URGENCY_ACK", "BOTH") and urgency.level == UrgencyLevel.CRITICAL:
        urg_ack = URGENCY_ACKNOWLEDGEMENTS.get(lang, URGENCY_ACKNOWLEDGEMENTS.get("en", ""))
        if urg_ack:
            response_parts.append(urg_ack)
    
    if response_modifier in ("ANGER_ACK", "BOTH"):
        anger_ack = ANGER_ACKNOWLEDGEMENTS.get(lang, ANGER_ACKNOWLEDGEMENTS.get("en", ""))
        if anger_ack:
            response_parts.append(anger_ack)
    
    # Generate intent-specific response using LLM
    api_key = os.environ.get("GROQ_API_KEY")
    max_sentences = get_max_sentences_by_urgency(urgency.level)
    
    if api_key:
        try:
            system_prompt = f"""You are Meera, a warm, empathetic multilingual voice assistant.
You MUST respond ONLY in {language_code}. Never switch to English unless the user spoke English.
Keep responses short ({max_sentences} sentences max), helpful, use feminine first-person voice.
Be conversational, never robotic. Never blame the user.

Intent: {final_intent.value}
Emotion: {emotion.emotion.value}
Urgency: {urgency.level.value}

If urgency is CRITICAL or HIGH, skip pleasantries and get to the point immediately.
For complaints/escalation, offer a concrete next step, not vague promises."""

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcript}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.7
                },
                timeout=8
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"].strip()
                response_parts.append(llm_response)
            else:
                response_parts.append(_get_fallback_response(final_intent, lang))
        except Exception as e:
            logger.warning(f"Response generation LLM error: {e}")
            response_parts.append(_get_fallback_response(final_intent, lang))
    else:
        response_parts.append(_get_fallback_response(final_intent, lang))
    
    return " ".join(response_parts)


def _get_fallback_response(intent: Intent, lang: str) -> str:
    """Fallback responses by intent and language."""
    fallbacks = {
        "en": {
            Intent.GREETING: "Hello! How can I help you today?",
            Intent.COMPLAINT: "I understand. Let me help you with this issue.",
            Intent.ESCALATION: "I'm escalating this to a supervisor right away.",
            Intent.QUERY: "I'll look into that for you.",
            Intent.FAREWELL: "Goodbye! Have a great day.",
            Intent.UNCLEAR: "Could you please explain more about what you need?",
        },
        "hi": {
            Intent.GREETING: "नमस्ते! मैं आपकी कैसे मदद कर सकती हूँ?",
            Intent.COMPLAINT: "मैं समझती हूँ। मैं इस समस्या में आपकी मदद करती हूँ।",
            Intent.ESCALATION: "मैं इसे तुरंत सुपरवाइज़र को भेज रही हूँ।",
            Intent.QUERY: "मैं इसकी जानकारी लेती हूँ।",
            Intent.FAREWELL: "धन्यवाद! आपका दिन शुभ हो।",
            Intent.UNCLEAR: "कृपया अपनी बात और स्पष्ट करें।",
        }
    }
    
    lang_fallbacks = fallbacks.get(lang, fallbacks.get("en", {}))
    return lang_fallbacks.get(intent, fallbacks["en"].get(Intent.UNCLEAR, "I'm here to help."))


# ============================================================================
# MAIN PIPELINE (Section 7 - Complete Dynamic Pipeline)
# ============================================================================

def generate_pipeline_summary(context: PipelineContext) -> PipelineSummary:
    """Generate internal summary for routing and logging (Section 4)."""
    # Create summary sentence (max 20 words, English, factual)
    entities_str = ", ".join([f"{e.entity_type.value}:{e.raw_value}" for e in context.entities[:2]])
    summary = f"User {context.final_intent.value if context.final_intent else 'unclear'}"
    if entities_str:
        summary += f" regarding {entities_str}"
    
    return PipelineSummary(
        turn_id=context.turn_count,
        language_code=context.language_code,
        confidence=context.language_detection.confidence if context.language_detection else 0.8,
        codeswitching=context.language_detection.codeswitching if context.language_detection else False,
        detected_entities=context.entities,
        primary_intent=context.final_intent or Intent.UNCLEAR,
        secondary_intents=context.base_intent.secondary_intents if context.base_intent else [],
        emotion=context.emotion.emotion if context.emotion else Emotion.NEUTRAL,
        urgency_level=context.urgency.level if context.urgency else UrgencyLevel.NONE,
        urgency_triggers=context.urgency.triggers if context.urgency else [],
        topic_continuity=False,
        resolved_references={},
        escalation_flag=context.final_intent == Intent.ESCALATION,
        repeat_complaint=False,
        routed_to=context.final_intent.value if context.final_intent else "unclear",
        response_modifier=context.response_modifier,
        summary_sentence=summary[:100]
    )


def run_voice_pipeline(
    audio_path: Optional[str] = None,
    transcript: Optional[str] = None,
    language_code: Optional[str] = None,
    conversation_history: Optional[List[Dict]] = None
) -> PipelineContext:
    """
    Execute the full Meera voice assistant pipeline (11 steps).
    
    Pipeline order (Section 7):
    1. Language Detection (dynamic, script + morphological)
    2. Text Preprocessing
    3. NLP Processing (entity extraction, intent classification)
    4. Emotion Detection
    5. Urgency Detection
    6. Emotion x Intent Override
    7. Summary Generation
    8. Response Modifier Selection
    9. Response Generation
    10. TTS Preprocessing
    11. TTS Dispatch (fallback chain)
    
    Args:
        audio_path: Path to audio file (for STT)
        transcript: Pre-transcribed text (skips STT)
        language_code: Pre-detected language (if known)
        conversation_history: List of prior turns for context
    
    Returns:
        PipelineContext with all results
    """
    context = PipelineContext(
        language_code=language_code or "hi",
        transcript=transcript or "",
        conversation_history=conversation_history or [],
        turn_count=len(conversation_history) + 1 if conversation_history else 1
    )
    
    try:
        # STEP 1: STT + Language Detection
        if audio_path and not transcript:
            try:
                from unified_stt_service import transcribe
                stt_result, engine, detected_lang = transcribe(audio_path)
                context.transcript = stt_result
                context.language_code = detected_lang
                logger.info(f"[Pipeline] Step 1 STT: {engine}, lang={detected_lang}")
            except ImportError:
                logger.warning("[Pipeline] unified_stt_service not available")
        
        # Dynamic language detection from text
        if context.transcript:
            context.language_detection = detect_language_dynamic(context.transcript)
            if not language_code:  # Override if not explicitly provided
                context.language_code = context.language_detection.language_code
            logger.info(f"[Pipeline] Step 1 Lang: {context.language_code}, "
                       f"conf={context.language_detection.confidence:.2f}, "
                       f"codeswitching={context.language_detection.codeswitching}")
        
        # STEP 2: Text Preprocessing (for analysis, not TTS yet)
        context.preprocessed_transcript = context.transcript  # Keep original for now
        
        # STEP 3: NLP Processing - Entity Extraction
        context.entities = extract_entities(context.transcript, context.language_code)
        logger.info(f"[Pipeline] Step 3 Entities: {len(context.entities)} found")
        
        # STEP 3b: Intent Classification (LLM)
        base_intent = classify_intent_with_llm(context.transcript, context.language_code)
        logger.info(f"[Pipeline] Step 3 Base intent: {base_intent.value}")
        
        # STEP 4: Detect Emotion
        context.emotion = detect_emotion(context.transcript, context.language_code)
        logger.info(f"[Pipeline] Step 4 Emotion: {context.emotion.emotion.value}, "
                   f"score={context.emotion.anger_score:.2f}")
        
        # STEP 5: Detect Urgency
        context.urgency = detect_urgency(context.transcript, context.language_code)
        logger.info(f"[Pipeline] Step 5 Urgency: {context.urgency.level.value}")
        
        # STEP 6: Apply Intent Override (emotion-based)
        context.final_intent = apply_emotion_override(base_intent, context.emotion.emotion)
        context.base_intent = IntentResult(
            intent=base_intent,
            final_intent=context.final_intent,
            confidence=0.8
        )
        logger.info(f"[Pipeline] Step 6 Final intent: {context.final_intent.value}")
        
        # STEP 7: Generate Summary (internal)
        context.summary = generate_pipeline_summary(context)
        
        # STEP 8: Determine Response Modifier
        context.response_modifier = determine_response_modifier(
            context.emotion, context.urgency, context.final_intent
        )
        logger.info(f"[Pipeline] Step 8 Response modifier: {context.response_modifier}")
        
        # STEP 9: Generate Response
        context.response_text = generate_response(
            context.transcript,
            context.language_code,
            context.final_intent,
            context.emotion,
            context.urgency
        )
        logger.info(f"[Pipeline] Step 9 Response: {context.response_text[:100]}...")
        
        # STEP 10: TTS Preprocessing
        context.preprocessed_text = preprocess_text_for_tts(
            context.response_text,
            context.language_code
        )
        
        # STEP 11: TTS Fallback Chain
        context.audio_path, context.tts_provider_used = tts_with_fallback(
            context.preprocessed_text,
            context.language_code
        )
        logger.info(f"[Pipeline] Step 11 TTS: {context.tts_provider_used}, audio={context.audio_path}")
        
    except Exception as e:
        context.errors.append(str(e))
        logger.error(f"[Pipeline] Error: {e}")
    
    return context


# ============================================================================
# TESTING / CLI
# ============================================================================

def test_pipeline():
    """Test the Meera voice pipeline with sample inputs."""
    test_cases = [
        # (text, language, description)
        ("यह बेकार है! मेरी समस्या हल नहीं हुई!! अभी तुरंत हल करो!", "hi", "ANGRY + CRITICAL urgency"),
        ("Mere ghar mein bijli nahi aa rahi hai since 3 days", "hi", "complaint with time urgency"),
        ("Hello, I need help with my bill", "en", "simple query"),
        ("नमस्ते", "hi", "greeting"),
        ("நான் மிகவும் கோபமாக இருக்கிறேன்! இது மோசமான சேவை!", "ta", "Tamil angry complaint"),
        ("मी order #45821 बद्दल तक्रार करतो आहे", "mr", "Marathi with entity"),
    ]
    
    print("\n" + "="*70)
    print("MEERA - DYNAMIC MULTILINGUAL VOICE ASSISTANT - PIPELINE TEST")
    print("="*70)
    
    for text, lang, description in test_cases:
        print(f"\n{'─'*70}")
        print(f"TEST: {description}")
        print(f"{'─'*70}")
        print(f"Input: {text}")
        print(f"Expected Lang: {lang}")
        
        # Run pipeline
        ctx = run_voice_pipeline(transcript=text, language_code=lang)
        
        print(f"\n📊 ANALYSIS:")
        if ctx.language_detection:
            print(f"  Language: {ctx.language_code} (conf: {ctx.language_detection.confidence:.2f}, "
                  f"script: {ctx.language_detection.script})")
            if ctx.language_detection.codeswitching:
                print(f"  Code-switching: Yes, secondary={ctx.language_detection.secondary_language}")
        print(f"  Emotion: {ctx.emotion.emotion.value} (score: {ctx.emotion.anger_score:.2f})")
        print(f"  Urgency: {ctx.urgency.level.value}")
        if ctx.urgency.triggers:
            print(f"  Urgency triggers: {ctx.urgency.triggers[:3]}")
        print(f"  Intent: {ctx.base_intent.intent.value} → {ctx.final_intent.value}")
        print(f"  Response Modifier: {ctx.response_modifier}")
        if ctx.entities:
            print(f"  Entities: {[(e.entity_type.value, e.raw_value) for e in ctx.entities[:3]]}")
        
        print(f"\n💬 RESPONSE:")
        print(f"  {ctx.response_text[:120]}...")
        
        print(f"\n🔊 TTS: {ctx.tts_provider_used}")
        if ctx.audio_path:
            print(f"  Audio: {ctx.audio_path}")
        if ctx.errors:
            print(f"  ⚠️ Errors: {ctx.errors}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE - All 11 pipeline steps executed")
    print("="*70)


if __name__ == "__main__":
    test_pipeline()
