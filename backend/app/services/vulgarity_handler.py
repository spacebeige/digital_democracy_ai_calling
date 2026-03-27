"""
Vulgarity Detection & Warning System
Detects profanity across all supported languages and issues warnings before service termination.
"""

import json
import logging
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class VulgarityLevel(str, Enum):
    """Severity levels for detected vulgarity."""
    NONE = "NONE"
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    EXTREME = "EXTREME"


class WarningLevel(int, Enum):
    """Warning levels before service termination."""
    FIRST_WARNING = 1
    SECOND_WARNING = 2
    FINAL_WARNING = 3
    TERMINATED = 4


class VulgarityResponse(BaseModel):
    """Structured response for vulgarity detection."""
    detected: bool
    level: VulgarityLevel
    matched_terms: List[str]
    warning_count: int
    warning_level: WarningLevel
    should_terminate: bool
    response_message: Dict[str, str]  # language: message


class VulgarityHandler:
    """Handles vulgarity detection across all supported languages with progressive warnings."""
    
    def __init__(self, keywords_path: Optional[Path] = None):
        """Initialize vulgarity handler with keyword lexicon."""
        self.keywords_path = keywords_path or Path(__file__).parent / "emergency_keywords.json"
        self.vulgarity_lexicon: Dict[str, List[str]] = {}
        self.session_warnings: Dict[str, int] = {}  # session_id: warning_count
        self._load_keywords()
        
        # Warning response templates (multilingual)
        self.warning_templates = self._init_warning_templates()
    
    def _load_keywords(self):
        """Load vulgarity keywords from JSON config."""
        try:
            with open(self.keywords_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.vulgarity_lexicon = data.get("abuse_toxicity", {})
                logger.info(f"Loaded vulgarity keywords: {sum(len(v) for v in self.vulgarity_lexicon.values())} terms")
        except Exception as e:
            logger.error(f"Failed to load vulgarity keywords: {e}")
            self.vulgarity_lexicon = {"hindi": [], "english": [], "universal": []}
    
    def _init_warning_templates(self) -> Dict[str, Dict[int, str]]:
        """Initialize warning message templates for each language."""
        return {
            "hi": {
                1: "कृपया शिष्ट भाषा का प्रयोग करें। असभ्य भाषा स्वीकार्य नहीं है। यह आपकी पहली चेतावनी है।",
                2: "दूसरी बार असभ्य भाषा का उपयोग किया गया है। कृपया तुरंत सुधार करें, अन्यथा सेवा बंद की जाएगी।",
                3: "अंतिम चेतावनी। अगली बार असभ्य भाषा का प्रयोग करने पर सेवा तुरंत समाप्त कर दी जाएगी।",
                4: "सेवा समाप्त की जा रही है। बार-बार असभ्य भाषा के उपयोग के कारण आपकी शिकायत दर्ज नहीं की जा सकती।"
            },
            "en": {
                1: "Please use respectful language. Abusive language is not acceptable. This is your first warning.",
                2: "Abusive language detected again. Please correct your behavior immediately, or service will be terminated.",
                3: "Final warning. Any further use of abusive language will result in immediate service termination.",
                4: "Service terminated due to repeated use of abusive language. Your complaint cannot be processed."
            },
            "mr": {
                1: "कृपया सभ्य भाषा वापरा। असभ्य भाषा मान्य नाही. ही तुमची पहिली चेतावणी आहे।",
                2: "पुन्हा असभ्य भाषा आढळली. कृपया ताबडतोब सुधारणा करा, अन्यथा सेवा बंद केली जाईल।",
                3: "अंतिम चेतावणी. पुढील असभ्य भाषेमुळे सेवा तात्काळ बंद केली जाईल।",
                4: "वारंवार असभ्य भाषेमुळे सेवा बंद केली जात आहे। तुमची तक्रार नोंदवली जाऊ शकत नाही।"
            },
            "ta": {
                1: "மரியாதையான மொழியைப் பயன்படுத்தவும். தவறான மொழி ஏற்றுக்கொள்ளப்படாது. இது உங்கள் முதல் எச்சரிக்கை.",
                2: "மீண்டும் தவறான மொழி கண்டறியப்பட்டது. உடனடியாக சரிசெய்யுங்கள், இல்லையெனில் சேவை நிறுத்தப்படும்.",
                3: "இறுதி எச்சரிக்கை. மேலும் தவறான மொழி பயன்படுத்தினால் சேவை உடனடியாக நிறுத்தப்படும்.",
                4: "மீண்டும் மீண்டும் தவறான மொழியால் சேவை நிறுத்தப்படுகிறது। உங்கள் புகார் பதிவு செய்ய முடியாது."
            },
            "te": {
                1: "దయచేసి మర్యాదపూర్వక భాషను ఉపయోగించండి. దురుసు భాష ఆమోదయోగ్యం కాదు. ఇది మీ మొదటి హెచ్చరిక.",
                2: "మళ్లీ దురుసు భాష గుర్తించబడింది. వెంటనే సరిదిద్దుకోండి, లేకపోతే సేవ నిలిపివేయబడుతుంది.",
                3: "చివరి హెచ్చరిక. మరింత దురుసు భాష ఉపయోగిస్తే సేవ వెంటనే నిలిపివేయబడుతుంది.",
                4: "పదే పదే దురుసు భాష వాడటం వల్ల సేవ నిలిపివేయబడుతోంది। మీ ఫిర్యాదు నమోదు చేయలేము."
            },
            "bn": {
                1: "অনুগ্রহ করে সম্মানজনক ভাষা ব্যবহার করুন। অসভ্য ভাষা গ্রহণযোগ্য নয়। এটি আপনার প্রথম সতর্কতা।",
                2: "আবার অসভ্য ভাষা সনাক্ত করা হয়েছে। অবিলম্বে সংশোধন করুন, নইলে পরিষেবা বন্ধ করা হবে।",
                3: "চূড়ান্ত সতর্কতা। আরও অসভ্য ভাষা ব্যবহারে পরিষেবা অবিলম্বে বন্ধ করা হবে।",
                4: "বারবার অসভ্য ভাষার কারণে পরিষেবা বন্ধ করা হচ্ছে। আপনার অভিযোগ নথিভুক্ত করা যাবে না।"
            },
            "gu": {
                1: "કૃપા કરીને આદરપૂર્વક ભાષાનો ઉપયોગ કરો. અસભ્ય ભાષા સ્વીકાર્ય નથી. આ તમારી પ્રથમ ચેતવણી છે.",
                2: "ફરીથી અસભ્ય ભાષા શોધાઈ. તુરંત સુધારો કરો, નહીતર સેવા બંધ કરવામાં આવશે.",
                3: "અંતિમ ચેતવણી. વધુ અસભ્ય ભાષા ઉપયોગથી સેવા તુરંત બંધ થશે.",
                4: "વારંવાર અસભ્ય ભાષાના કારણે સેવા બંધ કરવામાં આવી રહી છે. તમારી ફરિયાદ નોંધી શકાતી નથી."
            },
            "kn": {
                1: "ದಯವಿಟ್ಟು ಗೌರವಯುತ ಭಾಷೆ ಬಳಸಿ. ಅವಹೇಳನಕಾರಿ ಭಾಷೆ ಸ್ವೀಕಾರಾರ್ಹವಲ್ಲ. ಇದು ನಿಮ್ಮ ಮೊದಲ ಎಚ್ಚರಿಕೆ.",
                2: "ಮತ್ತೆ ಅವಹೇಳನಕಾರಿ ಭಾಷೆ ಪತ್ತೆಯಾಗಿದೆ. ತಕ್ಷಣ ಸರಿಪಡಿಸಿ, ಇಲ್ಲದಿದ್ದರೆ ಸೇವೆ ನಿಲ್ಲಿಸಲಾಗುವುದು.",
                3: "ಅಂತಿಮ ಎಚ್ಚರಿಕೆ. ಮತ್ತಷ್ಟು ಅವಹೇಳನಕಾರಿ ಭಾಷೆ ಬಳಕೆಯಿಂದ ಸೇವೆ ತಕ್ಷಣ ನಿಲ್ಲಿಸಲಾಗುವುದು.",
                4: "ಪದೇ ಪದೇ ಅವಹೇಳನಕಾರಿ ಭಾಷೆಯಿಂದಾಗಿ ಸೇವೆ ನಿಲ್ಲಿಸಲಾಗುತ್ತಿದೆ. ನಿಮ್ಮ ದೂರು ದಾಖಲಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ."
            },
            "ml": {
                1: "ദയവായി മര്യാദയുള്ള ഭാഷ ഉപയോഗിക്കുക. അസഭ്യ ഭാഷ സ്വീകാര്യമല്ല. ഇത് നിങ്ങളുടെ ആദ്യ മുന്നറിയിപ്പാണ്.",
                2: "വീണ്ടും അസഭ്യ ഭാഷ കണ്ടെത്തി. ഉടനടി തിരുത്തുക, അല്ലെങ്കിൽ സേവനം നിർത്തും.",
                3: "അവസാന മുന്നറിയിപ്പ്. കൂടുതൽ അസഭ്യ ഭാഷ ഉപയോഗിച്ചാൽ സേവനം ഉടൻ നിർത്തും.",
                4: "ആവർത്തിച്ചുള്ള അസഭ്യ ഭാഷ കാരണം സേവനം നിർത്തുന്നു. നിങ്ങളുടെ പരാതി രജിസ്റ്റർ ചെയ്യാൻ കഴിയില്ല."
            },
            "pa": {
                1: "ਕਿਰਪਾ ਕਰਕੇ ਸਤਿਕਾਰ ਭਾਸ਼ਾ ਵਰਤੋ। ਅਸਭਿਆਚਾਰਕ ਭਾਸ਼ਾ ਮਨਜ਼ੂਰ ਨਹੀਂ। ਇਹ ਤੁਹਾਡੀ ਪਹਿਲੀ ਚੇਤਾਵਨੀ ਹੈ।",
                2: "ਦੁਬਾਰਾ ਅਸਭਿਆਚਾਰਕ ਭਾਸ਼ਾ ਪਾਈ ਗਈ। ਤੁਰੰਤ ਸੁਧਾਰੋ, ਨਹੀਂ ਤਾਂ ਸੇਵਾ ਬੰਦ ਕੀਤੀ ਜਾਵੇਗੀ।",
                3: "ਆਖਰੀ ਚੇਤਾਵਨੀ। ਹੋਰ ਅਸਭਿਆਚਾਰਕ ਭਾਸ਼ਾ ਨਾਲ ਸੇਵਾ ਤੁਰੰਤ ਬੰਦ ਹੋ ਜਾਵੇਗੀ।",
                4: "ਵਾਰ-ਵਾਰ ਅਸਭਿਆਚਾਰਕ ਭਾਸ਼ਾ ਕਰਕੇ ਸੇਵਾ ਬੰਦ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ। ਤੁਹਾਡੀ ਸ਼ਿਕਾਇਤ ਦਰਜ ਨਹੀਂ ਹੋ ਸਕਦੀ।"
            }
        }
    
    def detect_vulgarity(
        self,
        text: str,
        language: str = "en",
        session_id: str = None
    ) -> VulgarityResponse:
        """
        Detect vulgarity in text using lexicon-based matching.
        
        Args:
            text: Input text to analyze
            language: Detected language code
            session_id: Session identifier for tracking warnings
        
        Returns:
            VulgarityResponse with detection results and appropriate warning
        """
        text_lower = text.lower()
        matched_terms: Set[str] = set()
        
        # Check all lexicon categories
        for category, terms in self.vulgarity_lexicon.items():
            for term in terms:
                # Use word boundary matching to avoid false positives
                pattern = r'\b' + re.escape(term.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    matched_terms.add(term)
        
        detected = len(matched_terms) > 0
        
        # Determine severity level based on number and type of matches
        level = self._calculate_severity(matched_terms)
        
        # Track warnings per session
        warning_count = 0
        if session_id:
            if detected:
                self.session_warnings[session_id] = self.session_warnings.get(session_id, 0) + 1
            warning_count = self.session_warnings.get(session_id, 0)
        
        # Determine warning level
        warning_level = self._get_warning_level(warning_count)
        should_terminate = warning_level == WarningLevel.TERMINATED
        
        # Generate multilingual response
        response_message = self._generate_response(language, warning_count, should_terminate)
        
        return VulgarityResponse(
            detected=detected,
            level=level,
            matched_terms=list(matched_terms),
            warning_count=warning_count,
            warning_level=warning_level,
            should_terminate=should_terminate,
            response_message=response_message
        )
    
    def _calculate_severity(self, matched_terms: Set[str]) -> VulgarityLevel:
        """Calculate severity based on matched terms."""
        if not matched_terms:
            return VulgarityLevel.NONE
        
        count = len(matched_terms)
        
        # Check for severe/universal threats
        universal_threats = set(self.vulgarity_lexicon.get("universal", []))
        severe_matches = matched_terms.intersection(universal_threats)
        
        if severe_matches or count >= 5:
            return VulgarityLevel.EXTREME
        elif count >= 3:
            return VulgarityLevel.SEVERE
        elif count >= 2:
            return VulgarityLevel.MODERATE
        else:
            return VulgarityLevel.MILD
    
    def _get_warning_level(self, warning_count: int) -> WarningLevel:
        """Map warning count to warning level."""
        if warning_count == 0:
            return WarningLevel.FIRST_WARNING
        elif warning_count == 1:
            return WarningLevel.FIRST_WARNING
        elif warning_count == 2:
            return WarningLevel.SECOND_WARNING
        elif warning_count == 3:
            return WarningLevel.FINAL_WARNING
        else:
            return WarningLevel.TERMINATED
    
    def _generate_response(
        self,
        language: str,
        warning_count: int,
        should_terminate: bool
    ) -> Dict[str, str]:
        """Generate appropriate warning response in multiple languages."""
        # Default to English if language not supported
        supported_langs = ["hi", "en", "mr", "ta", "te", "bn", "gu", "kn", "ml", "pa"]
        primary_lang = language if language in supported_langs else "en"
        
        warning_num = min(warning_count + 1, 4) if not should_terminate else 4
        
        # Return message in detected language + English fallback
        return {
            primary_lang: self.warning_templates.get(primary_lang, self.warning_templates["en"])[warning_num],
            "en": self.warning_templates["en"][warning_num]
        }
    
    def reset_session_warnings(self, session_id: str):
        """Reset warning count for a session (e.g., after successful resolution)."""
        if session_id in self.session_warnings:
            del self.session_warnings[session_id]
    
    def get_session_status(self, session_id: str) -> Dict[str, any]:
        """Get current warning status for a session."""
        warning_count = self.session_warnings.get(session_id, 0)
        warning_level = self._get_warning_level(warning_count)
        
        return {
            "session_id": session_id,
            "warning_count": warning_count,
            "warning_level": warning_level.name,
            "warnings_remaining": max(0, 3 - warning_count),
            "is_terminated": warning_level == WarningLevel.TERMINATED
        }
