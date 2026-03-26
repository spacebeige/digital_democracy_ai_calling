"""
NLP Routing Module - Intent Classification & Urgency Analysis
==============================================================
Classifies user intent and urgency level using:
- Keyword matching (critical, high, medium, low)
- Pattern recognition
- Regional language support
- Confidence scoring based on evidence
"""

from typing import Tuple, List, Dict
from models.grievance_models import (
    IntentClassification, 
    UrgencyLevel,
    ConfidenceMetric,
)
from external_services.gov_services_map import (
    SERVICE_KEYWORDS,
    detect_service_type,
)


# ─────────────────────────────────────────────────────────────────
# URGENCY KEYWORDS DATABASE
# ─────────────────────────────────────────────────────────────────

URGENCY_KEYWORDS = {
    "CRITICAL": {
        "hindi": [
            "आग", "आग लगी", "fire", "आग लगो", "आग है", "emergency", 
            "तुरंत", "मदद", "बचाओ", "बचा लो", "मदद करो",
            "जान का खतरा", "घायल", "खून", "accident", "दुर्घटना",
            "मेरी जान", "ट्रैप", "फंस रहा हूं", "help", "sos",
            "dying", "dead", "severe injury"
        ],
        "english": [
            "fire", "emergency", "urgent", "critical", "danger", "help", 
            "911", "dying", "severe", "accident", "bleeding", "unconscious",
            "dead", "police", "attack", "shot", "madad", "save me",
            "rescue", "help immediately"
        ],
        "marathi": [
            "आग", "आग लगली", "मदत", "मदत करा", "बचव", "तुरंत",
            "गंभीर", "दुर्घटना", "जिवाचा धोका"
        ],
    },
    "HIGH": {
        "hindi": [
            "बिजली गई", "बिजली नहीं", "नहीं आ रही", "बिजली निकल गई",
            "पानी नहीं", "नल से पानी नहीं", "पानी समस्या",
            "चोर", "चोरी", "डाका", "गायब", "खो गया",
            "अस्पताल", "बीमार", "बहुत बीमार", "दर्द", "बहुत दर्द",
            "तकलीफ", "गंभीर", "खतरनाक", "जरूरी", "समस्या है"
        ],
        "english": [
            "no electricity", "power cut", "outage", "no water",
            "theft", "robbery", "missing", "lost",
            "hospital", "sick", "illness", "pain", "medical",
            "serious", "urgent care", "bleeding", "injury"
        ],
        "marathi": [
            "विजा नाही", "वीज गेली", "पाणी नाही", "नाळ सुकली",
            "चोरी", "हल्ला", "बीमारी", "दुखापल",
            "गंभीर", "जरूरी"
        ],
    },
    "MEDIUM": {
        "hindi": [
            "तोड़ा", "तोड़", "खराब", "नहीं काम कर रहा", "काम नहीं",
            "समस्या", "issue", "गड्ढा", "गड्ढे", "टूटा-फूटा",
            "सड़क", "गली", "पार्क", "बस", "ट्रेन",
            "कूड़ा", "कचरा", "साफ सफाई", "गंदा", "प्रदूषण"
        ],
        "english": [
            "broken", "damage", "damaged", "not working",
            "problem", "issue", "pothole", "broken",
            "road", "street", "garbage", "trash", "dirt",
            "maintenance needed"
        ],
        "marathi": [
            "तुटले", "खराब", "काम करत नाही", "समस्या",
            "खड्डा", "रस्ता", "कचरा", "घाण"
        ],
    },
    "LOW": {
        "hindi": [
            "सुझाव", "सुझाव दूं", "शिकायत", "पूछना", "पूछ रहा हूं",
            "जानकारी", "जानना चाहता हूं", "आवेदन", "फॉर्म",
            "स्थिति", "कब", "कहाँ", "क्या", "कैसे", "कौन"
        ],
        "english": [
            "suggestion", "complaint", "question", "information",
            "application", "status", "when", "where", "what", "how", "why",
            "form", "process", "feedback"
        ],
        "marathi": [
            "सूचना", "प्रश्न", "माहिती", "शिकायत",
            "कधी", "कुठे", "काय", "कसे"
        ],
    },
}

# Pattern-based intent mapping
INTENT_PATTERNS = {
    "report_fire": {
        "keywords": ["आग", "fire"],
        "urgency": UrgencyLevel.CRITICAL,
        "service": "fire",
    },
    "report_injury": {
        "keywords": ["घायल", "bleeding", "bleeding badly", "injury"],
        "urgency": UrgencyLevel.CRITICAL,
        "service": "police",
    },
    "electricity_issue": {
        "keywords": ["बिजली", "electricity", "power"],
        "urgency": UrgencyLevel.HIGH,
        "service": "electricity",
    },
    "water_issue": {
        "keywords": ["पानी", "water", "tap"],
        "urgency": UrgencyLevel.HIGH,
        "service": "water",
    },
    "gas_leak": {
        "keywords": ["गैस", "gas"],
        "urgency": UrgencyLevel.HIGH,
        "service": "gas",
    },
    "theft_report": {
        "keywords": ["चोर", "theft", "stolen"],
        "urgency": UrgencyLevel.HIGH,
        "service": "police",
    },
    "infrastructure_damage": {
        "keywords": ["गड्ढा", "pothole", "सड़क", "road"],
        "urgency": UrgencyLevel.MEDIUM,
        "service": "municipal",
    },
    "general_complaint": {
        "keywords": ["शिकायत", "complaint"],
        "urgency": UrgencyLevel.LOW,
        "service": "general",
    },
}


def classify_urgency(
    transcript: str,
    keywords_found: List[str] = None,
    emotion_score: float = 0.0,
) -> Tuple[UrgencyLevel, List[str], float]:
    """
    Classify urgency level using keyword matching and patterns.
    
    Args:
        transcript: User's spoken/typed complaint
        keywords_found: Optional pre-identified keywords
        emotion_score: 0-1 anger/stress score from voice analysis
        
    Returns:
        (urgency_level, matched_keywords, confidence_0_to_1)
    """
    text_lower = transcript.lower()
    found_keywords = keywords_found if keywords_found else []
    
    # Keyword matching for each urgency level
    keyword_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    matched_keywords = []
    
    for urgency_level, keywords_dict in URGENCY_KEYWORDS.items():
        all_keywords = (
            keywords_dict.get("hindi", []) +
            keywords_dict.get("english", []) +
            keywords_dict.get("marathi", [])
        )
        
        for keyword in all_keywords:
            keyword_lower = keyword.lower()
            # Check for keyword in transcript or in already-found keywords
            if keyword_lower in text_lower or keyword in found_keywords:
                keyword_counts[urgency_level] += 1
                if keyword not in matched_keywords:
                    matched_keywords.append(keyword)
    
    # Determine urgency level
    if keyword_counts["CRITICAL"] >= 1:
        urgency = UrgencyLevel.CRITICAL
        confidence = 0.95 if keyword_counts["CRITICAL"] >= 2 else 0.80
    elif keyword_counts["HIGH"] >= 1:
        urgency = UrgencyLevel.HIGH
        confidence = 0.80 if keyword_counts["HIGH"] >= 2 else 0.60
    elif keyword_counts["MEDIUM"] >= 2:
        urgency = UrgencyLevel.MEDIUM
        confidence = 0.70
    else:
        urgency = UrgencyLevel.LOW
        confidence = 0.50
    
    # Boost confidence if emotion score matches urgency
    if emotion_score > 0.7 and urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        confidence = min(0.99, confidence + 0.15)
    elif emotion_score > 0.5 and urgency == UrgencyLevel.MEDIUM:
        confidence = min(0.95, confidence + 0.10)
    
    return urgency, matched_keywords, confidence


def classify_intent(
    transcript: str,
    urgency_level: UrgencyLevel,
    matched_keywords: List[str],
    detected_language: str = "en",
) -> IntentClassification:
    """
    Classify user intent and generate confidence metrics.
    
    Args:
        transcript: User's complaint
        urgency_level: Detected urgency from keyword analysis
        matched_keywords: Keywords found in transcript
        detected_language: ISO language code (en, hi, mr, etc.)
        
    Returns:
        IntentClassification with detailed reasoning
    """
    text_lower = transcript.lower()
    
    # Detect service type from transcript
    service_type, service_keywords, _ = detect_service_type(
        transcript,
        matched_keywords,
    )
    
    # Find best matching intent pattern
    primary_intent = "general_complaint"
    secondary_intents = []
    
    for intent_name, pattern in INTENT_PATTERNS.items():
        pattern_keywords = pattern.get("keywords", [])
        keyword_matches = sum(1 for kw in pattern_keywords if kw.lower() in text_lower)
        
        if keyword_matches > 0:
            secondary_intents.append(intent_name)
            if len(secondary_intents) == 1:
                primary_intent = intent_name
    
    # Calculate confidence components
    keyword_match_score = min(1.0, len(matched_keywords) / 3)  # Normalize to 0-1
    urgency_consistency_score = 0.8 if urgency_level != UrgencyLevel.LOW else 0.5
    pattern_match_score = 0.7 if primary_intent != "general_complaint" else 0.4
    emotion_alignment_score = 0.6 if urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH] else 0.4
    
    # Get confidence score
    confidence_score, confidence_reason = ConfidenceMetric.calculate(
        keyword_match=keyword_match_score,
        urgency_consistency=urgency_consistency_score,
        pattern_match=pattern_match_score,
        emotion_alignment=emotion_alignment_score,
    )
    
    # Get urgency score from keyword analysis
    _, _, urgency_confidence = classify_urgency(transcript, matched_keywords)
    urgency_score = int(urgency_confidence * 4)
    
    return IntentClassification(
        primary_intent=primary_intent,
        secondary_intents=secondary_intents,
        urgency_level=urgency_level,
        urgency_score=urgency_score,
        confidence=confidence_score,
        confidence_reason=confidence_reason,
        matched_keywords=matched_keywords,
    )


def create_ai_summary(
    transcript: str,
    intent: IntentClassification,
    matched_keywords: List[str],
    urgency_level: UrgencyLevel,
) -> str:
    """
    Create a brief AI summary of the grievance.
    
    Args:
        transcript: Original user transcript
        intent: Intent classification
        matched_keywords: Found keywords
        urgency_level: Detected urgency
        
    Returns:
        Brief summary string (1-2 sentences)
    """
    # Determine main issue from keywords
    main_issues = {
        "electricity": "reported electricity/power issue",
        "water": "reported water supply problem",
        "fire": "emergency fire situation",
        "police": "reported crime/safety issue",
        "gas": "reported gas safety issue",
        "municipal": "reported infrastructure/sanitation issue",
    }
    
    # Detect service from keywords
    for service_type, keywords_dict in SERVICE_KEYWORDS.items():
        all_keywords = (
            keywords_dict.get("hindi", []) +
            keywords_dict.get("english", []) +
            keywords_dict.get("marathi", [])
        )
        if any(kw in matched_keywords for kw in all_keywords):
            issue_text = main_issues.get(service_type, "reported issue")
            break
    else:
        issue_text = "submitted a complaint"
    
    # Urgency indication
    urgency_text = {
        UrgencyLevel.CRITICAL: "URGENT: Critical emergency requiring immediate response",
        UrgencyLevel.HIGH: "Serious issue requiring quick intervention",
        UrgencyLevel.MEDIUM: "Moderate issue requiring attention",
        UrgencyLevel.LOW: "General inquiry or non-urgent complaint",
    }.get(urgency_level, "complaint")
    
    # Extract key details from transcript (first 30 words)
    key_details = " ".join(transcript.split()[:30])
    if len(key_details) > 100:
        key_details = key_details[:100] + "..."
    
    summary = f"{urgency_text}. User {issue_text}. Summary: {key_details}"
    
    return summary
