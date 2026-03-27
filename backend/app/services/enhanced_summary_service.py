"""
Enhanced AI Summary Service
Provides concise, urgent, and better summaries of citizen complaints with improved urgency detection.
Optimizes API calls by caching and intelligent processing.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UrgencyLevel(str, Enum):
    """Urgency levels for complaints."""
    CRITICAL = "CRITICAL"  # Life threatening, immediate action needed
    HIGH = "HIGH"  # Serious issue, action within hours
    MEDIUM = "MEDIUM"  # Important but not urgent
    LOW = "LOW"  # Can be addressed in due course
    INFORMATIONAL = "INFORMATIONAL"  # Just information, no action needed


class SummaryStyle(str, Enum):
    """Summary generation styles."""
    CONCISE = "CONCISE"  # Single sentence
    BRIEF = "BRIEF"  # 2-3 sentences
    DETAILED = "DETAILED"  # Full paragraph


class EnhancedSummary(BaseModel):
    """Enhanced summary with urgency and key points."""
    original_text: str
    summary: str
    key_points: List[str] = Field(default_factory=list)
    urgency: UrgencyLevel
    urgency_score: float  # 0.0 to 1.0
    category: str
    requires_immediate_action: bool
    suggested_response_time: str  # e.g., "within 2 hours", "within 24 hours"
    affected_area: Optional[str] = None
    citizen_emotion: Optional[str] = None  # angry, frustrated, neutral, satisfied
    generated_at: datetime = Field(default_factory=datetime.now)


class SummaryCache:
    """Cache for generated summaries to reduce API calls."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 24):
        """
        Initialize summary cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time to live for cached items in hours
        """
        self.cache_dir = cache_dir or Path(__file__).parent / "summary_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: Dict[str, EnhancedSummary] = {}
        self._load_cache()
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.md5(text.lower().strip().encode()).hexdigest()
    
    def get(self, text: str) -> Optional[EnhancedSummary]:
        """Get cached summary if available and not expired."""
        key = self._get_cache_key(text)
        
        if key in self._cache:
            summary = self._cache[key]
            age = datetime.now() - summary.generated_at
            
            if age < self.ttl:
                logger.info(f"Cache hit for summary: {key[:8]}...")
                return summary
            else:
                # Expired, remove from cache
                del self._cache[key]
        
        return None
    
    def set(self, text: str, summary: EnhancedSummary):
        """Store summary in cache."""
        key = self._get_cache_key(text)
        self._cache[key] = summary
        self._save_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        cache_file = self.cache_dir / "summaries.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, item in data.items():
                        self._cache[key] = EnhancedSummary(**item)
                logger.info(f"Loaded {len(self._cache)} summaries from cache")
            except Exception as e:
                logger.error(f"Error loading summary cache: {e}")
    
    def _save_cache(self):
        """Save cache to disk."""
        cache_file = self.cache_dir / "summaries.json"
        
        try:
            # Only save non-expired items
            valid_cache = {
                k: v.model_dump(mode='json')
                for k, v in self._cache.items()
                if datetime.now() - v.generated_at < self.ttl
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(valid_cache, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving summary cache: {e}")


class EnhancedAISummaryService:
    """
    Enhanced AI summary service with urgency detection and caching.
    Generates concise summaries optimized for quick understanding.
    """
    
    def __init__(self, enable_cache: bool = True):
        """
        Initialize enhanced summary service.
        
        Args:
            enable_cache: Whether to enable summary caching
        """
        self.cache = SummaryCache() if enable_cache else None
        
        # Urgency keywords and patterns
        self.urgency_patterns = self._init_urgency_patterns()
        
        # Emotion detection patterns
        self.emotion_patterns = self._init_emotion_patterns()
    
    def _init_urgency_patterns(self) -> Dict[UrgencyLevel, List[str]]:
        """Initialize urgency detection patterns."""
        return {
            UrgencyLevel.CRITICAL: [
                r'\b(emergency|urgent|critical|immediate|asap|dying|death|fire|accident|ambulance)\b',
                r'\b(aag|jalan|maut|ambulans|turant|jaldi|bachao|madad)\b',
                r'\b(எச்சரிக்கை|அவசரம்|உடனடி)\b',  # Tamil
                r'\b(आपातकालीन|तत्काल|जरूरी|जल्दी)\b',  # Hindi/Marathi
                r'\b(ತುರ್ತು|ತಕ್ಷಣ)\b',  # Kannada
                r'\b(അടിയന്തിര|ഉടനടി)\b'  # Malayalam
            ],
            UrgencyLevel.HIGH: [
                r'\b(serious|severe|major|breakdown|flooding|no water|power cut)\b',
                r'\b(bahut|zyada|bada|serious|problem|dikkat|paani nahi|bijli nahi)\b',
                r'\b(தீவிர|பெரிய|சிக்கல்)\b',
                r'\b(गंभीर|बड़ी|समस्या)\b',
                r'\b(తీవ్రమైన|పెద్ద|సమస్య)\b'  # Telugu
            ],
            UrgencyLevel.MEDIUM: [
                r'\b(issue|problem|complaint|not working|broken|damaged)\b',
                r'\b(kharab|toot|bigad|samasya|shikayat)\b',
                r'\b(பிரச்சனை|கெட்டுப்போன)\b',
                r'\b(समस्या|टूटा|खराब)\b'
            ],
            UrgencyLevel.LOW: [
                r'\b(request|need|want|improvement|suggestion)\b',
                r'\b(chahiye|zaroorat|sudhar|salah)\b',
                r'\b(வேண்டும்|தேவை)\b'
            ]
        }
    
    def _init_emotion_patterns(self) -> Dict[str, List[str]]:
        """Initialize emotion detection patterns."""
        return {
            "angry": [
                r'\b(angry|furious|mad|frustrated|fed up|disgusted)\b',
                r'\b(gussa|naraz|pareshan|tang|thak)\b',
                r'\b(கோபம்|எரிச்சல்)\b',
                r'\b(गुस्सा|नाराज़|परेशान)\b'
            ],
            "frustrated": [
                r'\b(frustrated|tired|helpless|hopeless|again|repeatedly)\b',
                r'\b(pareshan|thak|baar baar|phir se|koi sunwai nahi)\b',
                r'\b(விரக்தி|சோர்வு)\b'
            ],
            "neutral": [
                r'\b(inform|report|notify|register|complaint)\b',
                r'\b(batana|report|shikayat|darj)\b'
            ],
            "satisfied": [
                r'\b(thank|appreciate|resolved|fixed|good|better)\b',
                r'\b(dhanyavad|shukriya|theek|thik)\b'
            ]
        }
    
    def generate_summary(
        self,
        text: str,
        category: str = "General",
        language: str = "en",
        style: SummaryStyle = SummaryStyle.CONCISE
    ) -> EnhancedSummary:
        """
        Generate enhanced summary with urgency detection.
        
        Args:
            text: Original complaint text
            category: Issue category (Water, Electricity, etc.)
            language: Detected language
            style: Summary style (concise/brief/detailed)
        
        Returns:
            EnhancedSummary object
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(text)
            if cached:
                return cached
        
        # Detect urgency
        urgency, urgency_score = self._detect_urgency(text)
        
        # Detect emotion
        emotion = self._detect_emotion(text)
        
        # Generate summary based on style
        summary = self._create_summary(text, style, category, language)
        
        # Extract key points
        key_points = self._extract_key_points(text)
        
        # Determine response time
        response_time = self._get_response_time(urgency)
        
        # Detect affected area if mentioned
        affected_area = self._extract_location(text)
        
        result = EnhancedSummary(
            original_text=text,
            summary=summary,
            key_points=key_points,
            urgency=urgency,
            urgency_score=urgency_score,
            category=category,
            requires_immediate_action=(urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]),
            suggested_response_time=response_time,
            affected_area=affected_area,
            citizen_emotion=emotion
        )
        
        # Cache the result
        if self.cache:
            self.cache.set(text, result)
        
        return result
    
    def _detect_urgency(self, text: str) -> Tuple[UrgencyLevel, float]:
        """
        Detect urgency level from text.
        
        Returns:
            Tuple of (UrgencyLevel, confidence_score)
        """
        text_lower = text.lower()
        scores = {level: 0.0 for level in UrgencyLevel}
        
        for level, patterns in self.urgency_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                scores[level] += matches * 0.2
        
        # Check for exclamation marks and caps (indicating urgency)
        exclamations = text.count('!')
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        if exclamations >= 2 or caps_ratio > 0.3:
            scores[UrgencyLevel.CRITICAL] += 0.3
            scores[UrgencyLevel.HIGH] += 0.2
        
        # Normalize scores
        max_score = max(scores.values())
        if max_score > 0:
            for level in scores:
                scores[level] /= max_score
        
        # Get highest scoring level
        urgency = max(scores.items(), key=lambda x: x[1])[0]
        confidence = scores[urgency]
        
        # Default to MEDIUM if no clear signals
        if confidence < 0.3:
            urgency = UrgencyLevel.MEDIUM
            confidence = 0.5
        
        return urgency, min(confidence, 1.0)
    
    def _detect_emotion(self, text: str) -> str:
        """Detect citizen's emotional state from text."""
        text_lower = text.lower()
        scores = {emotion: 0 for emotion in self.emotion_patterns}
        
        for emotion, patterns in self.emotion_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                scores[emotion] += matches
        
        # Return emotion with highest score, default to neutral
        if max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "neutral"
    
    def _create_summary(
        self,
        text: str,
        style: SummaryStyle,
        category: str,
        language: str
    ) -> str:
        """Create summary based on style."""
        # Clean text
        text = text.strip()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if style == SummaryStyle.CONCISE:
            # Single sentence summary
            if sentences:
                # Take first meaningful sentence or combine key phrases
                summary = sentences[0]
                if len(summary) > 100:
                    summary = summary[:97] + "..."
                return f"{category}: {summary}"
            return f"{category} issue reported"
        
        elif style == SummaryStyle.BRIEF:
            # 2-3 sentences
            summary_sentences = sentences[:3]
            return " ".join(summary_sentences)
        
        else:  # DETAILED
            # Full paragraph with context
            return text[:500] + ("..." if len(text) > 500 else "")
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from complaint text."""
        key_points = []
        
        # Look for specific details
        patterns = {
            "location": r'\b(area|ward|street|road|colony|mohalla|village|locality)\s+([A-Za-z\s]+)\b',
            "time": r'\b(since|from|for)\s+(\d+\s*(?:day|week|month|hour)s?)\b',
            "quantity": r'\b(\d+)\s+(people|families|houses|days|times)\b',
            "frequency": r'\b(daily|everyday|repeatedly|multiple times|baar baar)\b'
        }
        
        for point_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if point_type == "location":
                    key_points.append(f"Location: {matches[0][1].strip()}")
                elif point_type == "time":
                    key_points.append(f"Duration: {matches[0][1]}")
                elif point_type == "quantity":
                    key_points.append(f"Affected: {matches[0][0]} {matches[0][1]}")
                elif point_type == "frequency":
                    key_points.append(f"Frequency: {matches[0]}")
        
        return key_points[:5]  # Limit to top 5 key points
    
    def _get_response_time(self, urgency: UrgencyLevel) -> str:
        """Get suggested response time based on urgency."""
        response_times = {
            UrgencyLevel.CRITICAL: "immediate (within 1 hour)",
            UrgencyLevel.HIGH: "within 4 hours",
            UrgencyLevel.MEDIUM: "within 24 hours",
            UrgencyLevel.LOW: "within 3 days",
            UrgencyLevel.INFORMATIONAL: "within 7 days"
        }
        return response_times.get(urgency, "within 24 hours")
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location/area information from text."""
        # Common location patterns
        patterns = [
            r'(?:in|at|near)\s+([A-Za-z\s]+(?:area|ward|colony|road|street|mohalla|nagar|puram|pur))',
            r'(?:area|ward|colony|road|street)\s+(?:number\s+)?([A-Z0-9\s]+)',
            r'([A-Za-z]+\s+(?:nagar|puram|colony|area|ward))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 3:  # Avoid very short matches
                    return location
        
        return None
    
    def format_for_display(self, summary: EnhancedSummary, language: str = "en") -> str:
        """Format enhanced summary for display/TTS."""
        if language == "hi":
            urgency_text = {
                UrgencyLevel.CRITICAL: "अत्यंत आवश्यक",
                UrgencyLevel.HIGH: "जरूरी",
                UrgencyLevel.MEDIUM: "सामान्य",
                UrgencyLevel.LOW: "कम प्राथमिकता",
                UrgencyLevel.INFORMATIONAL: "सूचनात्मक"
            }
            
            text = f"श्रेणी: {summary.category}\n"
            text += f"प्राथमिकता: {urgency_text[summary.urgency]}\n"
            text += f"सारांश: {summary.summary}\n"
            
            if summary.key_points:
                text += f"मुख्य बिंदु: {', '.join(summary.key_points[:3])}\n"
            
            if summary.requires_immediate_action:
                text += "⚠️ तत्काल कार्रवाई आवश्यक\n"
            
            return text
        else:
            text = f"Category: {summary.category}\n"
            text += f"Urgency: {summary.urgency.value}\n"
            text += f"Summary: {summary.summary}\n"
            
            if summary.key_points:
                text += f"Key Points: {', '.join(summary.key_points[:3])}\n"
            
            if summary.requires_immediate_action:
                text += "⚠️ Immediate action required\n"
            
            return text
