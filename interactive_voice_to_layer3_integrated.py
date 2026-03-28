#!/usr/bin/env python3
"""
✨ MULTILINGUAL INTEGRATED VOICE → AI ANALYSIS → INTELLIGENT ROUTING → ORGANIZED JSON
=======================================================================================
"""

# ════════════════════════════════════════════════════════════════════════════════
# CPU-ONLY MODE: Disable CUDA/GPU before importing ML libraries
# ════════════════════════════════════════════════════════════════════════════════
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import json
import time
import logging
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from collections import defaultdict
from typing import Dict, Tuple, Optional
import tempfile
from dotenv import load_dotenv
import httpx

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'awaaz'))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, "awaaz", ".env"))

# ════════════════════════════════════════════════════════════════════════════════
# SARVAM API CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
SARVAM_LANG_DETECT_URL = os.environ.get("SARVAM_LANG_DETECT_API_URL", "https://api.sarvam.ai/language/detect")
SARVAM_AVAILABLE = bool(SARVAM_API_KEY)

# Import our organized system
try:
    from analytics.analytical_model import create_processor
    from models.grievance_models import create_session_id, UrgencyLevel
    from outputs.json_storage_manager import JSONStorageManager
    from core.emotion_detection import analyze_emotions
    import soundfile as sf
except ImportError as e:
    logger.error(f"Error importing core components: {e}")

# Import awaaz recorder
try:
    from awaaz.awaaz_recorder import MicCalibrator, VADEngine, Recorder, save_wav, TARGET_SR
    RECORDER_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ awaaz_recorder not available, mic recording will fail.")
    RECORDER_AVAILABLE = False
    TARGET_SR = 16000

# Import multilingual support from AWAAZ
try:
    from awaaz.src.pipeline.stt import STTProcessor
    from awaaz.src.pipeline.nlp import ModelProcessor as AWAAZNLPProcessor, LANGUAGE_CONFIG
    from awaaz.src.pipeline.tts import synthesize_speech, TTSProcessor
    from awaaz.src.pipeline.enhancements.tts_pipeline_v2 import enhanced_tts
    from awaaz.src.pipeline.phonetic_converter import PhoneticConverter
    from awaaz.src.session_store import AWAAZSession
    AWAAZ_AVAILABLE = True
except ImportError as e:
    AWAAZ_AVAILABLE = False
    logger.warning(f"AWAAZ multilingual modules not available: {e}")
    LANGUAGE_CONFIG = {
        "hi": {"name": "Hindi", "script": "Devanagari"},
        "en": {"name": "English", "script": "Latin"},
    }

GROQ_AVAILABLE = False
groq_client = None
groq_client_async = None
try:
    from groq import AsyncGroq, Groq
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        groq_client_async = AsyncGroq(api_key=api_key)
        GROQ_AVAILABLE = True
    else:
        logger.warning("GROQ_API_KEY not set - using fallback responses")
except ImportError:
    logger.warning("Groq library not installed - using fallback responses")

# Language detection
try:
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")

def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}")
    print(f"{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MEERA - MULTILINGUAL VOICE ASSISTANT - 10-STEP PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

class MeeraAssistant:
    """
    Meera: Warm, feminine, empathetic multilingual voice assistant.
    Implements 10-step processing pipeline for intelligent, context-aware responses.
    """
    
    # Language configs
    LANGUAGE_CONFIG_MEERA = {
        'hi': {'name': 'Hindi', 'script': 'Devanagari', 'terminal': '।'},
        'en': {'name': 'English', 'script': 'Latin', 'terminal': '.'},
        'ta': {'name': 'Tamil', 'script': 'Tamil', 'terminal': '.'},
        'te': {'name': 'Telugu', 'script': 'Telugu', 'terminal': '.'},
        'bn': {'name': 'Bengali', 'script': 'Bengali', 'terminal': '।'},
        'mr': {'name': 'Marathi', 'script': 'Devanagari', 'terminal': '।'},
        'gu': {'name': 'Gujarati', 'script': 'Gujarati', 'terminal': '।'},
        'kn': {'name': 'Kannada', 'script': 'Kannada', 'terminal': '.'},
        'ml': {'name': 'Malayalam', 'script': 'Malayalam', 'terminal': '.'},
        'pa': {'name': 'Punjabi', 'script': 'Gurmukhi', 'terminal': '।'},
        'ur': {'name': 'Urdu', 'script': 'Arabic', 'terminal': '۔'},
        'or': {'name': 'Odia', 'script': 'Odia', 'terminal': '።'},
        'as': {'name': 'Assamese', 'script': 'Bengali', 'terminal': '।'},
        'sa': {'name': 'Sanskrit', 'script': 'Devanagari', 'terminal': '।'},
        'ne': {'name': 'Nepali', 'script': 'Devanagari', 'terminal': '।'},
        'si': {'name': 'Sinhala', 'script': 'Sinhala', 'terminal': '।'},
    }
    
    # Anger keywords by language
    ANGER_KEYWORDS = {
        'en': {'angry', 'furious', 'useless', 'stupid', 'terrible', 'worst', 'hate', 'pathetic'},
        'hi': {'गुस्सा', 'बेकार', 'नालायक', 'बकवास', 'घटिया', 'निकम्मा'},
        'ta': {'கோபம்', 'மோசமான', 'பயனற்ற'},
        'te': {'కోపం', 'చెత్త', 'నికృష్టం'},
        'bn': {'রাগ', 'বাজে', 'অকেজো'},
        'mr': {'राग', 'बेकार', 'निकामी'},
        'gu': {'ગુસ્સો', 'નકામું', 'ઘટિયા'},
        'kn': {'ಕೋಪ', 'ಕೆಟ್ಟ', 'ನಿಷ್ಪ್ರಯೋಜಕ'},
        'ml': {'കോപം', 'മോശം'},
        'pa': {'ਗੁੱਸਾ', 'ਬੇਕਾਰ', 'ਨਿਕੰਮਾ'},
        'ur': {'غصہ', 'بیکار', 'گھٹیا'},
    }
    
    # Urgency keywords
    URGENCY_CRITICAL = {
        'en': {'right now', 'immediately', 'asap', 'emergency', 'urgent', 'expires today', 'last chance', 'legal action'},
        'hi': {'अभी', 'तुरंत', 'फ़ौरन', 'आपातकाल', 'जल्दी'},
        'ta': {'இப்போதே', 'உடனடியாக', 'அவசரம்'},
    }
    
    # Urgency soft keywords
    URGENCY_HIGH = {
        'en': {'still not', 'waiting since', 'how long', 'already'},
        'hi': {'अभी तक नहीं', 'कब होगा', 'कितने दिन'},
    }
    
    # Greeting responses
    GREETINGS = {
        'en': "Hello! I'm Meera. How can I help you today?",
        'hi': "नमस्ते! मैं मीरा हूँ। आज मैं आपकी कैसे मदद कर सकती हूँ?",
        'ta': "வணக்கம்! நான் மீரா. இன்று எப்படி உதவட்டும்?",
        'te': "నమస్కారం! నేను మీరా. ఈరోజు ఎలా సహాయపడగలను?",
        'bn': "নমস্কার! আমি মীরা। আজ কীভাবে সাহায্য করতে পারি?",
        'mr': "नमस्कार! मी मीरा. आज मी कशी मदत करू?",
        'gu': "નમસ્તે! હું મીરા. આજે હું કેવી રીતે મદદ કરી શકું?",
        'kn': "ನಮಸ್ಕಾರ! ನಾನು ಮೀರಾ. ಇಂದು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
        'ml': "നമസ്കാരം! ഞാൻ മീര. ഇന്ന് എങ്ങനെ സഹായിക്കാം?",
        'pa': "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਮੀਰਾ। ਅੱਜ ਕਿਵੇਂ ਮਦਦ ਕਰਾਂ?",
        'ur': "السلام علیکم! میں میرا ہوں۔ آج کیسے مدد کر سکتی ہوں؟",
        'or': "ନମସ୍କାର! ମୁଁ ମୀରା. ଆଜ ମୁଁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?",
    }
    
    # Urgency acknowledgment phrases
    URGENCY_ACK = {
        'en': "I'm on this right now:",
        'hi': "मैं अभी इस पर हूँ:",
        'ta': "இதை இப்போதே கவனிக்கிறேன்:",
        'te': "దీన్ని ఇప్పుడే చూస్తున్నాను:",
        'bn': "এটি আমি এখনই দেখছি:",
        'mr': "मी आत्ताच बघत आहे:",
        'gu': "હું હમણાં જ જોઉં છું:",
        'kn': "ಈಗಲೇ ನೋಡುತ್ತಿದ್ದೇನೆ:",
        'ml': "ഞാൻ ഇപ്പോൾ തന്നെ നോക്കുന്നു:",
        'pa': "ਮੈਂ ਹੁਣੇ ਦੇਖ ਰਹੀ ਹਾਂ:",
        'ur': "میں ابھی دیکھ رہی ہوں:",
    }
    
    # Anger acknowledgment phrases
    ANGER_ACK = {
        'en': "I understand your frustration. Let me fix this now.",
        'hi': "मैं समझ सकती हूँ। मैं अभी मदद करूँगी।",
        'ta': "புரிந்துகொள்கிறேன். உடனே தீர்வு காண்பேன்.",
        'te': "అర్థమైంది. వెంటనే పరిష్కారం చూపిస్తాను.",
        'bn': "বুঝতে পারছি। এখনই সাহায্য করব।",
        'mr': "समजतं. मी लगेच मदत करते.",
        'gu': "સમજી શકું છું. તરત મદદ કરીશ.",
        'kn': "ಅರ್ಥವಾಗುತ್ತದೆ. ತಕ್ಷಣ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.",
        'ml': "മനസ്സിലാകുന്നു. ഉടൻ സഹായിക്കുന്നു.",
        'pa': "ਸਮਝਦੀ ਹਾਂ। ਤੁਰੰਤ ਮਦਦ ਕਰਾਂਗੀ।",
        'ur': "سمجھتی ہوں۔ ابھی مدد کروں گی۔",
    }
    
    def __init__(self):
        self.session_history = defaultdict(list)
        self.session_context = {}
    
    # STEP 1: Detect Language
    # STEP 1: Detect Language using SARVAM API
    async def detect_language(self, text: str) -> Tuple[str, str, str]:
        """Detect language using Sarvam API. Returns (lang_code, confidence, script_detected)"""
        if not text or len(text.strip()) == 0:
            return 'en', 'low', 'unknown'
        
        # Try Sarvam API first
        if SARVAM_AVAILABLE:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        SARVAM_LANG_DETECT_URL,
                        headers={"Authorization": f"Bearer {SARVAM_API_KEY}"},
                        json={"input": text}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        lang_code = result.get('language', 'en').lower()[:2]
                        confidence = result.get('confidence', 0.5)
                        conf_level = 'high' if confidence > 0.7 else 'medium' if confidence > 0.5 else 'low'
                        script = self.LANGUAGE_CONFIG_MEERA.get(lang_code, {}).get('script', 'Unknown')
                        logger.info(f"[MEERA] Sarvam API detected: {lang_code} (conf: {confidence:.2f})")
                        return lang_code, conf_level, script
            except Exception as e:
                logger.warning(f"Sarvam API language detection failed: {e}")
        
        # Fallback to script-based detection
        script_markers = {
            'Devanagari': ['\u0900', '\u0901', '\u0915', '\u0916'],
            'Tamil': ['\u0BA4', '\u0BA5', '\u0BA6'],
            'Telugu': ['\u0C24', '\u0C25', '\u0C26'],
            'Kannada': ['\u0C95', '\u0C96', '\u0C97'],
            'Malayalam': ['\u0D15', '\u0D16', '\u0D17'],
            'Bengali': ['\u0985', '\u0986', '\u0987'],
            'Gujarati': ['\u0A95', '\u0A96', '\u0A97'],
            'Gurmukhi': ['\u0A15', '\u0A16', '\u0A17'],
            'Odia': ['\u0B15', '\u0B16', '\u0B17'],
            'Arabic': ['\u0628', '\u0629', '\u062A'],
        }
        
        detected_script = 'Latin'
        for script, markers in script_markers.items():
            if any(marker in text for marker in markers):
                detected_script = script
                break
        
        script_lang_map = {
            'Devanagari': 'hi',
            'Tamil': 'ta',
            'Telugu': 'te',
            'Kannada': 'kn',
            'Malayalam': 'ml',
            'Bengali': 'bn',
            'Gujarati': 'gu',
            'Gurmukhi': 'pa',
            'Odia': 'or',
            'Arabic': 'ur',
            'Latin': 'en',
        }
        
        lang_code = script_lang_map.get(detected_script, 'en')
        confidence = 'high' if detected_script != 'Latin' else 'medium'
        logger.info(f"[MEERA] Script-based detection: {lang_code} ({confidence})")
        
        return lang_code, confidence, detected_script
    
    # STEP 2: Clean Text
    def clean_text(self, text: str, lang_code: str) -> str:
        """Clean text: remove markdown, URLs, add proper punctuation"""
        import re
        cleaned = text
        cleaned = re.sub(r'\[.*?\]\(.*?\)', '', cleaned)  # Remove [text](url)
        cleaned = re.sub(r'https?://\S+', '', cleaned)  # Remove URLs
        cleaned = re.sub(r'[*#`<>{}[\]]', '', cleaned)  # Remove markdown
        cleaned = cleaned.strip()
        
        # Add terminal punctuation
        if cleaned and not cleaned[-1] in '.।۔।؟!':
            terminal = self.LANGUAGE_CONFIG_MEERA.get(lang_code, {}).get('terminal', '.')
            cleaned += ' ' + terminal
        
        return cleaned
    
    # STEP 3: Extract Entities
    def extract_entities(self, text: str) -> Dict:
        """Extract entities: order_id, product, date, amount, location, issue_type"""
        entities = {}
        import re
        
        # Order/Ticket IDs
        if re.search(r'(?:order|ticket|ref|id)[:\s]*([\w\d]+)', text, re.I):
            entities['order_id'] = re.search(r'(?:order|ticket|ref|id)[:\s]*([\w\d]+)', text, re.I).group(1)
        
        # Amount
        if re.search(r'₹|रु|rupees?|रुपये?|dollars?|\$|inr', text, re.I):
            match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:₹|रु|rupees?|रुपये?)', text, re.I)
            if match:
                entities['amount'] = match.group(1)
        
        return entities
    
    # STEP 4: Classify Intent
    def classify_intent(self, text: str, lang_code: str) -> str:
        """Classify intent: greeting, query, complaint, escalation, etc."""
        text_lower = text.lower()
        text_orig = text
        
        # Greeting detection (enhanced)
        greeting_words = {'hi', 'hello', 'bye', 'thanks', 'namaste', 'नमस्ते', 'वणक्कम्', 'hey', 'hola', 'नमस्कार', 'का हाल', 'कैसे'}
        greeting_unicodes = {'नमस्ते', 'नमस्कार', 'वंदे', 'सलाम', 'وسلام', 'வணக்கம்', 'ನಮಸ್ಕಾರ'}
        
        if any(word in text_lower for word in greeting_words) or any(word in text_orig for word in greeting_unicodes):
            # But not if it has complaints
            if not any(word in text_lower for word in {'problem', 'issue', 'broken', 'complaint'}):
                return 'greeting'
        
        complaint_words = {'problem', 'issue', 'broken', 'not working', 'error', 'समस्या', 'परेशानी', 'शिकायत', 'गलत', 'खराब'}
        escalation_words = {'urgent', 'legal', 'complaint', 'social media', 'अभी', 'तुरंत', 'फ़ौरन', 'immediately'}
        
        if any(word in text_lower for word in escalation_words):
            return 'escalation'
        elif any(word in text_lower for word in complaint_words):
            return 'complaint'
        else:
            return 'query'
    
    # STEP 5: Detect Emotion & Anger using Groq LLM
    async def detect_emotion(self, text: str, lang_code: str) -> Tuple[str, float]:
        """Detect emotion using Groq LLM. Returns (emotion_name, anger_score)"""
        
        # Quick heuristic first
        anger_score = 0.0
        emotion = 'NEUTRAL'
        
        if text.count('!') >= 2:
            anger_score += 0.2
        
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars > 0:
            uppercase_ratio = sum(1 for c in text if c.isupper()) / alpha_chars
            if uppercase_ratio > 0.4:
                anger_score += 0.2
        
        anger_words = self.ANGER_KEYWORDS.get(lang_code, set())
        if any(word in text.lower() for word in anger_words):
            anger_score += 0.3
        
        # Use Groq for deeper classification if available
        if GROQ_AVAILABLE and groq_client_async is not None:
            try:
                prompt = f"""Analyze the emotion in this text:

Text: "{text}"

Respond with ONLY: emotion_type|anger_score (e.g., ANGRY|0.85)
Emotion types: ANGRY, HAPPY, NEUTRAL, CONFUSED, SAD
Anger score: 0.0 to 1.0"""
                
                message = await groq_client_async.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=50
                )
                
                response_text = message.choices[0].message.content.strip()
                if '|' in response_text:
                    emotion, score_str = response_text.split('|')
                    emotion = emotion.strip().upper()
                    anger_score = float(score_str.strip())
                    logger.info(f"[MEERA] Groq emotion: {emotion} ({anger_score:.2f})")
            except Exception as e:
                logger.warning(f"Groq emotion detection failed: {e}")
        
        if anger_score > 0.5:
            emotion = 'ANGRY'
        
        return emotion, min(anger_score, 1.0)
    
    # STEP 6: Detect Urgency using Groq LLM
    async def detect_urgency(self, text: str, lang_code: str) -> str:
        """Detect urgency level using Groq LLM"""
        text_lower = text.lower()
        
        # Quick keyword check
        critical_words = self.URGENCY_CRITICAL.get(lang_code, set())
        if any(word in text_lower for word in critical_words):
            return 'CRITICAL'
        
        high_words = self.URGENCY_HIGH.get(lang_code, set())
        if any(word in text_lower for word in high_words):
            return 'HIGH'
        
        # Use Groq for deeper classification
        if GROQ_AVAILABLE and groq_client_async is not None:
            try:
                prompt = f"""Classify urgency level:

Text: "{text}"

Respond with ONLY the urgency level:
CRITICAL, HIGH, MEDIUM, or LOW"""
                
                message = await groq_client_async.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=20
                )
                
                urgency = message.choices[0].message.content.strip().upper()
                if urgency in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    logger.info(f"[MEERA] Groq urgency: {urgency}")
                    return urgency
            except Exception as e:
                logger.warning(f"Groq urgency detection failed: {e}")
        
        return 'MEDIUM'
    
    # STEP 7: Build Internal Summary
    def build_summary(self, text: str, lang_code: str, confidence: str, emotion: str, 
                     anger_score: float, intent: str, urgency: str) -> Dict:
        """Build internal processing summary"""
        return {
            'lang': lang_code,
            'confidence': confidence,
            'emotion': emotion,
            'anger_score': anger_score,
            'intent': intent,
            'urgency': urgency,
            'text_sample': text[:50],
        }
    
    # STEP 8: Select Response Modifier
    def get_response_prefix(self, urgency: str, emotion: str, intent: str, lang_code: str) -> str:
        """Get response prefix based on urgency and emotion"""
        prefix = ""
        
        if urgency == 'CRITICAL':
            prefix += self.URGENCY_ACK.get(lang_code, "I'm on this right now:")
            if emotion == 'ANGRY':
                prefix += " " + self.ANGER_ACK.get(lang_code, "I understand.")
        elif emotion == 'ANGRY' and intent in ['complaint', 'escalation']:
            prefix = self.ANGER_ACK.get(lang_code, "I understand.")
        
        return prefix
    
    # STEP 10: Generate Response
    async def generate_response(self, text: str, lang_code: str, urgency: str, 
                               intent: str, processing_result: str) -> str:
        """Generate multilingual response using Groq with smart fallback"""
        
        emotion, anger_score = await self.detect_emotion(text, lang_code)
        prefix = self.get_response_prefix(urgency, emotion, intent, lang_code)
        
        # Use Groq if available
        if GROQ_AVAILABLE and groq_client_async is not None:
            try:
                lang_name = self.LANGUAGE_CONFIG_MEERA.get(lang_code, {}).get('name', 'English')
                
                prompt = f"""You are Meera, a warm, empathetic Indian voice assistant.

User said: "{text}"
Language: {lang_name}
Intent: {intent}
Urgency: {urgency}
Emotion: {emotion}

Respond in pure {lang_name} (native script, no English). Be warm, empathetic, and conversational. 
Response must be 2-3 sentences max. {prefix if prefix else ""}
Use Indian cultural context. No markdown, no bullet points."""

                message = await groq_client_async.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=150
                )
                return message.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Groq unavailable, using fallback: {e}")
        
        # Fallback responses (template-based)
        fallback_responses = {
            'en': {
                'greeting': 'Hello! How can I assist you today?',
                'complaint': 'Thank you for reporting this issue. We are looking into it.',
                'escalation': 'This has been marked as urgent. Our team will contact you shortly.',
                'query': 'Your query has been received. We will help you soon.'
            },
            'hi': {
                'greeting': 'नमस्ते! आप कैसे हैं?',
                'complaint': 'आपकी समस्या के लिए धन्यवाद। हम इस पर काम कर रहे हैं।',
                'escalation': 'यह तुरंत के लिए चिह्नित किया गया है। हमारी टीम आपसे जल्द संपर्क करेगी।',
                'query': 'आपकी प्रश्न प्राप्त हुआ है। हम आपकी मदद करेंगे।'
            },
            'ta': {
                'greeting': 'வணக்கம்! நீங்கள் எப்படி இருக்கிறீர்கள்?',
                'complaint': 'உங்கள் பிரச்சனைக்கு நன்றி. நாங்கள் அதை பார்த்துக்கொண்டிருக்கிறோம்.',
                'escalation': 'இது உடனடி எனக் குறிக்கப்பட்டுள்ளது. எங்கள் குழு விரைவில் உங்களைத் தொடர்பு கொள்ளும்.',
                'query': 'உங்கள் கேள்வி பெறப்பட்டுவிட்டது. நாங்கள் உங்களுக்கு உதவியாக இருப்போம்.'
            },
            'mr': {
                'greeting': 'नमस्कार! आप कसे आहात?',
                'complaint': 'आपल्या समस्येबद्दल धन्यवाद. आम्ही त्यावर काम करत आहोत.',
                'escalation': 'हे लगेचसाठी चिन्हांकित केले आहे. आमची टीम लगेच आपल्याशी संपर्क साधेल.',
                'query': 'आपली प्रश्न प्राप्त झाली. आम्ही लगेच मदत करू.'
            }
        }
        
        lang_responses = fallback_responses.get(lang_code, fallback_responses.get('en', {}))
        response = lang_responses.get(intent, lang_responses.get('query', 'Your request has been received.'))
        
        if prefix:
            return f"{prefix} {response}"
        return response
    
    # MAIN ORCHESTRATION: Run all steps
    async def process_input(self, text: str, session_id: str) -> Dict:
        """Run full 10-step pipeline"""
        
        # STEP 1: Detect language (using Sarvam API)
        lang_code, conf, script = await self.detect_language(text)
        logger.info(f"[MEERA] STEP 1 - LANG DETECT: {lang_code} ({conf}) from {script} [Sarvam API]")
        
        # STEP 2: Clean text
        cleaned_text = self.clean_text(text, lang_code)
        logger.info(f"[MEERA] STEP 2 - TEXT CLEAN: {cleaned_text[:50]}")
        
        # STEP 3: Extract entities
        entities = self.extract_entities(text)
        logger.info(f"[MEERA] STEP 3 - ENTITIES: {entities}")
        
        # STEP 4: Classify intent
        intent = self.classify_intent(text, lang_code)
        logger.info(f"[MEERA] STEP 4 - INTENT: {intent}")
        
        # STEP 5: Detect emotion (using Groq LLM)
        emotion, anger_score = await self.detect_emotion(text, lang_code)
        logger.info(f"[MEERA] STEP 5 - EMOTION: {emotion} (score: {anger_score:.2f}) [Groq LLM]")
        
        # STEP 6: Detect urgency (using Groq LLM)
        urgency = await self.detect_urgency(text, lang_code)
        logger.info(f"[MEERA] STEP 6 - URGENCY: {urgency} [Groq LLM]")
        
        # STEP 7: Build summary
        summary = self.build_summary(text, lang_code, conf, emotion, anger_score, intent, urgency)
        logger.info(f"[MEERA] STEP 7 - SUMMARY: {summary}")
        
        # STEP 9 & 10: Generate response
        greeting = self.GREETINGS.get(lang_code, "Hello!")
        if intent == 'greeting':
            response = greeting
        else:
            processing_msg = f"Your {intent} regarding {entities.get('order_id', 'your issue')} has been received"
            response = await self.generate_response(text, lang_code, urgency, intent, processing_msg)
        
        logger.info(f"[MEERA] STEP 10 - RESPONSE: {response}")
        
        return {
            'session_id': session_id,
            'lang_code': lang_code,
            'lang_name': self.LANGUAGE_CONFIG_MEERA[lang_code]['name'],
            'confidence': conf,
            'original_text': text,
            'cleaned_text': cleaned_text,
            'intent': intent,
            'emotion': emotion,
            'anger_score': anger_score,
            'urgency': urgency,
            'entities': entities,
            'response': response,
        }


async def generate_groq_response(transcript: str, language: str, urgency: str, intent: str, service_name: str) -> str:
    """
    Generate AI response using Groq in the detected language.
    Summarizes issue, gives immediate steps, and maps to government scheme.
    """
    if GROQ_AVAILABLE and groq_client_async is not None:
        try:
            lang_config = LANGUAGE_CONFIG.get(language, {})
            lang_name = lang_config.get('name', 'English')
            
            prompt = f"""You are a helpful AI assistant for Indian citizens reporting grievances.
        
User's issue: "{transcript}"
Detected Category: {intent}
Urgency Level: {urgency}
Routed Department/Service: {service_name}

Provide a short response directed to the user entirely in pure Indian native {lang_name} that:
1. Acknowledges their specific issue empathetically using a very smooth, human-like, Indian cultural conversational context.
2. Explains exactly what immediate actionable steps they can take right now based on fetching live details.
3. Explicitly mentions which Indian government scheme or specific department is mapped to this.

Keep your response highly conversational, extremely natural, reassuring, and concise (3-4 sentences max). Ensure any English technical/department jargon is properly transliterated and dynamically translated into Indian dialect smoothly. Respond ONLY with the clean spoken text to be synthesized to the user strictly in {lang_name}, in its native script without any bullet points or markdown."""
            
            message = await groq_client_async.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            return message.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Groq response generation failed: {e}")
    
    # Fallback template-based response
    fallback_responses = {
        'en': f"Your {intent} has been documented and routed to {service_name}. You will receive updates shortly.",
        'hi': f"आपकी {intent} दर्ज की गई है और {service_name} को भेजी गई है। आप जल्द ही अपडेट पाएंगे।",
        'ta': f"உங்கள் {intent} பதிவு செய்யப்பட்டுவிட்டது. விரைவில் தகவல் பெறுவீர்கள்.",
        'mr': f"आपली {intent} नोंदणी केली गेली आहे. लगेच अपडेट मिळेल."
    }
    
    return fallback_responses.get(language, fallback_responses['en'])


def record_live_audio(duration_s: int = 15):
    """Record audio from microphone with VAD voice isolation"""
    if not RECORDER_AVAILABLE:
        print("❌ awaaz_recorder module not available. Cannot use microphone.")
        return None
    
    print_section("🎤 MICROPHONE CALIBRATION & RECORDING")
    
    print("[REC] Calibrating microphone...")
    try:
        calibrator = MicCalibrator()
        calibration = calibrator.calibrate()
        print("  ✓ Microphone calibrated")
    except Exception as e:
        print(f"  ⚠️  Calibration warning: {e}")
        calibration = None
    
    print(f"\n{Colors.GREEN}🔴 RECORDING IN PROGRESS...{Colors.END}")
    print(f"{Colors.YELLOW}📣 Please speak your complaint clearly.{Colors.END}")
    print(f"{Colors.CYAN}Ready — speak now (max {duration_s}s, silence cutoff 20s){Colors.END}")
    
    try:
        vad = VADEngine(aggressiveness=1)  # Less aggressive VAD (1 instead of 2)
        recorder = Recorder(vad=vad, device_index=None)
        
        audio = recorder.record(
            max_duration_s=duration_s,
            silence_ms=20000,  # 20 seconds silence before cutoff
            calibration=calibration
        )
        
        if audio is None or len(audio) == 0:
            print("  ❌ No audio captured")
            return None
        
        duration = len(audio) / TARGET_SR
        print(f"\n{Colors.GREEN}✓ Recording complete: {duration:.2f}s captured{Colors.END}")
        
        audio_path = tempfile.mktemp(suffix=".wav")
        save_wav(audio, TARGET_SR, audio_path)
        print(f"  ✓ Audio saved locally to temp file.")
        
        return audio_path, audio
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Recording stopped{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        return None

async def main():
    print_header("🎤 MULTILINGUAL INTEGRATED VOICE GRIEVANCE PROCESSING 🎤")
    
    processor = create_processor(use_groq=False)
    json_storage = JSONStorageManager(base_output_dir="outputs/json_results")
    meera = MeeraAssistant()  # Initialize Meera
    
    # Try to record audio, but allow text input as fallback
    recording_result = record_live_audio(duration_s=20)
    
    # If no audio recorded, offer text input option
    if not recording_result:
        print(f"\n{Colors.YELLOW}No audio recorded. Try text input instead?{Colors.END}")
        user_input = input(f"{Colors.CYAN}Enter complaint (or press Enter to skip): {Colors.END}").strip()
        
        if not user_input:
            print(f"{Colors.YELLOW}Cancelled.{Colors.END}")
            return
        
        # Use text input directly
        transcript_native = user_input
        audio_data = None
        audio_file_path = None
        lang_code = "auto"  # Will be auto-detected by Meera
        confidence = 0.5
    else:
        audio_file_path, audio_data = recording_result
    
    print_section("📝 STEP 2: STT TRANSCRIPTION & LANGUAGE DETECTION")
    
    # Only do STT if we have audio file
    if audio_file_path:
        stt = STTProcessor(preferred_provider="groq_whisper")
        await stt.load()
        
        # Lower confidence threshold for better speech capture
        if hasattr(stt, 'confidence_threshold'):
            stt.confidence_threshold = 0.3
        else:
            # Override via provider config
            for provider in stt.providers:
                if hasattr(provider, 'confidence_threshold'):
                    provider.confidence_threshold = 0.3
        
        stt_result = await stt.transcribe(audio_file_path, language="auto")
        if not stt_result or not stt_result.text:
            print("  ❌ STT failed - trying fallback transcription")
            print("  💡 Tip: When you run again, speak CLEARLY and LOUDLY for 5-10 seconds")
            return
        
        lang_code = stt_result.detected_language or "hi"
        confidence = stt_result.confidence
        transcript = stt_result.text
        transcript_native = stt_result.native_script_text or transcript
        script = LANGUAGE_CONFIG.get(lang_code, {}).get('script', 'Unknown')
        lang_name = LANGUAGE_CONFIG.get(lang_code, {}).get('name', 'Unknown')
        
        print(f"  {Colors.CYAN}Detected transcript (native script):{Colors.END}")
        print(f"  \"{transcript_native}\"")
        print(f"\n  {Colors.CYAN}Language Detection (from STT audio analysis):{Colors.END}")
        print(f"  • Language: {lang_name} ({lang_code})")
        print(f"  • Script: {script}")
        print(f"  • Confidence: {confidence*100:.1f}%\n")
    else:
        # Text input mode - skip STT
        print(f"  {Colors.YELLOW}[TEXT MODE] Skipping STT, using direct text input{Colors.END}")
        print(f"  {Colors.CYAN}Text: \"{transcript_native}\"{Colors.END}")
        print(f"  {Colors.YELLOW}→ Language will be auto-detected by Meera from text content\n{Colors.END}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MEERA 10-STEP PROCESSING PIPELINE
    # ═══════════════════════════════════════════════════════════════════════════════
    print_section("🧠 MEERA MULTILINGUAL ASSISTANT - 10-STEP PIPELINE")
    session_id = create_session_id()
    
    meera_result = await meera.process_input(transcript_native, session_id)
    
    print(f"\n  {Colors.CYAN}[MEERA PROCESSING SUMMARY]{Colors.END}")
    print(f"  ✓ Language: {meera_result['lang_name']} ({meera_result['lang_code']})")
    print(f"  ✓ Intent: {meera_result['intent']}")
    print(f"  ✓ Emotion: {meera_result['emotion']} (anger: {meera_result['anger_score']:.2f})")
    print(f"  ✓ Urgency: {meera_result['urgency']}")
    
    if meera_result['entities']:
        print(f"  ✓ Entities: {meera_result['entities']}")
    
    print(f"\n  {Colors.YELLOW}[MEERA RESPONSE]{Colors.END}")
    print(f"  \"{meera_result['response']}\"")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Continue with existing analysis pipeline (works with or without audio)
    # ═══════════════════════════════════════════════════════════════════════════════
    print_section("🧠 STEP 3: AI ANALYSIS & MULTILINGUAL ROUTING")
    
    # Use detected language from Meera if we're in text mode
    analysis_lang = meera_result['lang_code']
    
    analytical_model = processor.process_grievance(
        session_id=session_id,
        transcript=transcript_native,
        audio_data=audio_data,  # Will be None for text input
        sample_rate=TARGET_SR if audio_data else 0,
        detected_language=analysis_lang,  # Use Meera's detected language
        state="maharashtra",
    )
    
    print(f"  ✓ NLP Intent: {analytical_model.intent.primary_intent}")
    urgency_level = analytical_model.intent.urgency_level.name if analytical_model.intent.urgency_level else "MEDIUM"
    print(f"  ✓ Urgency: {urgency_level}")
    print(f"  ✓ Emotion: {analytical_model.emotion.detected_emotion.name}")
    print(f"  ✓ Anger Score: {analytical_model.emotion.anger_score:.2f}\n")
    
    print_section("🚦 STEP 4: INTELLIGENT ROUTING & ESCALATION")
    analytical_model, escalation_info = processor.apply_routing_and_escalation(
        analytical_model,
        transcript=transcript_native,
        time_since_filing_minutes=0,
        num_previous_calls=0,
    )
    
    service_mapped = analytical_model.routing.mapped_service.service_name if analytical_model.routing.mapped_service else "General Dept"
    print(f"  ✓ Department: {Colors.CYAN}{analytical_model.routing.primary_department.upper()}{Colors.END}")
    print(f"  ✓ Priority: P{analytical_model.routing.priority_level}")
    print(f"  ✓ Service: {service_mapped}")
    
    print_section("🤖 STEP 5: GROQ AI RESPONSE (STEPS & SCHEME IN NATIVE LANGUAGE)")
    groq_response = await generate_groq_response(
        transcript_native,
        lang_code,
        urgency_level,
        analytical_model.intent.primary_intent,
        service_mapped
    )
    print(f"  {Colors.CYAN}AI Actionable Response ({lang_name}):{Colors.END}")
    print(f"  \"{groq_response}\"\n")
    
    print_section("🔊 STEP 6: AUDIO SYNTHESIS (TTS - ENHANCED SARVAM MULTILINGUAL)")
    
    session = AWAAZSession(session_id=session_id)
    session.lang = lang_code
    session.lang_name = lang_name
    
    # Pass emotion and intent for human-like TTS adjustments
    session.anger_score = analytical_model.emotion.anger_score
    session.intent = analytical_model.intent.primary_intent
    session.emotion_name = analytical_model.emotion.detected_emotion.name
    session.is_emergency = (urgency_level == "CRITICAL")
    
    temp_wav = f"/tmp/{session_id}_reply.wav"
    
    # Use Meera's response for TTS instead of groq_response for more natural feel
    tts_text = meera_result['response']
    print(f"  [TTS] Synthesizing Meera's voice (warm, empathetic) for {lang_name}...")
    
    try:
        # Try enhanced TTS first
        base_tts = TTSProcessor(preferred_provider="sarvam")
        success = enhanced_tts(
            text=tts_text,
            session=session,
            output_path=temp_wav,
            existing_tts=base_tts
        )
        
        if success and os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 1000:
            print(f"  ✓ Meera's TTS Generated successfully: {temp_wav}")
            print("  🔊 Playing Meera's response...")
            result = os.system(f"afplay {temp_wav} 2>/dev/null || play {temp_wav} 2>/dev/null || mpv {temp_wav} 2>/dev/null")
            if result != 0:
                print(f"  ⚠️  Audio playback skipped (no player available)")
        else:
            print(f"  ⚠️  TTS synthesis incomplete - displaying text instead")
            print(f"  📝 Meera's response: {tts_text}")
    except Exception as e:
        logger.warning(f"TTS synthesis failed: {e}")
        print(f"  ⚠️  TTS failed - displaying text response")
        print(f"  📝 Meera's response: {tts_text}")
    
    print_section("📁 STEP 7: ORGANIZED JSON STORAGE")
    saved_paths = processor.save_result_organized(analytical_model, escalation_info=escalation_info)
    print(f"  ✓ Saved to by_urgency/{urgency_level}/... {saved_paths['by_urgency'].split('/')[-1]}")
    print(f"  ✓ Saved to by_department/{analytical_model.routing.primary_department}/... {saved_paths['by_department'].split('/')[-1]}")
    
    # Save Meera's processing result too
    # Convert numpy types to JSON-serializable Python types
    def convert_to_serializable(obj):
        """Convert numpy/pandas types to JSON-serializable Python types"""
        import numpy as np
        if isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()  # Convert numpy type to Python native
        else:
            return obj
    
    grievance_dict = analytical_model.to_dict() if hasattr(analytical_model, 'to_dict') else str(analytical_model)
    
    meera_output = {
        'meera_processing': meera_result,
        'session_info': {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'grievance_summary': convert_to_serializable(grievance_dict) if isinstance(grievance_dict, dict) else grievance_dict,
        }
    }
    
    meera_json_path = f"outputs/json_results/meera_interactions/{session_id}.json"
    os.makedirs(os.path.dirname(meera_json_path), exist_ok=True)
    with open(meera_json_path, 'w', encoding='utf-8') as f:
        json.dump(convert_to_serializable(meera_output), f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Meera interaction saved: {meera_json_path}")
    
    print_header("✅ SYSTEM OPERATING PERFECTLY - MEERA ASSISTANT ACTIVE")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  Interrupted{Colors.END}\n")
