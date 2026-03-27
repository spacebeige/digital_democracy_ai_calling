#!/usr/bin/env python3
"""
✨ MULTILINGUAL INTEGRATED VOICE → AI ANALYSIS → INTELLIGENT ROUTING → ORGANIZED JSON
=======================================================================================
Enhanced with:
- Vulgarity detection FIRST (before NLP routing)
- Devanagari abuse term detection for Hindi/Marathi
- Better model (llama-3.3-70b-versatile) for accurate intent
- Progressive warning system with proper routing
"""

import sys
import os
import json
import time
import logging
import asyncio
import re
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from collections import defaultdict
from typing import Dict, Tuple, Optional, List, Set
import tempfile
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from scheme_classifier import classify_scheme, classify_scheme_async
from db_scheme_fetcher import fetch_schemes_from_neon
from db_scheme_fetcher import fetch_schemes_from_neon
sys.path.insert(0, os.path.join(BASE_DIR, 'awaaz'))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, "awaaz", ".env"))

# ═══════════════════════════════════════════════════════════════════════════════
# VULGARITY DETECTION SYSTEM (DEVANAGARI + ROMANIZED)
# ═══════════════════════════════════════════════════════════════════════════════

class VulgarityDetector:
    """Fast lexicon-based vulgarity detection for Indian languages with multi-phrase support."""
    
    def __init__(self):
        self.single_terms, self.phrases = self._load_lexicon()
        self.session_warnings: Dict[str, int] = {}
        self.warning_messages = self._init_warning_messages()
    
    def _load_lexicon(self) -> Tuple[Set[str], Set[str]]:
        """Load abuse terms and phrases into separate sets for efficient matching."""
        lexicon_path = Path(BASE_DIR) / "backend/app/services/emergency_keywords.json"
        single_terms: Set[str] = set()
        phrases: Set[str] = set()
        
        try:
            with open(lexicon_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                abuse_data = data.get("abuse_toxicity", {})
                
                for category, terms in abuse_data.items():
                    for term in terms:
                        term_lower = term.lower()
                        # Separate single words from multi-word phrases
                        if ' ' in term_lower or len(term_lower.split()) > 1:
                            phrases.add(term_lower)
                            phrases.add(term_lower.replace('-', ' '))
                        else:
                            single_terms.add(term_lower)
                            single_terms.add(term_lower.replace('-', ''))
                
                logger.info(f"[VULGARITY] Loaded {len(single_terms)} single terms + {len(phrases)} phrases")
        except Exception as e:
            logger.error(f"[VULGARITY] Failed to load lexicon: {e}")
            # Fallback critical terms (Devanagari + Romanized)
            single_terms = {
                "चोद", "चूस", "लवडा", "लौड़ा", "लोडा", "गांड", "भोसड़ी", "रंडी", "रांड",
                "मादरचोद", "बहनचोद", "भड़वा", "हरामी", "चूतिया", "झवाड्या", "पादरचोद",
                "बेनचोद", "भेनचोद", "लुंड", "झाट", "चूसना", "चूसले",
                "chod", "choos", "lavda", "lauda", "gaand", "bhosdi", "randi", "rand",
                "madarchod", "benchod", "bhadwa", "harami", "chutiya", "jhavadya",
                "mc", "bc", "bkl", "lund", "jhaat", "chodna"
            }
            phrases = {"teri maa ki", "gand mara", "maa ki chut", "तेरी माँ की", "गांड मरा"}
        
        return single_terms, phrases
    
    def _init_warning_messages(self) -> Dict[str, Dict[int, str]]:
        """Warning messages in multiple languages - refined and polite."""
        return {
            "hi": {
                1: "कृपया सभ्य भाषा का प्रयोग करें। हम आपकी मदद करना चाहते हैं, लेकिन असभ्य भाषा स्वीकार्य नहीं है। यह आपकी पहली चेतावनी है।",
                2: "आपने फिर से असभ्य भाषा का उपयोग किया है। कृपया अपनी भाषा सुधारें ताकि हम आपकी शिकायत दर्ज कर सकें।",
                3: "यह आपकी अंतिम चेतावनी है। अगली बार असभ्य भाषा का प्रयोग करने पर सेवा तुरंत बंद कर दी जाएगी।",
                4: "असभ्य व्यवहार के कारण सेवा समाप्त की जा रही है। कृपया बाद में पुनः प्रयास करें।"
            },
            "mr": {
                1: "कृपया सभ्य भाषा वापरा। आम्ही तुम्हाला मदत करू इच्छितो, पण असभ्य भाषा मान्य नाही। ही तुमची पहिली चेतावणी आहे।",
                2: "तुम्ही पुन्हा असभ्य भाषा वापरली आहे। कृपया तुमची भाषा सुधारा जेणेकरून आम्ही तुमची तक्रार नोंदवू शकू।",
                3: "ही तुमची अंतिम चेतावणी आहे। पुन्हा असभ्य भाषा वापरल्यास सेवा तात्काळ बंद केली जाईल।",
                4: "असभ्य वर्तनामुळे सेवा बंद केली जात आहे। कृपया नंतर पुन्हा प्रयत्न करा।"
            },
            "en": {
                1: "Please use respectful language. We want to help you, but abusive language is not acceptable. This is your first warning.",
                2: "You have used abusive language again. Please correct your language so we can register your complaint.",
                3: "This is your final warning. Using abusive language again will result in immediate service termination.",
                4: "Service is being terminated due to abusive behavior. Please try again later."
            },
            "ta": {
                1: "தயவுசெய்து மரியாதையான மொழியைப் பயன்படுத்தவும். இது உங்கள் முதல் எச்சரிக்கை.",
                2: "நீங்கள் மீண்டும் அநாகரிக மொழியைப் பயன்படுத்தியுள்ளீர்கள். தயவுசெய்து சரிசெய்யவும்.",
                3: "இது உங்கள் இறுதி எச்சரிக்கை. மீண்டும் அநாகரிக மொழி சேவையை நிறுத்திவிடும்.",
                4: "அநாகரிக நடத்தை காரணமாக சேவை நிறுத்தப்படுகிறது."
            },
            "te": {
                1: "దయచేసి మర్యాదగా మాట్లాడండి. ఇది మీ మొదటి హెచ్చరిక.",
                2: "మీరు మళ్లీ అసభ్య భాషను ఉపయోగించారు. దయచేసి సరిచేయండి.",
                3: "ఇది మీ చివరి హెచ్చరిక. మళ్లీ అసభ్య భాష సేవను ఆపేస్తుంది.",
                4: "అసభ్య ప్రవర్తన కారణంగా సేవ నిలిపివేయబడుతోంది."
            },
            "bn": {
                1: "অনুগ্রহ করে ভদ্র ভাষা ব্যবহার করুন। এটি আপনার প্রথম সতর্কবার্তা।",
                2: "আপনি আবার অভদ্র ভাষা ব্যবহার করেছেন। অনুগ্রহ করে সংশোধন করুন।",
                3: "এটি আপনার শেষ সতর্কবার্তা। আবার অভদ্র ভাষা সেবা বন্ধ করে দেবে।",
                4: "অভদ্র আচরণের কারণে সেবা বন্ধ করা হচ্ছে।"
            },
            "gu": {
                1: "કૃપા કરીને સભ્ય ભાષાનો ઉપયોગ કરો. આ તમારી પહેલી ચેતવણી છે.",
                2: "તમે ફરીથી અસભ્ય ભાષાનો ઉપયોગ કર્યો છે. કૃપા કરીને સુધારો.",
                3: "આ તમારી છેલ્લી ચેતવણી છે. ફરીથી અસભ્ય ભાષા સેવા બંધ કરશે.",
                4: "અસભ્ય વર્તણૂકને કારણે સેવા બંધ કરવામાં આવી રહી છે."
            },
            "pa": {
                1: "ਕਿਰਪਾ ਕਰਕੇ ਸਭਿਅਕ ਭਾਸ਼ਾ ਵਰਤੋ। ਇਹ ਤੁਹਾਡੀ ਪਹਿਲੀ ਚੇਤਾਵਨੀ ਹੈ।",
                2: "ਤੁਸੀਂ ਦੁਬਾਰਾ ਅਸਭਿਅਕ ਭਾਸ਼ਾ ਵਰਤੀ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਸੁਧਾਰ ਕਰੋ।",
                3: "ਇਹ ਤੁਹਾਡੀ ਆਖਰੀ ਚੇਤਾਵਨੀ ਹੈ। ਦੁਬਾਰਾ ਅਸਭਿਅਕ ਭਾਸ਼ਾ ਸੇਵਾ ਬੰਦ ਕਰ ਦੇਵੇਗੀ।",
                4: "ਅਸਭਿਅਕ ਵਰਤਾਅ ਕਾਰਨ ਸੇਵਾ ਬੰਦ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ।"
            },
            "kn": {
                1: "ದಯವಿಟ್ಟು ಗೌರವಾನ್ವಿತ ಭಾಷೆಯನ್ನು ಬಳಸಿ. ಇದು ನಿಮ್ಮ ಮೊದಲ ಎಚ್ಚರಿಕೆ.",
                2: "ನೀವು ಮತ್ತೆ ಅಸಭ್ಯ ಭಾಷೆಯನ್ನು ಬಳಸಿದ್ದೀರಿ. ದಯವಿಟ್ಟು ಸರಿಪಡಿಸಿ.",
                3: "ಇದು ನಿಮ್ಮ ಕೊನೆಯ ಎಚ್ಚರಿಕೆ. ಮತ್ತೆ ಅಸಭ್ಯ ಭಾಷೆ ಸೇವೆಯನ್ನು ನಿಲ್ಲಿಸುತ್ತದೆ.",
                4: "ಅಸಭ್ಯ ನಡವಳಿಕೆಯಿಂದಾಗಿ ಸೇವೆ ನಿಲ್ಲಿಸಲಾಗುತ್ತಿದೆ."
            },
            "ml": {
                1: "ദയവായി മാന്യമായ ഭാഷ ഉപയോഗിക്കുക. ഇത് നിങ്ങളുടെ ആദ്യ മുന്നറിയിപ്പാണ്.",
                2: "നിങ്ങൾ വീണ്ടും അസഭ്യ ഭാഷ ഉപയോഗിച്ചു. ദയവായി തിരുത്തുക.",
                3: "ഇത് നിങ്ങളുടെ അവസാന മുന്നറിയിപ്പാണ്. വീണ്ടും അസഭ്യ ഭാഷ സേവനം നിർത്തും.",
                4: "അസഭ്യ പെരുമാറ്റം കാരണം സേവനം നിർത്തുന്നു."
            },
            "or": {
                1: "ଦୟାକରି ଭଦ୍ର ଭାଷା ବ୍ୟବହାର କରନ୍ତୁ। ଏହା ଆପଣଙ୍କ ପ୍ରଥମ ଚେତାବନୀ।",
                2: "ଆପଣ ପୁଣି ଅସଭ୍ୟ ଭାଷା ବ୍ୟବହାର କରିଛନ୍ତି। ଦୟାକରି ସଂଶୋଧନ କରନ୍ତୁ।",
                3: "ଏହା ଆପଣଙ୍କ ଶେଷ ଚେତାବନୀ। ପୁଣି ଅସଭ୍ୟ ଭାଷା ସେବା ବନ୍ଦ କରିବ।",
                4: "ଅସଭ୍ୟ ଆଚରଣ ପାଇଁ ସେବା ବନ୍ଦ କରାଯାଉଛି।"
            }
        }
    
    def detect(self, text: str, session_id: str, language: str = "hi") -> Dict:
        """
        Detect vulgarity in text and return result with warning info.
        Supports both single terms and multi-word phrases.
        
        Returns:
            {
                "detected": bool,
                "matched_terms": List[str],
                "matched_phrases": List[str],
                "severity": str,  # NONE, MILD, MODERATE, SEVERE, EXTREME
                "warning_count": int,
                "should_terminate": bool,
                "warning_message": str,
                "clean_content_ratio": float  # % of text that is NOT vulgar
            }
        """
        text_lower = text.lower()
        matched_terms: Set[str] = set()
        matched_phrases: Set[str] = set()
        
        # 1. Check multi-word phrases FIRST (longer matches take priority)
        for phrase in self.phrases:
            if len(phrase) > 2:  # Skip very short phrases
                # For Devanagari phrases, use direct substring match
                is_devanagari = any(ord(c) > 2304 and ord(c) < 2432 for c in phrase)
                if is_devanagari:
                    if phrase in text_lower:
                        matched_phrases.add(phrase)
                else:
                    # For romanized phrases, more flexible matching
                    if phrase in text_lower:
                        matched_phrases.add(phrase)
        
        # 2. Check single terms
        for term in self.single_terms:
            if len(term) < 2:
                continue  # Skip single-char terms
            # For Devanagari, use substring match (no word boundaries)
            is_devanagari = any(ord(c) > 2304 and ord(c) < 2432 for c in term)
            if is_devanagari:
                if term in text_lower:
                    matched_terms.add(term)
            else:
                # For romanized, use word boundary
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matched_terms.add(term)
        
        # Combine matches (phrases are more severe)
        all_matches = matched_terms | matched_phrases
        detected = len(all_matches) > 0
        
        # Update session warning count
        if detected:
            self.session_warnings[session_id] = self.session_warnings.get(session_id, 0) + 1
        warning_count = self.session_warnings.get(session_id, 0)
        
        # Calculate severity (phrases count double)
        severity = self._calculate_severity(matched_terms, matched_phrases, text)
        
        # Should terminate?
        should_terminate = warning_count >= 4
        
        # Get warning message in appropriate language
        lang_key = language.split('-')[0] if language else "en"  # Handle "hi-IN" format
        if lang_key not in self.warning_messages:
            lang_key = "en"
        warning_num = min(warning_count, 4) if warning_count > 0 else 1
        warning_message = self.warning_messages[lang_key].get(warning_num, self.warning_messages["en"][1])
        
        # Calculate clean content ratio
        words = text.split()
        vulgar_word_count = sum(1 for w in words if any(t in w.lower() for t in all_matches))
        clean_ratio = 1.0 - (vulgar_word_count / max(len(words), 1))
        
        return {
            "detected": detected,
            "matched_terms": list(matched_terms),
            "matched_phrases": list(matched_phrases),
            "severity": severity,
            "warning_count": warning_count,
            "should_terminate": should_terminate,
            "warning_message": warning_message,
            "clean_content_ratio": clean_ratio
        }
    
    def _calculate_severity(self, terms: Set[str], phrases: Set[str], text: str) -> str:
        """Calculate severity - phrases are weighted more heavily."""
        if not terms and not phrases:
            return "NONE"
        
        # Phrases count as 2x severity
        effective_count = len(terms) + (len(phrases) * 2)
        words = text.split()
        density = effective_count / max(len(words), 1)
        
        if effective_count >= 6 or density > 0.35:
            return "EXTREME"
        elif effective_count >= 4 or density > 0.25:
            return "SEVERE"
        elif effective_count >= 2:
            return "MODERATE"
        else:
            return "MILD"

# Global vulgarity detector
vulgarity_detector = VulgarityDetector()

# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE TO STATE INFERENCE + TICKET GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

# Map language codes to likely states (for fallback when location not mentioned)
LANGUAGE_TO_STATE_MAP = {
    "hi": "UP",     # Hindi -> Uttar Pradesh (most Hindi speakers)
    "mr": "MH",     # Marathi -> Maharashtra  
    "bn": "WB",     # Bengali -> West Bengal
    "ta": "TN",     # Tamil -> Tamil Nadu
    "te": "TG",     # Telugu -> Telangana (or AP)
    "kn": "KA",     # Kannada -> Karnataka
    "ml": "KL",     # Malayalam -> Kerala
    "gu": "GJ",     # Gujarati -> Gujarat
    "pa": "PB",     # Punjabi -> Punjab
    "or": "OD",     # Odia -> Odisha
    "as": "AS",     # Assamese -> Assam
    "ur": "UP",     # Urdu -> Uttar Pradesh
    "kok": "GA",    # Konkani -> Goa
    "mai": "BR",    # Maithili -> Bihar
    "bho": "BR",    # Bhojpuri -> Bihar
    "ne": "WB",     # Nepali -> West Bengal (Darjeeling)
    "en": "DL",     # English -> Default to Delhi
}

# State-wise service names for major departments
STATE_SERVICE_NAMES = {
    "MH": {
        "electricity": "Maharashtra State Electricity Distribution Co. (MSEDCL)",
        "water": "Maharashtra Jal Sansthan",
        "municipal": "Municipal Corporation of Greater Mumbai (MCGM)",
        "police": "Maharashtra Police",
        "fire": "Maharashtra Fire Service",
        "agriculture": "Maharashtra Agriculture Department - Kisan Call Centre",
        "scheme": "Maharashtra Social Welfare - Jan Seva Kendra",
        "general": "Maharashtra State Helpline - 181",
    },
    "DL": {
        "electricity": "BSES Yamuna/Rajdhani Power Limited",
        "water": "Delhi Jal Board (DJB)",
        "municipal": "Municipal Corporation of Delhi (MCD)",
        "police": "Delhi Police",
        "fire": "Delhi Fire Service",
        "agriculture": "Delhi Agriculture Department",
        "scheme": "Delhi e-District Portal - Jan Seva Kendra",
        "general": "Delhi Government Helpline - 1031",
    },
    "UP": {
        "electricity": "Uttar Pradesh Power Corporation Ltd. (UPPCL)",
        "water": "UP Jal Nigam",
        "municipal": "Nagar Nigam/Nagar Palika",
        "police": "Uttar Pradesh Police",
        "fire": "UP Fire Service",
        "agriculture": "UP Agriculture Department - Kisan Helpline 1551",
        "scheme": "UP Jan Sewa Kendra / Jan Suvidha Portal",
        "general": "UP State Helpline - 1076",
    },
    "TN": {
        "electricity": "Tamil Nadu Generation and Distribution Corporation (TANGEDCO)",
        "water": "Chennai Metropolitan Water Supply & Sewerage Board",
        "municipal": "Greater Chennai Corporation",
        "police": "Tamil Nadu Police",
        "fire": "Tamil Nadu Fire and Rescue Services",
        "agriculture": "TN Agriculture Department - 1800-425-4000",
        "scheme": "TN e-Sevai Centre",
        "general": "TN State Helpline - 1100",
    },
    "KA": {
        "electricity": "Bangalore Electricity Supply Company (BESCOM)",
        "water": "Bangalore Water Supply & Sewerage Board (BWSSB)",
        "municipal": "Bruhat Bengaluru Mahanagara Palike (BBMP)",
        "police": "Karnataka Police",
        "fire": "Karnataka State Fire and Emergency Services",
        "agriculture": "Karnataka Agriculture Department - 1800-425-1552",
        "scheme": "Karnataka Seva Sindhu Portal",
        "general": "Karnataka State Helpline - 161",
    },
    "GJ": {
        "electricity": "Gujarat Urja Vikas Nigam Ltd. (GUVNL)",
        "water": "Gujarat Water Supply & Sewerage Board",
        "municipal": "Ahmedabad Municipal Corporation",
        "police": "Gujarat Police",
        "fire": "Gujarat Fire and Emergency Services",
        "agriculture": "Gujarat Agriculture Department - Kisan Helpline",
        "scheme": "Gujarat Digital Seva Setu",
        "general": "Gujarat State Helpline - 1800-233-5500",
    },
    "WB": {
        "electricity": "West Bengal State Electricity Distribution Co. (WBSEDCL)",
        "water": "Kolkata Municipal Corporation Water Supply",
        "municipal": "Kolkata Municipal Corporation",
        "police": "West Bengal Police",
        "fire": "West Bengal Fire and Emergency Services",
        "agriculture": "West Bengal Agriculture Department",
        "scheme": "WB Duare Sarkar (Govt at Doorstep)",
        "general": "WB State Helpline - 1800-345-6200",
    },
    "RJ": {
        "electricity": "Jaipur Vidyut Vitran Nigam Ltd. (JVVNL)",
        "water": "Public Health Engineering Department (PHED)",
        "municipal": "Jaipur Nagar Nigam",
        "police": "Rajasthan Police",
        "fire": "Rajasthan Fire Service",
        "agriculture": "Rajasthan Agriculture Department - Kisan Sahayata",
        "scheme": "Rajasthan Jan Soochna Portal",
        "general": "Rajasthan State Helpline - 181",
    },
    "KL": {
        "electricity": "Kerala State Electricity Board (KSEB)",
        "water": "Kerala Water Authority",
        "municipal": "Thiruvananthapuram Corporation",
        "police": "Kerala Police",
        "fire": "Kerala Fire and Rescue Services",
        "agriculture": "Kerala Agriculture Department - Krishi Bhavan",
        "scheme": "Kerala e-Sevana Portal",
        "general": "Kerala State Helpline - 1800-425-1550",
    },
    "TG": {
        "electricity": "Telangana State Southern Power Distribution Co. (TSSPDCL)",
        "water": "Hyderabad Metropolitan Water Supply & Sewerage Board",
        "municipal": "Greater Hyderabad Municipal Corporation (GHMC)",
        "police": "Telangana State Police",
        "fire": "Telangana Fire Services",
        "agriculture": "Telangana Agriculture Department - Rytu Bandhu",
        "scheme": "Telangana MeeSeva Portal",
        "general": "Telangana State Helpline - 040-23450700",
    },
}

# Departments that require ticket generation
TICKET_DEPARTMENTS = {"electricity", "water", "municipal", "sanitation", "roads", "telecom", "gas", "agriculture"}
EMERGENCY_DEPARTMENTS = {"fire", "police", "medical"}
SCHEME_INTENTS = {"scheme_enquiry", "service_enquiry", "agriculture_help"}
# Departments that don't generate tickets
NO_TICKET_DEPARTMENTS = {"scheme", "general"}


def generate_ticket_number(department: str, state: str, session_id: str) -> str:
    """Generate a structured ticket number for tracking complaints."""
    import random
    from datetime import datetime
    
    # Format: DEPT-STATE-YYYYMMDD-XXXXX
    dept_code = department[:3].upper()
    state_code = state.upper() if state else "XX"
    date_code = datetime.now().strftime("%Y%m%d")
    random_code = f"{random.randint(10000, 99999)}"
    
    return f"{dept_code}-{state_code}-{date_code}-{random_code}"


def infer_state_from_language(language: str, detected_state: str = None) -> Tuple[str, str]:
    """
    Infer state from language code or return detected state.
    Returns: (state_code, inference_method)
    """
    if detected_state:
        # Map common state names to codes
        state_mapping = {
            "maharashtra": "MH", "delhi": "DL", "uttar pradesh": "UP",
            "tamil nadu": "TN", "karnataka": "KA", "gujarat": "GJ",
            "west bengal": "WB", "rajasthan": "RJ", "kerala": "KL",
            "telangana": "TG", "andhra pradesh": "AP", "bihar": "BR",
            "madhya pradesh": "MP", "punjab": "PB", "haryana": "HR",
            "odisha": "OD", "assam": "AS", "jharkhand": "JH",
            "chhattisgarh": "CG", "uttarakhand": "UK", "goa": "GA",
            "mumbai": "MH", "pune": "MH", "nashik": "MH",
            "chennai": "TN", "bangalore": "KA", "bengaluru": "KA",
            "hyderabad": "TG", "kolkata": "WB", "jaipur": "RJ",
            "lucknow": "UP", "ahmedabad": "GJ", "surat": "GJ",
        }
        detected_lower = detected_state.lower()
        for name, code in state_mapping.items():
            if name in detected_lower:
                return code, "location_mentioned"
    
    # DO NOT infer state from language; let the AI ask if missing
    return None, "not_provided"


def get_state_service(department: str, state_code: str) -> str:
    """Get the state-specific service name for a department."""
    state_services = STATE_SERVICE_NAMES.get(state_code, STATE_SERVICE_NAMES.get("DL", {}))
    return state_services.get(department, f"{department.title()} Department")


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
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
    else:
        logger.warning("GROQ_API_KEY not set")
except ImportError:
    pass

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


async def generate_groq_response(transcript: str, language: str, urgency: str, intent: str, service_name: str, 
                                  vulgarity_result: Dict = None, ticket_number: str = None,
                                  is_scheme_enquiry: bool = False, state_code: str = None,
                                  department: str = "general", db_scheme_data: dict = None) -> str:
    """
    Generate AI response using Groq in the detected language.
    Handles vulgarity cases with warning response.
    Includes ticket number if generated, or scheme info if scheme enquiry.
    Uses llama-3.3-70b-versatile for better accuracy.
    """
    if not GROQ_AVAILABLE or groq_client_async is None:
        return f"Complaint received: {transcript[:50]}..."
    
    # If vulgarity detected and severe, return warning instead
    if vulgarity_result and vulgarity_result.get("detected"):
        severity = vulgarity_result.get("severity", "MILD")
        if severity in ["SEVERE", "EXTREME"] or vulgarity_result.get("clean_content_ratio", 1.0) < 0.5:
            return vulgarity_result.get("warning_message", "Please use respectful language.")
    
    try:
        lang_config = LANGUAGE_CONFIG.get(language, {})
        lang_name = lang_config.get('name', 'English')
        
        # Pro Helpline Mapping
        HELPLINES = {
            "fire": "101 or 112 (National Emergency)",
            "police": "100 or 112",
            "medical": "102 or 108",
            "women_help": "1091",
            "electricity": "1912 (National Electricity Helpline)",
            "water": "1916 (Municipal Water Supply)",
            "agriculture": "1551 (Kisan Call Center)",
            "scheme": "1076 or 1100 (State CM Helpline)",
            "gas": "1906 (Gas Leak Emergency)",
            "roads": "1073 (Road Accident)",
            "telecom": "198 (Telecom)",
            "general": "1100 or 181"
        }
        active_helpline = HELPLINES.get(department.lower(), "1100 or 181")

        # Build context about ticket or scheme
        ticket_context = f"\nAssigned Helpline: {active_helpline} (CRITICAL: Tell the user to call this number for immediate help)\n"
        if db_scheme_data and db_scheme_data.get("found"):
            schemes = [s.get('name', 'Scheme') for s in db_scheme_data.get("raw_results", [])][:3]
            ticket_context += f"\nRelevant Schemes Found in Database: {', '.join(schemes)}\n"

        if ticket_number:
            ticket_context += f"\nTicket Number: {ticket_number} (Please tell user this ticket number)"
        elif is_scheme_enquiry:
            state_name = {
                "MH": "Maharashtra", "DL": "Delhi", "UP": "Uttar Pradesh", "TN": "Tamil Nadu",
                "KA": "Karnataka", "GJ": "Gujarat", "WB": "West Bengal", "RJ": "Rajasthan",
                "KL": "Kerala", "TG": "Telangana", "AP": "Andhra Pradesh", "PB": "Punjab",
                "BR": "Bihar", "MP": "Madhya Pradesh", "OR": "Odisha", "HR": "Haryana"
            }.get(state_code, "India")
            ticket_context = f"\nThis is a SCHEME ENQUIRY - No ticket needed. User is asking about government schemes in {state_name}."
        
        prompt = f"""You are a helpful FEMALE AI assistant for Indian citizens reporting grievances.
IMPORTANT: You must adopt a feminine persona. Use grammatically feminine constructs in Hindi, Marathi, or any other language (e.g., 'मैं आपकी सहायता करूंगी', NOT 'करूंगा').

IMPORTANT INSTRUCTIONS:
1. Analyze the user's ACTUAL grievance/complaint - what specific problem are they facing?
2. Ignore any filler words, frustration expressions, or mild expletives - focus on the CORE issue
3. If no clear grievance is found (just abuse/nonsense), politely ask them to explain their actual problem
4. If a ticket number is provided, ALWAYS mention it in your response
5. For scheme enquiries, inform them about actual relevant schemes found in the Database Context (if any are listed).
6. ALWAYS state the specific Assigned Helpline number aloud clearly so they know exactly who to call.

User's message: "{transcript}"
Detected Category: {intent}
Urgency Level: {urgency}
Assigned Department: {service_name}{ticket_context}
Language: {lang_name}

Provide a SHORT response (3-4 sentences MAX) in pure {lang_name} that:
1. Acknowledges their SPECIFIC issue with empathy (if a real issue exists)
2. MENTIONS THE TICKET NUMBER clearly if a ticket number is provided, AND state the specific Assigned Helpline number aloud clearly so they know exactly who to call. If the situation is an emergency (fire, medical/ambulance, police), strongly emphasize calling the emergency helpline number immediately as well as keeping the ticket number for reference.
3. Mentions which department/scheme is assigned to help them
4. If the location is required but not provided by the user, explicitly ask them to provide their location using the exact same language.
5. If the user mentions a natural disaster (flood, earthquake, etc.), respond EXACTLY with "we will connect you to a human operator" translated into their native language.

If the message is mostly nonsense/abuse with no clear grievance, politely ask: "Please explain your specific problem clearly so we can help you."

Respond ONLY in {lang_name} script, ensuring the language of your response matches the language of the user exactly. No bullet points, no markdown, just natural speech."""
        
        message = await groq_client_async.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300
        )
        return message.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Groq response generation failed: {e}")
        if ticket_number:
            return f"Your complaint has been registered. Ticket number: {ticket_number}"
        return f"Request registered. Steps are being evaluated."


async def analyze_intent_with_groq(transcript: str, language: str) -> Dict:
    """
    Use Groq LLM to accurately analyze intent, extract actual grievance, and detect abuse.
    Enhanced with: location/state detection, frustration mapping, ticket eligibility check.
    Returns structured analysis result.
    """
    if not GROQ_AVAILABLE or groq_client_async is None:
        return {"intent": "general_complaint", "urgency": "MEDIUM", "has_grievance": True}
    
    try:
        prompt = f"""Analyze this user message for an Indian grievance system. Return JSON only.

Message: "{transcript}"
Language Code: {language}

IMPORTANT: The STT transcription may have errors. Focus on the CORE MEANING, not exact words.
Look for keywords related to: farming, schemes, subsidies, किसान, शेतकरी, योजना, खेती, शेती, etc.

Analyze and return JSON with:
{{
  "has_real_grievance": true/false,    // Is there an actual complaint/problem?
  "is_scheme_enquiry": true/false,     // Is user asking about government schemes/policies/subsidies/किसान योजना/शेतकरी योजना?
  "extracted_grievance": "...",         // The actual problem/query in English (or empty if pure abuse)
  "intent": "...",                      // One of: report_fire, report_flood, report_water_issue, report_electricity, report_road, report_sanitation, report_medical, report_crime, report_corruption, scheme_enquiry, agriculture_help, general_complaint, service_enquiry, abuse_only, clarification_needed
  "urgency": "...",                     // CRITICAL, HIGH, MEDIUM, LOW
  "emotion": "...",                     // angry, frustrated, scared, distressed, calm, neutral
  "frustration_level": 1-10,            // 1=calm, 5=mildly frustrated, 8=very frustrated, 10=extremely angry
  "aggressiveness_score": 0-100,        // How aggressive is the tone? 0=polite, 100=threatening
  "abuse_percentage": 0-100,            // What % of content is abusive/vulgar
  "department": "...",                  // fire, police, water, electricity, roads, sanitation, health, municipal, telecom, agriculture, scheme, general
  "detected_state": "...",              // State/location mentioned (or null if not mentioned)
  "detected_city": "...",               // City/district mentioned (or null)
  "requires_ticket": true/false,        // Should a complaint ticket be generated?
  "ticket_category": "..."              // electricity, water, road, sanitation, fire, police, health, telecom, agriculture, other (or null if no ticket)
}}

RULES:
1. If message contains farming/agriculture words (किसान, खेती, शेतकरी, शेती, farmer, crop) → department="agriculture"
2. If message asks about schemes/योजना/subsidy/policy/pension → is_scheme_enquiry=true, department="scheme", requires_ticket=false
3. If message is MOSTLY abuse (>70%) with NO clear grievance → intent="abuse_only", has_real_grievance=false
4. Fire/flood/medical/ambulance/police emergencies → CRITICAL urgency, requires_ticket=true, ensure department is set to "fire", "medical", or "police" accordingly.
5. Actual infrastructure problems → requires_ticket=true
6. Extract state from text. IMPORTANT: DO NOT ASSUME OR GUESS THE LOCATION. IF THE USER DOES NOT EXPLICITLY MENTION A STATE OR CITY, SET IT TO null.
7. Even if there's some abuse mixed in, extract the CORE query/grievance
8. For scheme enquiries, set department="scheme" NOT "general" or "electricity"

Return ONLY valid JSON, no explanation."""

        message = await groq_client_async.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400
        )
        
        response_text = message.choices[0].message.content.strip()
        # Parse JSON from response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        return json.loads(response_text)
    except Exception as e:
        logger.warning(f"Groq intent analysis failed: {e}")
        return {"intent": "general_complaint", "urgency": "MEDIUM", "has_real_grievance": True, "department": "general"}


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
    print(f"{Colors.CYAN}Ready — speak now (max {duration_s}s, silence cutoff 800ms){Colors.END}")
    
    try:
        vad = VADEngine(aggressiveness=2)
        recorder = Recorder(vad=vad, device_index=None)
        
        audio = recorder.record(
            max_duration_s=duration_s,
            silence_ms=800,
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
    
    recording_result = record_live_audio(duration_s=20)
    if not recording_result:
        return
    audio_file_path, audio_data = recording_result
    
    print_section("📝 STEP 2: STT TRANSCRIPTION & LANGUAGE DETECTION")
    stt = STTProcessor(preferred_provider="groq_whisper")
    await stt.load()
    
    stt_result = await stt.transcribe(audio_file_path, language="auto")
    if not stt_result or not stt_result.text:
        print("  ❌ STT failed")
        return
    
    lang_code = stt_result.detected_language or "hi"
    confidence = stt_result.confidence
    transcript = stt_result.text
    transcript_native = stt_result.native_script_text or transcript
    script = LANGUAGE_CONFIG.get(lang_code, {}).get('script', 'Unknown')
    lang_name = LANGUAGE_CONFIG.get(lang_code, {}).get('name', 'Unknown')
    
    print(f"  {Colors.CYAN}Detected transcript (native script):{Colors.END}")
    print(f"  \"{transcript_native}\"")
    print(f"\n  {Colors.CYAN}Language Detection:{Colors.END}")
    print(f"  • Language: {lang_name} ({lang_code})")
    print(f"  • Script: {script}")
    print(f"  • Confidence: {confidence*100:.1f}%\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2.5: VULGARITY DETECTION (BEFORE NLP) - CRITICAL FIRST CHECK
    # ═══════════════════════════════════════════════════════════════════════════
    print_section("🚨 STEP 2.5: VULGARITY & ABUSE DETECTION")
    
    session_id = create_session_id()
    print(f"  Session ID: {session_id}\n")
    
    vulgarity_result = vulgarity_detector.detect(
        text=transcript_native,
        session_id=session_id,
        language=lang_code
    )
    
    if vulgarity_result["detected"]:
        severity = vulgarity_result["severity"]
        matched = vulgarity_result["matched_terms"][:5]  # Show first 5
        warning_count = vulgarity_result["warning_count"]
        clean_ratio = vulgarity_result["clean_content_ratio"]
        
        print(f"  {Colors.RED}⚠️  VULGARITY DETECTED!{Colors.END}")
        print(f"  • Severity: {Colors.RED}{severity}{Colors.END}")
        print(f"  • Matched Terms: {matched}")
        print(f"  • Warning Count: {warning_count}")
        print(f"  • Clean Content: {clean_ratio*100:.1f}%")
        
        # If mostly abuse (less than 30% clean), handle specially
        if clean_ratio < 0.3 or severity in ["SEVERE", "EXTREME"]:
            print(f"\n  {Colors.RED}❌ Content is primarily abusive - no valid grievance detected{Colors.END}")
            
            # Generate warning response
            print_section("🤖 STEP 3: GENERATING WARNING RESPONSE")
            warning_msg = vulgarity_result["warning_message"]
            print(f"  {Colors.YELLOW}Warning Message ({lang_name}):{Colors.END}")
            print(f"  \"{warning_msg}\"\n")
            
            # TTS the warning
            print_section("🔊 STEP 4: AUDIO WARNING (TTS)")
            session = AWAAZSession(session_id=session_id)
            session.lang = lang_code
            session.lang_name = lang_name
            session.anger_score = 0.0
            session.intent = "abuse_warning"
            session.emotion_name = "neutral"
            session.is_emergency = False
            
            temp_wav = f"/tmp/{session_id}_warning.wav"
            print(f"  [TTS] Synthesizing warning message in {lang_name}...")
            
            base_tts = TTSProcessor(preferred_provider="sarvam")
            success = enhanced_tts(
                text=warning_msg,
                session=session,
                output_path=temp_wav,
                existing_tts=base_tts
            )
            
            if success:
                print(f"  ✓ TTS Generated: {temp_wav}")
                print("  🔊 Playing warning...")
                os.system(f"afplay {temp_wav} 2>/dev/null")
            
            # Save to abuse folder
            print_section("📁 STEP 5: SAVING ABUSE INCIDENT")
            abuse_record = {
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "transcript": transcript_native,
                "language": lang_code,
                "vulgarity": vulgarity_result,
                "action_taken": "warning_issued",
                "warning_count": warning_count
            }
            
            abuse_dir = Path("outputs/json_results/by_abuse")
            abuse_dir.mkdir(parents=True, exist_ok=True)
            abuse_file = abuse_dir / f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(abuse_file, 'w', encoding='utf-8') as f:
                json.dump(abuse_record, f, ensure_ascii=False, indent=2)
            print(f"  ✓ Saved to by_abuse/... {abuse_file.name}")
            
            if vulgarity_result["should_terminate"]:
                print(f"\n  {Colors.RED}🚫 SERVICE TERMINATED - Too many abuse warnings{Colors.END}")
            
            print_header("⚠️ ABUSE DETECTED - NO GRIEVANCE PROCESSED")
            return
        else:
            print(f"\n  {Colors.YELLOW}⚡ Continuing with mild vulgarity - extracting actual grievance...{Colors.END}")
    else:
        print(f"  {Colors.GREEN}✓ No vulgarity detected - proceeding with analysis{Colors.END}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 3: ENHANCED AI ANALYSIS WITH LLM (llama-3.3-70b)
    # ═══════════════════════════════════════════════════════════════════════════
    print_section("🧠 STEP 3: AI ANALYSIS & INTENT DETECTION (llama-3.3-70b)")
    
    # Use LLM for accurate intent analysis
    llm_analysis = await analyze_intent_with_groq(transcript_native, lang_code)
    
    has_grievance = llm_analysis.get("has_real_grievance", True)
    extracted_issue = llm_analysis.get("extracted_grievance", "")
    llm_intent = llm_analysis.get("intent", "general_complaint")
    llm_urgency = llm_analysis.get("urgency", "MEDIUM")
    llm_emotion = llm_analysis.get("emotion", "neutral")
    llm_department = llm_analysis.get("department", "general")
    abuse_pct = llm_analysis.get("abuse_percentage", 0)
    
    # NEW: Extract enhanced fields
    is_scheme_enquiry = llm_analysis.get("is_scheme_enquiry", False)
    frustration_level = llm_analysis.get("frustration_level", 5)
    aggressiveness = llm_analysis.get("aggressiveness_score", 0)
    detected_state = llm_analysis.get("detected_state")
    detected_city = llm_analysis.get("detected_city")
    requires_ticket = llm_analysis.get("requires_ticket", False)
    ticket_category = llm_analysis.get("ticket_category")
    
    # Infer state from language if not detected
    state_code, state_method = infer_state_from_language(lang_code, detected_state)
    
    print(f"  ✓ Has Real Grievance: {Colors.GREEN if has_grievance else Colors.RED}{has_grievance}{Colors.END}")
    if extracted_issue:
        print(f"  ✓ Extracted Issue: {extracted_issue[:100]}...")
    print(f"  ✓ Intent: {llm_intent}")
    print(f"  ✓ Urgency: {llm_urgency}")
    print(f"  ✓ Emotion: {llm_emotion} (Frustration: {frustration_level}/10)")
    print(f"  ✓ Department: {llm_department}")
    print(f"  ✓ Location: {detected_city or 'N/A'}, {detected_state or state_code} ({state_method})")
    print(f"  ✓ Scheme Enquiry: {is_scheme_enquiry}")
    if abuse_pct > 20:
        print(f"  ⚠️  Abuse Content: {abuse_pct}%")
    if aggressiveness > 50:
        print(f"  ⚠️  Aggressiveness: {aggressiveness}%")
    
    # Adjust urgency based on frustration/aggressiveness
    if frustration_level >= 8 or aggressiveness >= 70:
        urgency_boost = {"LOW": "MEDIUM", "MEDIUM": "HIGH", "HIGH": "CRITICAL"}
        if llm_urgency in urgency_boost:
            llm_urgency = urgency_boost[llm_urgency]
            print(f"  ⚡ Urgency boosted to {llm_urgency} due to high frustration/aggressiveness")
    
    # If LLM says abuse_only, handle it
    if llm_intent == "abuse_only" or not has_grievance:
        print(f"\n  {Colors.YELLOW}⚠️ LLM detected no valid grievance - asking for clarification{Colors.END}")
        clarification_msg = {
            "hi": "कृपया अपनी समस्या स्पष्ट रूप से बताएं ताकि हम आपकी मदद कर सकें।",
            "mr": "कृपया तुमची समस्या स्पष्टपणे सांगा जेणेकरून आम्ही तुम्हाला मदत करू शकू.",
            "en": "Please explain your problem clearly so we can help you."
        }.get(lang_code, "Please explain your problem clearly.")
        
        llm_intent = "clarification_needed"
        llm_urgency = "LOW"
        llm_department = "general"
        requires_ticket = False
    
    # Handle scheme enquiry separately (no ticket)
    scheme_classification = None
    if is_scheme_enquiry:
        print(f"\n  {Colors.CYAN}📋 SCHEME ENQUIRY DETECTED - Classifying Scheme{Colors.END}")
        requires_ticket = False
        llm_intent = "scheme_enquiry"
        try:
            scheme_classification = await classify_scheme_async(transcript) 
            print(f"  ✓ Scheme Domain: {', '.join(scheme_classification.get('domain', []))}")
            if scheme_classification.get('scheme_name'):
                print(f"  ✓ Scheme Name: {scheme_classification.get('scheme_name')}")
        except Exception as e:
            print(f"  ⚠️ Scheme classification failed: {e}")
    
    # Also run traditional analytical model for comparison
    analytical_model = processor.process_grievance(
        session_id=session_id,
        transcript=transcript_native,
        audio_data=audio_data,
        sample_rate=TARGET_SR,
        detected_language=lang_code,
        state=state_code.lower() if state_code else "maharashtra",
    )
    
    # Override with LLM results if available (LLM is more accurate)
    if llm_intent != "general_complaint":
        analytical_model.intent.primary_intent = llm_intent
    
    # CRITICAL: Always use LLM department for scheme/agriculture detection
    # The traditional analytical model doesn't understand these categories well
    if llm_department in ["scheme", "agriculture", "general"]:
        analytical_model.routing.primary_department = llm_department
    elif llm_department and llm_department != "general":
        analytical_model.routing.primary_department = llm_department
    
    # Use the more severe urgency
    urgency_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    traditional_urgency = analytical_model.intent.urgency_level.name if analytical_model.intent.urgency_level else "MEDIUM"
    if urgency_map.get(llm_urgency, 2) > urgency_map.get(traditional_urgency, 2):
        urgency_level = llm_urgency
    else:
        urgency_level = traditional_urgency
    
    print(f"\n  {Colors.CYAN}Final Analysis:{Colors.END}")
    print(f"  • Intent: {analytical_model.intent.primary_intent}")
    print(f"  • Urgency: {urgency_level}")
    print(f"  • Emotion: {analytical_model.emotion.detected_emotion.name}")
    print(f"  • Anger Score: {analytical_model.emotion.anger_score:.2f}")
    if hasattr(analytical_model, 'ai_summary'):
        print(f"  • AI Summary: {analytical_model.ai_summary}\n")
    else:
        print("\n")
    
    print_section("🚦 STEP 4: INTELLIGENT ROUTING & ESCALATION")
    
    # Set department before routing - LLM department takes priority
    final_department = llm_department if llm_department else analytical_model.routing.primary_department
    analytical_model.routing.primary_department = final_department
    
    analytical_model, escalation_info = processor.apply_routing_and_escalation(
        analytical_model,
        transcript=transcript_native,
        time_since_filing_minutes=0,
        num_previous_calls=0,
    )
    
    # Get state-specific service name
    final_department = analytical_model.routing.primary_department
    state_service = get_state_service(final_department, state_code)
    
    # Override service name with state-specific one
    if analytical_model.routing.mapped_service:
        service_mapped = state_service
    else:
        service_mapped = state_service
        
    print(f"  ✓ Department: {Colors.CYAN}{final_department.upper()}{Colors.END}")
    print(f"  ✓ Priority: P{analytical_model.routing.priority_level}")
    print(f"  ✓ Service: {service_mapped}")
    print(f"  ✓ State: {state_code}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 4b: TICKET GENERATION (only for actual problems)
    # ═══════════════════════════════════════════════════════════════════════════
    ticket_number = None
    if requires_ticket and not is_scheme_enquiry:
        print_section("🎫 STEP 4b: TICKET GENERATION")
        ticket_number = generate_ticket_number(final_department, state_code, session_id)
        print(f"  ✓ Ticket Generated: {Colors.GREEN}{ticket_number}{Colors.END}")
        print(f"  • Department: {final_department.upper()}")
        print(f"  • State: {state_code}")
        print(f"  • Priority: P{analytical_model.routing.priority_level}")
        print(f"  • Status: OPEN")
    elif is_scheme_enquiry:
        print_section("📋 STEP 4b: SCHEME LOOKUP")
        print(f"  ℹ️  No ticket generated - this is a scheme enquiry")
        print(f"  • Looking up schemes for state: {state_code}")
    else:
        print_section("📌 STEP 4b: TICKET STATUS")
        print(f"  ℹ️  No ticket generated for intent: {llm_intent}")
    
    print_section("🤖 STEP 5: GROQ AI RESPONSE (STEPS & SCHEME IN NATIVE LANGUAGE)")
    # Fetch DB Schemes Dynamically
    db_scheme_data = None
    if is_scheme_enquiry and scheme_classification:
        if isinstance(scheme_classification, dict):
            print(f"  🔍 Querying Neon Database for exact schemes matching domains...")
            try:
                db_scheme_data = fetch_schemes_from_neon(
                    domain=scheme_classification.get("domain", []),
                    beneficiary_groups=scheme_classification.get("beneficiary_groups", [])
                )
                if db_scheme_data and db_scheme_data.get("found"):
                    print(f"  ✓ Database match: Found {len(db_scheme_data.get('raw_results', []))} specific schemes via Neon DB.")
            except Exception as e:
                print(f"  ⚠️ Database fetch failed: {e}")

    groq_response = await generate_groq_response(
        transcript_native,
        lang_code,
        urgency_level,
        analytical_model.intent.primary_intent,
        service_mapped,
        vulgarity_result=vulgarity_result,
        ticket_number=ticket_number,
        is_scheme_enquiry=is_scheme_enquiry,
        state_code=state_code,
        department=final_department,
        db_scheme_data=db_scheme_data
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
    
    print(f"  [TTS] Synthesizing human-like voice (Ritu) for {lang_name} using Sarvam AI...")
    
    # Initialize base_tts preferring sarvam for smooth "Ritu" voice
    base_tts = TTSProcessor(preferred_provider="sarvam")
    
    success = enhanced_tts(
        text=groq_response,
        session=session,
        output_path=temp_wav,
        existing_tts=base_tts
    )
    
    if success:
        print(f"  ✓ TTS Generated successfully: {temp_wav}")
        print("  🔊 Playing audio response...")
        os.system(f"afplay {temp_wav} 2>/dev/null")
    else:
        print(f"  ❌ [ERROR] TTS synthesis failed")
    
    print_section("📁 STEP 7: ORGANIZED JSON STORAGE")
    
    # Add enhanced fields to the model before saving
    enhanced_data = {
        "ticket_number": ticket_number,
        "state_code": state_code,
        "state_service": service_mapped,
        "is_scheme_enquiry": is_scheme_enquiry,
        "scheme_classification": scheme_classification,
        "frustration_level": frustration_level,
        "aggressiveness_score": aggressiveness,
        "ai_response": groq_response
    }
    
    saved_paths = processor.save_result_organized(analytical_model, escalation_info=escalation_info, 
                                                   extra_data=enhanced_data)
    print(f"  ✓ Saved to by_urgency/{urgency_level}/... {saved_paths['by_urgency'].split('/')[-1]}")
    print(f"  ✓ Saved to by_department/{analytical_model.routing.primary_department}/... {saved_paths['by_department'].split('/')[-1]}")
    
    # Show ticket number prominently
    if ticket_number:
        print(f"\n  {Colors.GREEN}🎫 TICKET NUMBER: {ticket_number}{Colors.END}")
    
    # Show vulgarity warning count if any
    if vulgarity_result["warning_count"] > 0:
        print(f"\n  {Colors.YELLOW}⚠️ User has {vulgarity_result['warning_count']} abuse warning(s){Colors.END}")
    
    print_header("✅ SYSTEM OPERATING PERFECTLY")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  Interrupted{Colors.END}\n")
