#!/usr/bin/env python3
"""
Sentence-Level Multilingual Language Detection using Sarvam
============================================================

Detects language at the sentence/segment level and supports mixed-language predictions.
Each sentence can have its own language code for proper TTS synthesis and routing.

Features:
  • Segment text into sentences/clauses
  • Detect language for each segment independently using Sarvam
  • Return predictions with per-sentence language codes
  • Support for code-switching and mixed-language content
  • Fallback to global language detection if segment-level fails
"""

import logging
import os
import re
import asyncio
from typing import List, Dict, Tuple, Optional
import aiohttp
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SegmentPrediction:
    """A single segment with its language prediction."""
    text: str
    language_code: str
    confidence: float
    start_idx: int  # Character position in original text
    end_idx: int    # Character position in original text
    provider: str = "sarvam"
    

@dataclass
class MultilingualPrediction:
    """Complete multilingual prediction for entire transcript."""
    full_text: str
    segments: List[SegmentPrediction]
    primary_language: str  # Most frequent language
    primary_confidence: float
    language_distribution: Dict[str, float]  # {lang_code: percentage}
    is_code_switched: bool  # True if multiple languages detected
    metadata: Dict = field(default_factory=dict)


class SentenceSegmenter:
    """Intelligently segments text for language detection."""
    
    # Sentence delimiters for Indian languages
    DELIMITERS = {
        # Devanagari script (Hindi, Marathi, Konkani, etc.)
        'devanagari': r'[।!\?॥]+',
        # Tamil script
        'tamil': r'[।!?]+',
        # Telugu script
        'telugu': r'[।!?\u0C64]+',
        # Kannada script
        'kannada': r'[।!?\u0CFA]+',
        # Malayalam script
        'malayalam': r'[!?\u0D02\u0D03]+',
        # Bengali script
        'bengali': r'[।!?\u0981\u0982\u0983]+',
        # Gujarati script
        'gujarati': r'[।!?\u0A82\u0A83]+',
        # Urdu/Persian script
        'urdu': r'[۔؟!]+',
        # Latin script (English, Romanized)
        'latin': r'[.!?]+',
        # Generic
        'generic': r'[.!?\n]+',
    }
    
    def __init__(self, min_segment_length: int = 5, max_segment_length: int = 200):
        """
        Initialize segmenter.
        
        Args:
            min_segment_length: Minimum characters for a segment
            max_segment_length: Maximum characters for a segment
        """
        self.min_segment_length = min_segment_length
        self.max_segment_length = max_segment_length
    
    @staticmethod
    def detect_script(text: str) -> str:
        """Detect which script is predominantly used."""
        # Devanagari range: U+0900 to U+097F
        devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
        # Tamil: U+0B80 to U+0BFF
        tamil_count = len(re.findall(r'[\u0B80-\u0BFF]', text))
        # Telugu: U+0C00 to U+0C7F
        telugu_count = len(re.findall(r'[\u0C00-\u0C7F]', text))
        # Kannada: U+0C80 to U+0CFF
        kannada_count = len(re.findall(r'[\u0C80-\u0CFF]', text))
        # Malayalam: U+0D00 to U+0D7F
        malayalam_count = len(re.findall(r'[\u0D00-\u0D7F]', text))
        # Bengali: U+0980 to U+09FF
        bengali_count = len(re.findall(r'[\u0980-\u09FF]', text))
        # Gujarati: U+0A80 to U+0AFF
        gujarati_count = len(re.findall(r'[\u0A80-\u0AFF]', text))
        # Urdu: Arabic script range
        urdu_count = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F]', text))
        
        counts = {
            'devanagari': devanagari_count,
            'tamil': tamil_count,
            'telugu': telugu_count,
            'kannada': kannada_count,
            'malayalam': malayalam_count,
            'bengali': bengali_count,
            'gujarati': gujarati_count,
            'urdu': urdu_count,
            'latin': len(text) - sum([devanagari_count, tamil_count, telugu_count, 
                                      kannada_count, malayalam_count, bengali_count, 
                                      gujarati_count, urdu_count])
        }
        
        max_script = max(counts, key=counts.get)
        return max_script if counts[max_script] > 0 else 'generic'
    
    def segment(self, text: str) -> List[Dict]:
        """
        Segment text into sentences/clauses.
        
        Returns:
            List of dicts: {'text': segment_text, 'start': idx, 'end': idx}
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Detect script to use appropriate delimiters
        script = self.detect_script(text)
        delim_pattern = self.DELIMITERS.get(script, self.DELIMITERS['generic'])
        
        # Split by delimiters while preserving positions
        segments = []
        current_pos = 0
        
        for match in re.finditer(delim_pattern, text):
            segment_text = text[current_pos:match.start()].strip()
            
            if len(segment_text) >= self.min_segment_length:
                segments.append({
                    'text': segment_text,
                    'start': current_pos,
                    'end': match.start()
                })
            
            current_pos = match.end()
        
        # Add remaining text as final segment
        remaining = text[current_pos:].strip()
        if len(remaining) >= self.min_segment_length:
            segments.append({
                'text': remaining,
                'start': current_pos,
                'end': len(text)
            })
        
        # If no segments found, return text as single segment
        if not segments:
            return [{
                'text': text.strip(),
                'start': 0,
                'end': len(text)
            }]
        
        # Merge small segments with adjacent segments
        merged = []
        for segment in segments:
            if len(segment['text']) < self.min_segment_length and merged:
                merged[-1]['text'] += ' ' + segment['text']
                merged[-1]['end'] = segment['end']
            else:
                merged.append(segment)
        
        return merged


class SentenceLevelLanguageDetector:
    """Detects language at sentence level using Sarvam."""
    
    def __init__(self):
        """Initialize detector with Sarvam credentials."""
        self.api_key = os.getenv("SARVAM_API_KEY", "").strip()
        self.lang_detect_url = os.getenv("SARVAM_LANG_DETECT_API_URL", "").strip()
        self.segmenter = SentenceSegmenter()
    
    @property
    def enabled(self) -> bool:
        """Check if Sarvam is properly configured."""
        return bool(self.api_key and self.lang_detect_url)
    
    @staticmethod
    def _normalize_lang_code(raw_lang: Optional[str]) -> Optional[str]:
        """Normalize language code from Sarvam response."""
        if not raw_lang:
            return None
        
        value = str(raw_lang).strip().lower()
        if value.endswith("-in"):
            value = value.split("-")[0]
        
        mapping = {
            "english": "en", "hindi": "hi", "marathi": "mr", "gujarati": "gu",
            "tamil": "ta", "telugu": "te", "kannada": "kn", "malayalam": "ml",
            "bengali": "bn", "assamese": "as", "odia": "or", "oriya": "or",
            "punjabi": "pa", "konkani": "kok", "bhojpuri": "bho", "maithili": "mai",
            "dogri": "doi", "haryanvi": "bgc", "marwadi": "mwr", "awadhi": "awa",
            "pahadi": "pah", "kashmiri": "ks", "kashmiri": "kas", "sindhi": "sd",
            "sanskrit": "sa", "nepali": "ne", "manipuri": "mni", "santali": "sat",
            "bodo": "bo", "tulu": "tcy", "urdu": "ur",
        }
        
        return mapping.get(value, value)
    
    async def detect_language_for_segment(self, segment_text: str) -> Tuple[Optional[str], float]:
        """
        Detect language for a single segment using Sarvam.
        
        Args:
            segment_text: Text of the segment to detect
        
        Returns:
            Tuple of (language_code, confidence)
        """
        if not self.enabled or not segment_text:
            return (None, 0.0)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"text": segment_text.strip()}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.lang_detect_url,
                    headers=headers,
                    json=payload,
                    timeout=5
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Sarvam returned {response.status}")
                        return (None, 0.0)
                    
                    result = await response.json()
                    
                    # Extract language from Sarvam response
                    raw_lang = (
                        result.get("language_code")
                        or result.get("language")
                        or result.get("detected_language")
                        or (result.get("data") or {}).get("language_code")
                        or (result.get("data") or {}).get("language")
                    )
                    
                    # Extract confidence
                    confidence = (
                        result.get("confidence", 0.7)
                        or (result.get("data") or {}).get("confidence", 0.7)
                    )
                    
                    lang_code = self._normalize_lang_code(raw_lang)
                    
                    logger.debug(
                        f"[SARVAM-SEGMENT] Text: '{segment_text[:50]}...' → "
                        f"Language: {lang_code} (confidence: {confidence:.2f})"
                    )
                    
                    return (lang_code, float(confidence))
        
        except asyncio.TimeoutError:
            logger.warning(f"Sarvam request timeout for segment: {segment_text[:50]}")
            return (None, 0.0)
        except Exception as e:
            logger.warning(f"Sarvam error for segment '{segment_text[:50]}': {e}")
            return (None, 0.0)
    
    async def detect_multilingual_predictions(
        self,
        text: str,
        fallback_language: str = "hi"
    ) -> MultilingualPrediction:
        """
        Detect language for each sentence/segment in text.
        
        Args:
            text: Full transcript text
            fallback_language: Language to use if detection fails
        
        Returns:
            MultilingualPrediction with per-segment language codes
        """
        logger.info(f"[SENTENCE-DETECT] Starting multilingual detection for {len(text)} chars")
        
        # Segment the text
        segments_data = self.segmenter.segment(text)
        logger.info(f"[SENTENCE-DETECT] Segmented into {len(segments_data)} segments")
        
        # Detect language for each segment
        segment_predictions = []
        language_counts = {}
        
        for i, seg_data in enumerate(segments_data):
            segment_text = seg_data['text']
            
            # Detect language
            lang_code, confidence = await self.detect_language_for_segment(segment_text)
            lang_code = lang_code or fallback_language
            
            # Create prediction
            prediction = SegmentPrediction(
                text=segment_text,
                language_code=lang_code,
                confidence=confidence,
                start_idx=seg_data['start'],
                end_idx=seg_data['end'],
                provider="sarvam"
            )
            segment_predictions.append(prediction)
            
            # Count languages
            language_counts[lang_code] = language_counts.get(lang_code, 0) + 1
            
            logger.debug(
                f"[SENTENCE-DETECT] Segment {i+1}/{len(segments_data)}: "
                f"{lang_code} (conf={confidence:.2f}) - '{segment_text[:40]}...'"
            )
        
        # Calculate language distribution
        total_segments = len(segment_predictions)
        language_distribution = {
            lang: count / total_segments
            for lang, count in language_counts.items()
        }
        
        # Determine primary language (most frequent)
        if segment_predictions:
            primary_language = max(language_counts, key=language_counts.get)
            primary_confidence = language_counts[primary_language] / total_segments
        else:
            primary_language = fallback_language
            primary_confidence = 0.0
        
        # Check if code-switched
        is_code_switched = len(language_counts) > 1
        
        # Build result
        result = MultilingualPrediction(
            full_text=text,
            segments=segment_predictions,
            primary_language=primary_language,
            primary_confidence=primary_confidence,
            language_distribution=language_distribution,
            is_code_switched=is_code_switched,
            metadata={
                'total_segments': total_segments,
                'language_count': len(language_counts),
                'segmentation_script': self.segmenter.detect_script(text),
            }
        )
        
        logger.info(
            f"[SENTENCE-DETECT] Complete: primary={primary_language} "
            f"(conf={primary_confidence:.2f}), code_switched={is_code_switched}, "
            f"languages={list(language_distribution.keys())}"
        )
        
        return result
    
    def format_predictions_for_tts(self, prediction: MultilingualPrediction) -> List[Dict]:
        """
        Format predictions for TTS synthesis with per-segment language codes.
        
        Returns:
            List of dicts: [{'text': segment, 'language': lang_code, 'confidence': conf}, ...]
        """
        return [
            {
                'text': seg.text,
                'language': seg.language_code,
                'confidence': seg.confidence,
                'start_idx': seg.start_idx,
                'end_idx': seg.end_idx,
            }
            for seg in prediction.segments
        ]
    
    def to_dict(self, prediction: MultilingualPrediction) -> Dict:
        """Convert prediction to dictionary for JSON serialization."""
        return {
            'full_text': prediction.full_text,
            'primary_language': prediction.primary_language,
            'primary_confidence': prediction.primary_confidence,
            'is_code_switched': prediction.is_code_switched,
            'language_distribution': prediction.language_distribution,
            'segments': [
                {
                    'text': seg.text,
                    'language_code': seg.language_code,
                    'confidence': seg.confidence,
                    'start_idx': seg.start_idx,
                    'end_idx': seg.end_idx,
                }
                for seg in prediction.segments
            ],
            'metadata': prediction.metadata,
        }


# Convenience function for STT pipeline integration
async def detect_multilingual_sentences(
    text: str,
    fallback_language: str = "hi"
) -> MultilingualPrediction:
    """
    Convenience function to detect language at sentence level.
    
    Usage:
        prediction = await detect_multilingual_sentences(transcript)
        for segment in prediction.segments:
            print(f"{segment.text} → {segment.language_code}")
    """
    detector = SentenceLevelLanguageDetector()
    return await detector.detect_multilingual_predictions(text, fallback_language)
