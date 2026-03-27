"""
Indian Government Services Mapping
===================================
Maps grievances to actual state/central government departments
and utilities for intelligent routing.

Services Included:
- Electricity (State Electricity Boards/Discoms)
- Water Supply (Municipal/State Water Boards)
- Fire/Emergency Services
- Police
- Municipal Corporation
- Other State-Level Services
"""

from typing import Dict, List, Optional, Tuple
from models.grievance_models import GovServiceMapping


# ─────────────────────────────────────────────────────────────────
# SERVICE KEYWORDS MAPPING
# ─────────────────────────────────────────────────────────────────

SERVICE_KEYWORDS = {
    "electricity": {
        "hindi": ["बिजली", "बिजली नहीं", "बिजली गई", "विद्युत", "बिल", "मीटर", "connection", "live wire"],
        "english": ["electricity", "power", "power cut", "outage", "blackout", "meter", "bill", "connection", "voltage"],
        "marathi": ["विजा", "विजा नाही", "वीज"],
        "department_codes": ["AES", "MSEDCL", "DSM"],
    },
    "water": {
        "hindi": ["पानी", "पानी नहीं", "पानी निकल रहा", "नल", "टंकी", "टैंक", "की समस्या"],
        "english": ["water", "no water", "water supply", "tap", "leakage", "burst", "pipeline", "tap water"],
        "marathi": ["पाणी", "नाळ", "टाकी"],
        "department_codes": ["JDVN", "BMC", "PHWSC"],
    },
    "fire": {
        "hindi": ["आग", "आग लगी", "आग लगना", "आग लगो", "आग है", "आग लगा दी", "fire"],
        "english": ["fire", "burning", "flames", "blaze", "smoke", "chemical fire", "forest fire"],
        "marathi": ["आग", "केमिकल आग"],
        "department_codes": ["FD", "MFD"],
        "is_emergency": True,
    },
    "police": {
        "hindi": ["चोर", "चोरी", "डाका", "मारपीट", "गुंडे", "हमला", "कानून", "पुलिस"],
        "english": ["theft", "robbery", "assault", "attack", "police", "crime", "stolen"],
        "marathi": ["चोरी", "हल्ला"],
        "department_codes": ["PD", "PS"],
        "may_escalate_to_fire": True,
    },
    "medical": {
        "hindi": ["अस्पताल", "डॉक्टर", "एम्बुलेंस", "बीमार", "स्वास्थ्य", "दुर्घटना"],
        "english": ["hospital", "doctor", "ambulance", "health", "sick", "accident", "emergency"],
        "marathi": ["रुग्णालय", "डॉक्टर", "रुग्णवाहिका", "आरोग्य"],
        "department_codes": ["MOH", "PHRD", "MED"],
        "is_emergency": True,
    },
    "municipal": {
        "hindi": ["सड़क", "गड्ढा", "पार्क", "स्कूल", "अस्पताल", "कूड़ा", "कचरा", "सफाई"],
        "english": ["pothole", "street", "road", "garbage", "dirt", "maintenance", "park", "public"],
        "marathi": ["रस्ता", "खड्डा", "कचरा"],
        "department_codes": ["MC", "BMC", "UMC"],
    },
    "gas": {
        "hindi": ["गैस", "गैस निकल रही", "गैस दुर्गंध", "गैस बदबू", "रिसाव"],
        "english": ["gas", "gas leak", "smell", "safety", "cylinder"],
        "marathi": ["गॅस", "गॅस गंध"],
        "department_codes": ["MGCL", "IGD"],
        "may_escalate_to_fire": True,
    },
    "telecom": {
        "hindi": ["फोन", "नेट", "इंटरनेट", "सिग्नल", "नेटवर्क", "कनेक्शन"],
        "english": ["phone", "network", "signal", "internet", "connection", "data"],
        "marathi": ["फोन", "नेट"],
        "department_codes": ["TRAI", "DOT"],
    },
    # NEW: Agriculture & Farmer schemes
    "agriculture": {
        "hindi": ["किसान", "खेती", "फसल", "कृषि", "बीज", "खाद", "सिंचाई", "ट्रैक्टर", "मंडी", "उपज", "खेत", "शेती"],
        "english": ["farmer", "farming", "agriculture", "crop", "seed", "fertilizer", "irrigation", "tractor", "harvest", "farm"],
        "marathi": ["शेतकरी", "शेती", "पीक", "कृषी", "बियाणे", "खत", "सिंचन", "शेत", "उत्पादन"],
        "tamil": ["விவசாயி", "விவசாயம்", "பயிர்", "விதை", "உரம்"],
        "telugu": ["రైతు", "వ్యవసాయం", "పంట", "విత్తనం"],
        "bengali": ["কৃষক", "চাষ", "ফসল", "বীজ"],
        "gujarati": ["ખેડૂત", "ખેતી", "પાક", "બીજ"],
        "kannada": ["ರೈತ", "ಕೃಷಿ", "ಬೆಳೆ", "ಬೀಜ"],
        "department_codes": ["AGRI", "DAC", "FW"],
    },
    # NEW: Government schemes category
    "scheme": {
        "hindi": ["योजना", "स्कीम", "सब्सिडी", "अनुदान", "लाभ", "सरकारी योजना", "पेंशन", "बीमा", "राशन", "आवास"],
        "english": ["scheme", "subsidy", "benefit", "grant", "pension", "insurance", "ration", "housing", "welfare", "pm kisan", "pmay"],
        "marathi": ["योजना", "अनुदान", "लाभ", "सरकारी योजना", "पेन्शन", "विमा", "रेशन", "आवास"],
        "tamil": ["திட்டம்", "மானியம்", "ஓய்வூதியம்", "காப்பீடு"],
        "telugu": ["పథకం", "సబ్సిడీ", "పెన్షన్", "బీమా"],
        "bengali": ["প্রকল্প", "ভর্তুকি", "পেনশন", "বীমা"],
        "gujarati": ["યોજના", "સબસિડી", "પેન્શન", "વીમા"],
        "kannada": ["ಯೋಜನೆ", "ಸಬ್ಸಿಡಿ", "ಪಿಂಚಣಿ", "ವಿಮೆ"],
        "department_codes": ["SW", "RD", "PMO"],
    },
    # NEW: General/Clarification category (lowest priority)
    "general": {
        "hindi": ["मदद", "सहायता", "जानकारी", "पूछना", "बताना"],
        "english": ["help", "information", "query", "question", "assistance", "support"],
        "marathi": ["मदत", "माहिती", "विचारणा"],
        "department_codes": ["GEN", "HELP"],
    },
}


# ─────────────────────────────────────────────────────────────────
# STATE-LEVEL SERVICE CONFIGURATIONS
# ─────────────────────────────────────────────────────────────────

STATE_SERVICES: Dict[str, Dict[str, GovServiceMapping]] = {
    "maharashtra": {
        "electricity": GovServiceMapping(
            service_type="electricity",
            service_name="Maharashtra State Electricity Distribution Company Limited (MSEDCL)",
            department_code="MSEDCL",
            contact_method="phone",
            contact_info="Toll Free: 1912 (local call); 9545909090",
            priority=1,
            sla_minutes=120,
            regional_office="Circle Representative Office",
            handling_team="Meter Reader + Line Workers + Technical Team",
        ),
        "water": GovServiceMapping(
            service_type="water",
            service_name="Jal Sansthan (Water Supply Board)",
            department_code="JDVN",
            contact_method="phone",
            contact_info="1800-233-1331 (Maharashtra Water Supply)",
            priority=2,
            sla_minutes=240,
            regional_office="Water Supply Zone",
            handling_team="Water Works Department",
        ),
        "gas": GovServiceMapping(
            service_type="gas",
            service_name="Mahanagar Gas Company Limited (MGCL)",
            department_code="MGCL",
            contact_method="phone",
            contact_info="1906 (toll free gas emergency)",
            priority=1,
            sla_minutes=30,
            regional_office="Regional Gas Office",
            handling_team="Emergency Response Team",
        ),
        "fire": GovServiceMapping(
            service_type="fire",
            service_name="Maharashtra Fire and Emergency Services",
            department_code="MFD",
            contact_method="phone",
            contact_info="101 (All Emergency)",
            priority=0,  # Highest
            sla_minutes=5,
            handling_team="Fire Brigade + Rescue Team",
        ),
        "police": GovServiceMapping(
            service_type="police",
            service_name="Maharashtra Police",
            department_code="PD",
            contact_method="phone",
            contact_info="100 (Police Emergency) or 112 (Integrated Emergency)",
            priority=0,  # Highest
            sla_minutes=5,
            handling_team="Local Police Station + Patrol Units",
        ),
        "medical": GovServiceMapping(
            service_type="medical",
            service_name="Medical Emergency & Ambulance Services",
            department_code="MED",
            contact_method="phone",
            contact_info="108 (Ambulance Options)",
            priority=0,  # Highest
            sla_minutes=5,
            handling_team="Health Emergency Team + Nearby Hospitals",
        ),
        "municipal": GovServiceMapping(
            service_type="municipal",
            service_name="Brihanmumbai Municipal Corporation (BMC) / Municipal Corporation",
            department_code="MC",
            contact_method="phone",
            contact_info="1916 (All complaints) or 1909 (Emergency)",
            priority=3,
            sla_minutes=86400,  # 24 hours
            regional_office="Ward Office + Health Post",
        ),
    },
    "tamil_nadu": {
        "electricity": GovServiceMapping(
            service_type="electricity",
            service_name="Tamil Nadu Generation and Distribution Corporation (TANGEDCO)",
            department_code="TANGEDCO",
            contact_method="phone",
            contact_info="1912 (Toll Free)",
            priority=1,
            sla_minutes=120,
        ),
        "water": GovServiceMapping(
            service_type="water",
            service_name="Chennai Metropolitan Water Supply Board",
            department_code="CMWSB",
            contact_method="phone",
            contact_info="14400 (Chennai) or 155333 (Other towns)",
            priority=2,
            sla_minutes=240,
        ),
        "fire": GovServiceMapping(
            service_type="fire",
            service_name="Tamil Nadu Fire and Rescue Services",
            department_code="FD",
            contact_method="phone",
            contact_info="101",
            priority=0,
            sla_minutes=5,
        ),
    },
    "delhi": {
        "electricity": GovServiceMapping(
            service_type="electricity",
            service_name="Delhi Electricity Regulatory Commission (DERC)",
            department_code="DERC",
            contact_method="phone",
            contact_info="1912 (BESCOM) or Customer Care Center",
            priority=1,
            sla_minutes=120,
        ),
        "water": GovServiceMapping(
            service_type="water",
            service_name="Delhi Jal Board (DJB)",
            department_code="DJB",
            contact_method="phone",
            contact_info="1916",
            priority=2,
            sla_minutes=240,
        ),
        "fire": GovServiceMapping(
            service_type="fire",
            service_name="Delhi Fire Service",
            department_code="DFS",
            contact_method="phone",
            contact_info="101",
            priority=0,
            sla_minutes=5,
        ),
    },
}

# Default state for test/fallback
DEFAULT_STATE = "maharashtra"

# Generic services when state is unknown
GENERIC_SERVICES = {
    "electricity": GovServiceMapping(
        service_type="electricity",
        service_name="State Electricity Distribution Company",
        department_code="DISCOM",
        contact_method="phone",
        contact_info="1912 (All States) or Local Customer Care",
        priority=2,
        sla_minutes=240,
    ),
    "water": GovServiceMapping(
        service_type="water",
        service_name="State Water Supply Board",
        department_code="WSB",
        contact_method="phone",
        contact_info="Local Water Supply Department",
        priority=2,
        sla_minutes=240,
    ),
    "fire": GovServiceMapping(
        service_type="fire",
        service_name="Fire and Emergency Services",
        department_code="FD",
        contact_method="phone",
        contact_info="101",
        priority=0,
        sla_minutes=5,
    ),
    "police": GovServiceMapping(
        service_type="police",
        service_name="Police Department",
        department_code="PD",
        contact_method="phone",
        contact_info="100 or 112",
        priority=0,
        sla_minutes=5,
    ),
    "medical": GovServiceMapping(
        service_type="medical",
        service_name="Medical/Ambulance Services",
        department_code="MED",
        contact_method="phone",
        contact_info="108",
        priority=0,
        sla_minutes=5,
    ),
    # NEW: Agriculture Department
    "agriculture": GovServiceMapping(
        service_type="agriculture",
        service_name="Department of Agriculture & Farmer Welfare",
        department_code="DAC",
        contact_method="phone",
        contact_info="1800-180-1551 (Kisan Call Centre)",
        priority=3,
        sla_minutes=1440,  # 24 hours
        regional_office="District Agriculture Office",
    ),
    # NEW: Scheme/Welfare Department
    "scheme": GovServiceMapping(
        service_type="scheme",
        service_name="Social Welfare & Schemes Department",
        department_code="SW",
        contact_method="phone",
        contact_info="1800-180-1111 (Govt Helpline)",
        priority=3,
        sla_minutes=1440,
        regional_office="District Collector Office",
    ),
    # NEW: General Helpdesk
    "general": GovServiceMapping(
        service_type="general",
        service_name="Government Helpdesk",
        department_code="HELP",
        contact_method="phone",
        contact_info="181 (State Helpline) or 1800-111-555",
        priority=4,
        sla_minutes=2880,  # 48 hours
    ),
}


def detect_service_type(
    transcript: str, 
    keywords_found: List[str],
    intent: Optional[str] = None,
) -> Tuple[str, List[str], bool]:
    """
    Detect service type from transcript and keywords.
    
    Args:
        transcript: Original user transcript
        keywords_found: Keywords identified from urgency analysis
        intent: Optional intent classification
        
    Returns:
        (service_type, matched_keywords, may_escalate_to_fire)
    """
    text_lower = transcript.lower()
    matched_keywords = []
    service_type = "general"
    may_escalate = False
    
    # Check each service's keywords
    for stype, keywords_dict in SERVICE_KEYWORDS.items():
        all_keywords = (
            keywords_dict.get("hindi", []) +
            keywords_dict.get("english", []) +
            keywords_dict.get("marathi", [])
        )
        
        for keyword in all_keywords:
            if keyword.lower() in text_lower or keyword in keywords_found:
                matched_keywords.append(keyword)
                if service_type == "general":
                    service_type = stype
    
    # Check for escalation patterns
    if service_type in ["gas", "fire", "police"]:
        may_escalate = SERVICE_KEYWORDS.get(service_type, {}).get("may_escalate_to_fire", False)
    
    return service_type, list(set(matched_keywords)), may_escalate


def get_service_mapping(
    service_type: str,
    state: str = DEFAULT_STATE,
    language: str = "en",
) -> Optional[GovServiceMapping]:
    """
    Get service mapping for a given service type and state.
    
    Args:
        service_type: Type of service (electricity, water, fire, etc.)
        state: State name (lowercase, space replaced with _)
        language: Language code (for future localization)
        
    Returns:
        GovServiceMapping or None
    """
    state_lower = state.lower().replace(" ", "_")
    
    # Try state-specific mapping
    if state_lower in STATE_SERVICES:
        if service_type in STATE_SERVICES[state_lower]:
            return STATE_SERVICES[state_lower][service_type]
    
    # Fall back to generic service
    return GENERIC_SERVICES.get(service_type)


def get_all_state_services(state: str = DEFAULT_STATE) -> Dict[str, GovServiceMapping]:
    """Get all available services for a state."""
    state_lower = state.lower().replace(" ", "_")
    return STATE_SERVICES.get(state_lower, GENERIC_SERVICES)


def format_service_contact(mapping: GovServiceMapping, language: str = "en") -> str:
    """
    Format service contact information for user communication.
    
    Args:
        mapping: GovServiceMapping object
        language: Language code
        
    Returns:
        Formatted contact string
    """
    contact_str = f"{mapping.service_name}\n"
    contact_str += f"Department: {mapping.department_code}\n"
    contact_str += f"Contact: {mapping.contact_info}\n"
    contact_str += f"Priority: Immediate response" if mapping.priority <= 1 else f"Expected response: {mapping.sla_minutes} minutes"
    
    if mapping.regional_office:
        contact_str += f"\nOffice: {mapping.regional_office}"
    if mapping.handling_team:
        contact_str += f"\nTeam: {mapping.handling_team}"
    
    return contact_str
