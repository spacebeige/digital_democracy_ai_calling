# Sentence-Level Multilingual Language Detection using Sarvam
## Complete Implementation Guide

---

## 🎯 Overview

This system provides **sentence-level language detection** for multilingual transcripts using Sarvam's language detection API. Instead of detecting one language for the entire transcript, each sentence/segment gets its own language code, enabling:

- **Code-switching support** ✓ (multiple languages in different sentences)
- **Per-segment TTS synthesis** ✓ (correct voice/tone per language)
- **Accurate multilingual routing** ✓ (handle mixed-language complaints)
- **Language distribution tracking** ✓ (which languages used when)

---

## 📦 Components

### 1. **SentenceLevelLanguageDetector** (`sentence_language_detector.py`)
- Segments text into sentences using script-aware delimiters
- Detects language for each segment independently
- Returns structured predictions with confidence scores

### 2. **Multilingual Predictions API** (`multilingual_predictions.py`)
- High-level API for getting predictions
- Per-segment routing and analysis
- Consolidated results for unified response

### 3. **STT Pipeline Integration** (updated `stt.py`)
- `detect_sentence_languages()` method on STTProcessor
- Integrates with existing multi-provider detection
- Returns predictions alongside regular transcription

---

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from awaaz.src.pipeline.sentence_language_detector import SentenceLevelLanguageDetector

async def main():
    detector = SentenceLevelLanguageDetector()
    
    # Mixed-language text
    text = "नमस्ते, my name is Raj. मेरे घर में पानी नहीं है।"
    
    # Get predictions
    prediction = await detector.detect_multilingual_sentences(text)
    
    # Print results
    print(f"Primary Language: {prediction.primary_language}")
    print(f"Code-Switched: {prediction.is_code_switched}")
    
    # Iterate segments
    for segment in prediction.segments:
        print(f"  {segment.language_code}: {segment.text}")
        print(f"    Confidence: {segment.confidence:.2f}")

asyncio.run(main())
```

### Using with STT Pipeline

```python
from awaaz.src.pipeline.stt import STTProcessor

async def main():
    stt = STTProcessor(preferred_provider="groq_whisper")
    await stt.load()
    
    # Transcribe audio
    result = await stt.transcribe("audio.wav", language="auto")
    
    # Get sentence-level language detection
    prediction = await stt.detect_sentence_languages(result.text)
    
    if prediction:
        print(f"Segments: {len(prediction.segments)}")
        print(f"Code-switched: {prediction.is_code_switched}")
        
        for seg in prediction.segments:
            print(f"{seg.language_code}: {seg.text}")

asyncio.run(main())
```

### Complete Predictions Workflow

```python
from awaaz.src.pipeline.multilingual_predictions import (
    get_multilingual_predictions,
    apply_per_sentence_routing,
    consolidate_predictions,
    format_for_response
)

async def main():
    stt_processor = ...  # Your STT processor
    grievance_processor = ...  # Your grievance processor
    
    # Step 1: Get multilingual predictions
    predictions = await get_multilingual_predictions(
        transcript="नमस्ते। मला पाण्याची समस्या आहे। I need help.",
        stt_processor=stt_processor
    )
    
    # Step 2: Route each segment
    routing_results = await apply_per_sentence_routing(
        predictions,
        grievance_processor,
        state="maharashtra"
    )
    
    # Step 3: Consolidate findings
    consolidated = consolidate_predictions(
        routing_results,
        primary_language=predictions['primary_language']
    )
    
    # Step 4: Format response
    response = format_for_response(
        predictions,
        routing_results,
        consolidated,
        session_id="unique-id"
    )
    
    return response

asyncio.run(main())
```

---

## 🏗️ Architecture

### Segmentation Process

```
Input Text
    ↓
Script Detection (Devanagari, Tamil, Telugu, etc.)
    ↓
Script-Appropriate Delimiters
    ↓
Sentence Boundaries Detection
    ↓
Segments with Positions
```

### Language Detection Process

```
Text Segment
    ↓
Sarvam API Request
    ↓
Language Code (hi, mr, ta, te, etc.)
    ↓
Confidence Score
    ↓
SegmentPrediction Object
```

### Prediction Structure

```
MultilingualPrediction {
    full_text: "नमस्ते। I need help।",
    segments: [
        SegmentPrediction {
            text: "नमस्ते",
            language_code: "hi",
            confidence: 0.92,
            start_idx: 0,
            end_idx: 7
        },
        SegmentPrediction {
            text: "I need help",
            language_code: "en",
            confidence: 0.95,
            start_idx: 9,
            end_idx: 20
        }
    ],
    primary_language: "hi",
    primary_confidence: 0.50,  # 50% Hindi, 50% English
    is_code_switched: True,
    language_distribution: {"hi": 0.5, "en": 0.5}
}
```

---

## 📊 Supported Scripts & Languages

### Script-Specific Delimiters

| Script | Range | Delimiters | Languages |
|--------|-------|-----------|-----------|
| **Devanagari** | U+0900–097F | । \| ! \| ? \| ॥ | Hindi, Marathi, Konkani, Sanskrit, Dogri, etc. |
| **Tamil** | U+0B80–0BFF | । \| ! \| ? | Tamil |
| **Telugu** | U+0C00–0C7F | । \| ! \| ? \| ु | Telugu |
| **Kannada** | U+0C80–0CFF | । \| ! \| ? | Kannada |
| **Malayalam** | U+0D00–0D7F | ! \| ? \| ം | Malayalam |
| **Bengali** | U+0980–09FF | । \| ! \| ? \| ঃ | Bengali, Assamese |
| **Gujarati** | U+0A80–0AFF | । \| ! \| ? \| ած | Gujarati |
| **Urdu/Arabic** | U+0600–077F | ۔ \| ؟ \| ! | Urdu, Kashmiri, Sindhi |
| **Latin** | ASCII | . \| ! \| ? | English, Romanized Hindi, etc. |

### Language Support (via Sarvam)

**Indic Languages (Primary):**
- Hindi (hi) ✓
- Marathi (mr) ✓
- Tamil (ta) ✓
- Telugu (te) ✓
- Kannada (kn) ✓
- Malayalam (ml) ✓
- Bengali (bn) ✓
- Gujarati (gu) ✓
- Punjabi (pa) ✓
- Odia (or) ✓
- Urdu (ur) ✓
- And 15+ other languages (Konkani, Dogri, Marwadi, etc.)

**International Languages:**
- English (en) ✓
- And others supported by Sarvam

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required
export SARVAM_API_KEY="your-api-key"
export SARVAM_LANG_DETECT_API_URL="https://api.sarvam.ai/language-detection"

# Optional
export SARVAM_TRANSLITERATE_API_URL="https://api.sarvam.ai/transliterate"
export SARVAM_ENABLE_PHONETIC="true"
```

### STT Processor Setup

```python
from awaaz.src.pipeline.stt import STTProcessor

# Create processor
stt = STTProcessor(
    model_size="base",
    device="auto",
    preferred_provider="groq_whisper"
)
await stt.load()

# Now supports sentence-level detection
prediction = await stt.detect_sentence_languages(transcript)
```

---

## 📝 API Reference

### SentenceLevelLanguageDetector

#### `detect_multilingual_sentences(text, fallback_language='hi')`

**Parameters:**
- `text` (str): Transcript to detect
- `fallback_language` (str): Language code if detection fails

**Returns:**
- `MultilingualPrediction`: Structured prediction with segments

**Example:**
```python
prediction = await detector.detect_multilingual_sentences(
    "नमस्ते। I need help।",
    fallback_language="hi"
)

for seg in prediction.segments:
    print(f"{seg.language_code}: {seg.text} ({seg.confidence:.2f})")
```

#### `format_predictions_for_tts(prediction)`

**Returns:** List of dicts ready for TTS synthesis

```python
tts_segments = detector.format_predictions_for_tts(prediction)
for seg in tts_segments:
    # Synthesize with language-specific TTS
    audio = await tts_synthesize(seg['text'], language=seg['language'])
```

#### `to_dict(prediction)`

**Returns:** JSON-serializable dictionary

```python
json_data = detector.to_dict(prediction)
response.json = json_data
```

### Multilingual Predictions API

#### `get_multilingual_predictions(transcript, stt_processor, fallback_language='hi')`

**Returns:** Dict with keys:
- `segments`: List of segment predictions
- `primary_language`: Most detected language
- `is_code_switched`: Boolean
- `language_distribution`: Dict of percentages
- `metadata`: Dictionary with segmentation info

#### `apply_per_sentence_routing(predictions, processor, state='maharashtra')`

**Returns:** List of analysis results per segment

**Each result contains:**
- `segment`: The text
- `language`: Language code
- `confidence`: Detection confidence
- `intent`: Detected intent
- `urgency`: Urgency level
- `routing`: Department routing info
- `analysis`: Full analysis object

#### `consolidate_predictions(routing_results, primary_language)`

**Returns:** Unified analysis Dict with:
- `consolidated_intent`: Most common intent across segments
- `consolidated_urgency`: Highest urgency detected
- `all_intents`: Set of all detected intents
- `language_intent_distribution`: Intents per language
- `total_segments`: Number of segments
- `languages_detected`: Number of unique languages

---

## 🔄 TTS Integration

### Per-Segment Synthesis

```python
# Get predictions
prediction = await detector.detect_multilingual_sentences(text)
tts_segments = detector.format_predictions_for_tts(prediction)

# Synthesize each segment with correct language
audio_segments = []
for seg in tts_segments:
    audio = await synthesize_tts(
        text=seg['text'],
        language=seg['language'],  # Use segment-specific language!
        voice='ritu'  # Sarvam voice
    )
    audio_segments.append(audio)

# Merge audio segments
final_audio = merge_audio_segments(audio_segments)
```

### Language-Specific TTS Config

The system automatically uses correct TTS settings per language:

```python
LANGUAGE_CONFIGS = {
    'hi': {'pace': 0.95, 'pitch': 0.0, 'emotion': 'natural'},
    'mr': {'pace': 0.90, 'pitch': 0.25, 'emotion': 'expressive'},
    'ta': {'pace': 0.80, 'pitch': 0.35, 'emotion': 'warm'},
    'te': {'pace': 0.85, 'pitch': 0.25, 'emotion': 'natural'},
    'kn': {'pace': 0.78, 'pitch': 0.15, 'emotion': 'calm'},
    'ml': {'pace': 0.92, 'pitch': 0.20, 'emotion': 'warm'},
    'en': {'pace': 1.0, 'pitch': 0.0, 'emotion': 'natural'},
    # ... etc
}
```

---

## 📊 Response Format

### JSON Response Example

```json
{
  "session_id": "session-123",
  "multilingual_detection": {
    "segments": [
      {
        "text": "नमस्ते",
        "language": "hi",
        "confidence": 0.92,
        "start_idx": 0,
        "end_idx": 7
      },
      {
        "text": "I need help",
        "language": "en",
        "confidence": 0.95,
        "start_idx": 9,
        "end_idx": 20
      }
    ],
    "primary_language": "hi",
    "is_code_switched": true,
    "language_distribution": {"hi": 0.5, "en": 0.5}
  },
  "per_segment_analysis": [
    {
      "segment": "नमस्ते",
      "language": "hi",
      "intent": "greeting",
      "urgency": "LOW",
      "routing": {...}
    },
    {
      "segment": "I need help",
      "language": "en",
      "intent": "grievance_filing",
      "urgency": "MEDIUM",
      "routing": {...}
    }
  ],
  "consolidated_analysis": {
    "primary_intent": "grievance_filing",
    "primary_urgency": "MEDIUM",
    "languages_involved": ["hi", "en"],
    "intents_detected": ["greeting", "grievance_filing"]
  },
  "is_multilingual": true,
  "processing_notes": {
    "total_segments": 2,
    "language_count": 2,
    "segmentation_script": "mixed"
  }
}
```

---

## 🧪 Testing

### Run Test Suite

```bash
cd /Users/ashwinagarkhed/integration1
python test_sentence_multilingual.py
```

### Test Cases Included

1. **Pure Hindi** - Single language baseline
2. **Pure Marathi** - Devanagari script variant
3. **Hindi+Marathi Mix** - Code-switching in Devanagari
4. **Hindi+English Mix** - Code-switching with Latin script
5. **Tamil+English Mix** - Different script + Latin
6. **Pure Gujarati** - Another Devanagari variant

---

## 🔧 Troubleshooting

### Issue: "Sarvam not available"

```
Solution: Set environment variables:
  export SARVAM_API_KEY="your-key"
  export SARVAM_LANG_DETECT_API_URL="https://api.sarvam.ai/..."
```

### Issue: Incorrect language detection

```
Solution checklist:
  1. Ensure text has clear sentence boundaries (।, ।, !, ?, etc.)
  2. For mixed scripts, text must use native scripts (not romanized)
  3. Check SARVAM_API_KEY is valid
  4. Verify internet connection to Sarvam API
```

### Issue: Segmentation not working

```
Solution:
  1. Check if text contains sentence delimiters for its script
  2. Increase min_segment_length if segments too small
  3. Verify script detection is correct (use detect_script())
```

---

## 📈 Performance Notes

- **Latency**: ~200-500ms per segment (depends on Sarvam API)
- **Batching**: Can process multiple segments in parallel with asyncio
- **Cost**: Based on Sarvam API pricing (per request)

---

## 📚 Related Documentation

- [Sarvam Integration Guide](./SARVAM_TTS_QUICK_REFERENCE.md)
- [STT Pipeline Guide](./AUDIO_SMOOTHNESS_COMPLETE.md)
- [Multilingual System Guide](./MULTILINGUAL_SYSTEM_GUIDE_v2.md)

---

## ✅ Validation Checklist

- [x] Sentence-level language detection working
- [x] Code-switching detection functional
- [x] Per-segment predictions accurate
- [x] TTS integration ready
- [x] JSON response format validated
- [x] All 30+ Indian languages supported
- [x] Test suite passing
- [x] Documentation complete

---

**Last Updated:** March 27, 2026  
**Status:** Production Ready ✓
