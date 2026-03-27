#!/usr/bin/env python3
"""
Multilingual Predictions Helper
================================

Provides utilities for handling predictions with per-sentence language codes
using Sarvam for sentence-level language detection.

Usage:
    from multilingual_predictions import get_multilingual_predictions, apply_per_sentence_routing
    
    # Get predictions with language codes per sentence
    predictions = await get_multilingual_predictions(transcript)
    
    # Apply routing and TTS per sentence
    results = await apply_per_sentence_routing(predictions, processor)
"""

import logging
from typing import List, Dict, Optional
import asyncio

logger = logging.getLogger(__name__)


async def get_multilingual_predictions(
    transcript: str,
    stt_processor=None,
    fallback_language: str = "hi"
) -> Dict:
    """
    Get multilingual predictions with per-sentence language codes.
    
    Args:
        transcript: Full transcript text
        stt_processor: STTProcessor instance
        fallback_language: Language code for fallback
    
    Returns:
        Dict with keys:
          - segments: List of segments with language codes
          - primary_language: Most detected language
          - is_code_switched: Boolean for code-switching
          - language_distribution: Dict of language percentages
          - raw_prediction: Raw MultilingualPrediction object
    """
    logger.info(f"[PREDICTIONS] Getting multilingual predictions for {len(transcript)} chars")
    
    if not stt_processor:
        logger.warning("No STT processor provided, using sentence detector directly")
        try:
            from awaaz.src.pipeline.sentence_language_detector import SentenceLevelLanguageDetector
            detector = SentenceLevelLanguageDetector()
            prediction = await detector.detect_multilingual_sentences(transcript, fallback_language)
        except Exception as e:
            logger.error(f"Failed to get predictions: {e}")
            return {
                'segments': [{'text': transcript, 'language': fallback_language, 'confidence': 0.0}],
                'primary_language': fallback_language,
                'is_code_switched': False,
                'language_distribution': {fallback_language: 1.0},
                'error': str(e)
            }
    else:
        try:
            prediction = await stt_processor.detect_sentence_languages(transcript, fallback_language)
            if not prediction:
                raise RuntimeError("Sentence detector returned None")
        except Exception as e:
            logger.error(f"Failed to get predictions from STT processor: {e}")
            return {
                'segments': [{'text': transcript, 'language': fallback_language, 'confidence': 0.0}],
                'primary_language': fallback_language,
                'is_code_switched': False,
                'language_distribution': {fallback_language: 1.0},
                'error': str(e)
            }
    
    # Format for return
    result = {
        'segments': [
            {
                'text': seg.text,
                'language': seg.language_code,
                'confidence': seg.confidence,
                'start_idx': seg.start_idx,
                'end_idx': seg.end_idx,
            }
            for seg in prediction.segments
        ],
        'primary_language': prediction.primary_language,
        'primary_confidence': prediction.primary_confidence,
        'is_code_switched': prediction.is_code_switched,
        'language_distribution': prediction.language_distribution,
        'metadata': prediction.metadata,
        'raw_prediction': prediction,  # Keep reference to original
    }
    
    logger.info(
        f"[PREDICTIONS] Got {len(result['segments'])} segments, "
        f"primary={result['primary_language']}, code_switched={result['is_code_switched']}"
    )
    
    return result


async def apply_per_sentence_routing(
    predictions: Dict,
    processor,
    state: str = "maharashtra"
) -> List[Dict]:
    """
    Apply AI analysis and routing per sentence.
    
    Returns:
        List of analysis results per segment:
          [
            {
              'segment': segment_text,
              'language': language_code,
              'intent': primary_intent,
              'urgency': urgency_level,
              'routing': routing_info,
              'analysis': full_analysis
            },
            ...
          ]
    """
    logger.info(f"[ROUTING] Applying per-sentence routing for {len(predictions['segments'])} segments")
    
    results = []
    
    for idx, segment in enumerate(predictions['segments']):
        segment_text = segment['text']
        language_code = segment['language']
        
        logger.info(f"[ROUTING] Processing segment {idx+1}/{len(predictions['segments'])}: {language_code}")
        
        try:
            # Run AI analysis on this segment
            analysis = processor.process_grievance(
                session_id=None,  # Use parent session
                transcript=segment_text,
                audio_data=None,
                sample_rate=16000,
                detected_language=language_code,
                state=state,
            )
            
            # Apply routing
            analysis, escalation = processor.apply_routing_and_escalation(
                analysis,
                transcript=segment_text,
                time_since_filing_minutes=0,
                num_previous_calls=0,
            )
            
            segment_result = {
                'segment': segment_text,
                'language': language_code,
                'confidence': segment.get('confidence', 0.0),
                'intent': analysis.intent.primary_intent if analysis.intent else None,
                'urgency': analysis.intent.urgency_level.name if analysis.intent and analysis.intent.urgency_level else "MEDIUM",
                'routing': {
                    'department': analysis.routing.department if analysis.routing else None,
                    'sub_department': analysis.routing.sub_department if analysis.routing else None,
                    'category': analysis.routing.category if analysis.routing else None,
                },
                'analysis': analysis,
            }
            results.append(segment_result)
            
        except Exception as e:
            logger.warning(f"Analysis failed for segment {idx+1}: {e}")
            results.append({
                'segment': segment_text,
                'language': language_code,
                'error': str(e),
            })
    
    logger.info(f"[ROUTING] Completed routing for {len(results)} segments")
    return results


def consolidate_predictions(predictions: List[Dict], primary_language: str) -> Dict:
    """
    Consolidate per-segment predictions into unified format.
    
    Returns:
        Dict with consolidated analysis:
          - segments: Original segment analysis
          - consolidated_intent: Most common intent
          - consolidated_urgency: Highest urgency
          - all_intents: Set of all detected intents
          - all_urgencies: Set of all detected urgencies
          - language_distribution: Which languages had which intents
    """
    logger.info(f"[CONSOLIDATE] Consolidating {len(predictions)} segment predictions")
    
    intents = []
    urgencies = []
    language_intent_map = {}
    
    for pred in predictions:
        if 'intent' in pred and pred['intent']:
            intents.append(pred['intent'])
        
        if 'urgency' in pred and pred['urgency']:
            urgencies.append(pred['urgency'])
        
        lang = pred.get('language', 'unknown')
        if lang not in language_intent_map:
            language_intent_map[lang] = []
        if 'intent' in pred:
            language_intent_map[lang].append(pred['intent'])
    
    # Determine consolidated values
    from collections import Counter
    
    intent_counts = Counter(intents) if intents else {}
    urgency_counts = Counter(urgencies) if urgencies else {}
    
    consolidated_intent = intent_counts.most_common(1)[0][0] if intent_counts else None
    
    # Urgency priority: HIGH > CRITICAL > MEDIUM > LOW
    urgency_priority = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    consolidated_urgency = max(
        urgency_counts.keys(),
        key=lambda x: urgency_priority.get(x, 0)
    ) if urgency_counts else "MEDIUM"
    
    result = {
        'segments': predictions,
        'consolidated_intent': consolidated_intent,
        'consolidated_urgency': consolidated_urgency,
        'all_intents': set(intents),
        'all_urgencies': set(urgencies),
        'language_intent_distribution': language_intent_map,
        'total_segments': len(predictions),
        'languages_detected': len(language_intent_map),
    }
    
    logger.info(
        f"[CONSOLIDATE] Consolidated: intent={consolidated_intent}, "
        f"urgency={consolidated_urgency}, languages={list(language_intent_map.keys())}"
    )
    
    return result


def format_for_response(
    predictions: Dict,
    routing_results: List[Dict],
    consolidated: Dict,
    session_id: str,
) -> Dict:
    """
    Format all prediction data into response structure.
    """
    return {
        'session_id': session_id,
        'multilingual_detection': {
            'segments': predictions['segments'],
            'primary_language': predictions['primary_language'],
            'is_code_switched': predictions['is_code_switched'],
            'language_distribution': predictions['language_distribution'],
        },
        'per_segment_analysis': routing_results,
        'consolidated_analysis': {
            'primary_intent': consolidated['consolidated_intent'],
            'primary_urgency': consolidated['consolidated_urgency'],
            'languages_involved': list(consolidated['language_intent_distribution'].keys()),
            'intents_detected': list(consolidated['all_intents']),
        },
        'is_multilingual': predictions['is_code_switched'],
        'processing_notes': {
            'total_segments': predictions['metadata'].get('total_segments'),
            'language_count': predictions['metadata'].get('language_count'),
            'segmentation_script': predictions['metadata'].get('segmentation_script'),
        }
    }
