"""
State-wise Government Schemes Service
Maps user location to relevant government schemes and policies across Indian states.
Uses intelligent caching and optional Grok API integration for real-time policy updates.
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SchemeCategory(str, Enum):
    """Government scheme categories."""
    WATER = "water"
    ELECTRICITY = "electricity"
    ROAD = "road_infrastructure"
    SANITATION = "sanitation"
    HEALTH = "health"
    EDUCATION = "education"
    AGRICULTURE = "agriculture"
    EMPLOYMENT = "employment"
    HOUSING = "housing"
    SOCIAL_WELFARE = "social_welfare"
    GENERAL = "general"


class IndianState(str, Enum):
    """Indian states and union territories."""
    ANDHRA_PRADESH = "AP"
    ARUNACHAL_PRADESH = "AR"
    ASSAM = "AS"
    BIHAR = "BR"
    CHHATTISGARH = "CG"
    GOA = "GA"
    GUJARAT = "GJ"
    HARYANA = "HR"
    HIMACHAL_PRADESH = "HP"
    JHARKHAND = "JH"
    KARNATAKA = "KA"
    KERALA = "KL"
    MADHYA_PRADESH = "MP"
    MAHARASHTRA = "MH"
    MANIPUR = "MN"
    MEGHALAYA = "ML"
    MIZORAM = "MZ"
    NAGALAND = "NL"
    ODISHA = "OD"
    PUNJAB = "PB"
    RAJASTHAN = "RJ"
    SIKKIM = "SK"
    TAMIL_NADU = "TN"
    TELANGANA = "TG"
    TRIPURA = "TR"
    UTTAR_PRADESH = "UP"
    UTTARAKHAND = "UK"
    WEST_BENGAL = "WB"
    DELHI = "DL"
    JAMMU_KASHMIR = "JK"
    LADAKH = "LA"
    PUDUCHERRY = "PY"
    CHANDIGARH = "CH"
    DADRA_NAGAR_HAVELI = "DN"
    LAKSHADWEEP = "LD"
    ANDAMAN_NICOBAR = "AN"


class Scheme(BaseModel):
    """Represents a government scheme."""
    name: str
    name_local: Optional[str] = None
    category: SchemeCategory
    description: str
    eligibility: str
    contact_number: Optional[str] = None
    website: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class StateSchemeMapping(BaseModel):
    """State-wise scheme mapping."""
    state_code: str
    state_name: str
    schemes: List[Scheme]
    last_fetched: datetime = Field(default_factory=datetime.now)


class StateSchemesService:
    """Service to map and retrieve state-specific government schemes."""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        enable_grok: bool = False,
        grok_api_key: Optional[str] = None
    ):
        """
        Initialize state schemes service.
        
        Args:
            cache_dir: Directory to cache scheme data
            enable_grok: Whether to use Grok API for real-time updates
            grok_api_key: Grok API key (if enabled)
        """
        self.cache_dir = cache_dir or Path(__file__).parent / "schemes_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        self.enable_grok = enable_grok and grok_api_key is not None
        self.grok_api_key = grok_api_key or os.getenv("GROK_API_KEY")
        self.grok_endpoint = "https://api.x.ai/v1/chat/completions"
        
        # State name mappings for language detection
        self.state_name_mappings = self._init_state_mappings()
        
        # Load or initialize scheme database
        self.schemes_db: Dict[str, StateSchemeMapping] = {}
        self._load_schemes()
    
    def _init_state_mappings(self) -> Dict[str, List[str]]:
        """Initialize state name variations across languages."""
        return {
            "MH": ["maharashtra", "महाराष्ट्र", "maharastra", "mh"],
            "DL": ["delhi", "दिल्ली", "dilli", "dl", "national capital"],
            "UP": ["uttar pradesh", "उत्तर प्रदेश", "up", "u.p."],
            "TN": ["tamil nadu", "தமிழ்நாடு", "tamilnadu", "tn"],
            "KA": ["karnataka", "ಕರ್ನಾಟಕ", "ka"],
            "GJ": ["gujarat", "ગુજરાત", "gujrat", "gj"],
            "RJ": ["rajasthan", "राजस्थान", "rj"],
            "WB": ["west bengal", "পশ্চিমবঙ্গ", "wb", "bengal"],
            "KL": ["kerala", "കേരളം", "kl"],
            "TG": ["telangana", "తెలంగాణ", "tg"],
            "AP": ["andhra pradesh", "ఆంధ్ర ప్రదేశ్", "ap", "andhra"],
            "BR": ["bihar", "बिहार", "br"],
            "MP": ["madhya pradesh", "मध्य प्रदेश", "mp", "m.p."],
            "HR": ["haryana", "हरियाणा", "hr"],
            "PB": ["punjab", "ਪੰਜਾਬ", "pb"],
            "AS": ["assam", "অসম", "as"],
            "OD": ["odisha", "ଓଡ଼ିଶା", "orissa", "od"],
            "CG": ["chhattisgarh", "छत्तीसगढ़", "cg"],
            "JH": ["jharkhand", "झारखंड", "jh"],
            "UK": ["uttarakhand", "उत्तराखंड", "uttaranchal", "uk"],
            "HP": ["himachal pradesh", "हिमाचल प्रदेश", "hp", "h.p."],
            "GA": ["goa", "गोवा", "ga"],
            "MN": ["manipur", "मणिपुर", "mn"],
            "ML": ["meghalaya", "मेघालय", "ml"],
            "MZ": ["mizoram", "मिजोरम", "mz"],
            "NL": ["nagaland", "नागालैंड", "nl"],
            "SK": ["sikkim", "सिक्किम", "sk"],
            "TR": ["tripura", "ত্রিপুরা", "tr"],
            "AR": ["arunachal pradesh", "अरुणाचल प्रदेश", "ar"],
            "JK": ["jammu and kashmir", "जम्मू और कश्मीर", "jk", "j&k", "jammu kashmir"],
            "LA": ["ladakh", "लद्दाख", "la"],
            "PY": ["puducherry", "पुदुच्चेरी", "pondicherry", "py"],
            "CH": ["chandigarh", "चंडीगढ़", "ch"],
            "DN": ["dadra and nagar haveli", "दादरा और नगर हवेली", "dn"],
            "LD": ["lakshadweep", "लक्षद्वीप", "ld"],
            "AN": ["andaman and nicobar", "अंडमान और निकोबार", "an", "andaman"]
        }
    
    def detect_state_from_text(self, text: str) -> Optional[str]:
        """
        Detect state code from user text using fuzzy matching.
        
        Args:
            text: User input text
        
        Returns:
            State code if detected, None otherwise
        """
        text_lower = text.lower()
        
        for state_code, variations in self.state_name_mappings.items():
            for variant in variations:
                if variant in text_lower:
                    logger.info(f"Detected state: {state_code} from text: '{variant}'")
                    return state_code
        
        return None
    
    def _load_schemes(self):
        """Load schemes from cache or initialize default schemes."""
        # Load Central Government Schemes (common to all states)
        central_schemes = self._get_central_schemes()
        
        # Load state-specific schemes from cache
        for state in IndianState:
            cache_file = self.cache_dir / f"{state.value}.json"
            
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        schemes = [Scheme(**s) for s in data.get("schemes", [])]
                        self.schemes_db[state.value] = StateSchemeMapping(
                            state_code=state.value,
                            state_name=state.name,
                            schemes=schemes + central_schemes,
                            last_fetched=datetime.fromisoformat(data.get("last_fetched", datetime.now().isoformat()))
                        )
                except Exception as e:
                    logger.error(f"Error loading schemes for {state.value}: {e}")
                    self.schemes_db[state.value] = self._init_default_schemes(state.value)
            else:
                self.schemes_db[state.value] = self._init_default_schemes(state.value)
    
    def _get_central_schemes(self) -> List[Scheme]:
        """Get list of central government schemes applicable to all states."""
        return [
            Scheme(
                name="Pradhan Mantri Awas Yojana",
                name_local="प्रधानमंत्री आवास योजना",
                category=SchemeCategory.HOUSING,
                description="Housing for all - financial assistance for construction/enhancement of houses",
                eligibility="Economically weaker sections, low and middle income groups",
                contact_number="1800-11-6163",
                website="https://pmaymis.gov.in"
            ),
            Scheme(
                name="Ayushman Bharat - PM-JAY",
                name_local="आयुष्मान भारत",
                category=SchemeCategory.HEALTH,
                description="Health insurance coverage of Rs 5 lakh per family per year",
                eligibility="Poor and vulnerable families as per SECC database",
                contact_number="14555",
                website="https://pmjay.gov.in"
            ),
            Scheme(
                name="PM-KISAN (Kisan Samman Nidhi)",
                name_local="पीएम-किसान सम्मान निधि",
                category=SchemeCategory.AGRICULTURE,
                description="Direct income support of Rs 6000 per year to farmers",
                eligibility="All landholding farmer families",
                contact_number="155261 / 011-24300606",
                website="https://pmkisan.gov.in"
            ),
            Scheme(
                name="Jal Jeevan Mission",
                name_local="जल जीवन मिशन",
                category=SchemeCategory.WATER,
                description="Functional household tap connection (Har Ghar Jal) to every rural household",
                eligibility="All rural households",
                contact_number="1800-11-1967",
                website="https://jaljeevanmission.gov.in"
            ),
            Scheme(
                name="Swachh Bharat Mission",
                name_local="स्वच्छ भारत मिशन",
                category=SchemeCategory.SANITATION,
                description="Construction of toilets and solid waste management",
                eligibility="All households without toilets",
                contact_number="1800-11-0007",
                website="https://swachhbharatmission.gov.in"
            ),
            Scheme(
                name="PM Gram Sadak Yojana",
                name_local="प्रधानमंत्री ग्राम सड़क योजना",
                category=SchemeCategory.ROAD,
                description="Connectivity to unconnected habitations through all-weather roads",
                eligibility="Rural habitations",
                contact_number="011-23711471",
                website="https://pmgsy.nic.in"
            ),
            Scheme(
                name="National Education Policy 2020",
                name_local="राष्ट्रीय शिक्षा नीति 2020",
                category=SchemeCategory.EDUCATION,
                description="Reforms in education system, scholarships, mid-day meals",
                eligibility="All students",
                contact_number="011-23765609",
                website="https://www.education.gov.in"
            ),
            Scheme(
                name="MGNREGA",
                name_local="महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार गारंटी अधिनियम",
                category=SchemeCategory.EMPLOYMENT,
                description="100 days guaranteed wage employment to rural households",
                eligibility="Rural households willing to do manual work",
                contact_number="1800-345-3455",
                website="https://nrega.nic.in"
            )
        ]
    
    def _init_default_schemes(self, state_code: str) -> StateSchemeMapping:
        """Initialize default schemes for a state."""
        central_schemes = self._get_central_schemes()
        
        return StateSchemeMapping(
            state_code=state_code,
            state_name=state_code,
            schemes=central_schemes,
            last_fetched=datetime.now()
        )
    
    async def get_schemes_for_state(
        self,
        state_code: str,
        category: Optional[SchemeCategory] = None,
        force_refresh: bool = False
    ) -> List[Scheme]:
        """
        Get schemes for a specific state and optionally filter by category.
        
        Args:
            state_code: State code (e.g., 'MH', 'DL')
            category: Optional category filter
            force_refresh: Force refresh from Grok API
        
        Returns:
            List of applicable schemes
        """
        # Normalize state code
        state_code = state_code.upper()
        
        # Check if refresh needed
        if force_refresh or self._needs_refresh(state_code):
            if self.enable_grok:
                await self._fetch_schemes_from_grok(state_code)
        
        # Get schemes from database
        state_mapping = self.schemes_db.get(state_code)
        if not state_mapping:
            logger.warning(f"No schemes found for state: {state_code}")
            return []
        
        schemes = state_mapping.schemes
        
        # Filter by category if specified
        if category:
            schemes = [s for s in schemes if s.category == category]
        
        return schemes
    
    def _needs_refresh(self, state_code: str, max_age_days: int = 30) -> bool:
        """Check if cached schemes need refresh."""
        state_mapping = self.schemes_db.get(state_code)
        if not state_mapping:
            return True
        
        age = datetime.now() - state_mapping.last_fetched
        return age > timedelta(days=max_age_days)
    
    async def _fetch_schemes_from_grok(self, state_code: str):
        """
        Fetch real-time schemes from Grok API.
        
        Args:
            state_code: State code to fetch schemes for
        """
        if not self.grok_api_key:
            logger.warning("Grok API key not configured")
            return
        
        state_name = [k for k, v in IndianState.__members__.items() if v.value == state_code]
        state_name = state_name[0].replace("_", " ").title() if state_name else state_code
        
        prompt = f"""List the current active government schemes and policies for {state_name}, India. 
        Focus on schemes related to water supply, electricity, roads, sanitation, health, education, and social welfare.
        
        For each scheme, provide:
        1. Scheme name (in English and local language if applicable)
        2. Category (water/electricity/road/health/education/etc.)
        3. Brief description
        4. Eligibility criteria
        5. Contact number
        6. Official website URL
        
        Return the response in JSON format as an array of schemes."""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.grok_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.grok_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant that provides accurate information about Indian government schemes."},
                            {"role": "user", "content": prompt}
                        ],
                        "model": "grok-beta",
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Extract JSON from response
                    schemes_data = self._extract_json_from_text(content)
                    if schemes_data:
                        schemes = [Scheme(**s) for s in schemes_data]
                        
                        # Merge with central schemes
                        central_schemes = self._get_central_schemes()
                        all_schemes = schemes + central_schemes
                        
                        # Update database
                        self.schemes_db[state_code] = StateSchemeMapping(
                            state_code=state_code,
                            state_name=state_name,
                            schemes=all_schemes,
                            last_fetched=datetime.now()
                        )
                        
                        # Save to cache
                        self._save_to_cache(state_code)
                        
                        logger.info(f"Fetched {len(schemes)} schemes from Grok for {state_code}")
                else:
                    logger.error(f"Grok API error: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Error fetching schemes from Grok: {e}")
    
    def _extract_json_from_text(self, text: str) -> Optional[List[Dict]]:
        """Extract JSON array from text response."""
        try:
            # Try direct parsing
            return json.loads(text)
        except:
            # Try to find JSON block in text
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
        return None
    
    def _save_to_cache(self, state_code: str):
        """Save schemes to cache file."""
        state_mapping = self.schemes_db.get(state_code)
        if not state_mapping:
            return
        
        cache_file = self.cache_dir / f"{state_code}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "state_code": state_mapping.state_code,
                    "state_name": state_mapping.state_name,
                    "schemes": [s.model_dump(mode='json') for s in state_mapping.schemes],
                    "last_fetched": state_mapping.last_fetched.isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved schemes to cache: {cache_file}")
        except Exception as e:
            logger.error(f"Error saving schemes to cache: {e}")
    
    def format_schemes_for_response(
        self,
        schemes: List[Scheme],
        language: str = "en",
        max_schemes: int = 5
    ) -> str:
        """
        Format schemes into a user-friendly response string.
        
        Args:
            schemes: List of schemes to format
            language: Language code for response
            max_schemes: Maximum number of schemes to include
        
        Returns:
            Formatted string response
        """
        if not schemes:
            if language == "hi":
                return "आपके क्षेत्र के लिए कोई योजना उपलब्ध नहीं है।"
            else:
                return "No schemes available for your region."
        
        # Limit number of schemes
        schemes = schemes[:max_schemes]
        
        if language == "hi":
            intro = f"आपके लिए {len(schemes)} सरकारी योजनाएं उपलब्ध हैं:\n\n"
            scheme_text = []
            for i, scheme in enumerate(schemes, 1):
                text = f"{i}. {scheme.name_local or scheme.name}\n"
                text += f"   विवरण: {scheme.description}\n"
                if scheme.contact_number:
                    text += f"   संपर्क: {scheme.contact_number}\n"
                scheme_text.append(text)
            return intro + "\n".join(scheme_text)
        else:
            intro = f"You are eligible for {len(schemes)} government schemes:\n\n"
            scheme_text = []
            for i, scheme in enumerate(schemes, 1):
                text = f"{i}. {scheme.name}\n"
                text += f"   Description: {scheme.description}\n"
                if scheme.contact_number:
                    text += f"   Contact: {scheme.contact_number}\n"
                scheme_text.append(text)
            return intro + "\n".join(scheme_text)
