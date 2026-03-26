# Audio Smoothness - Language Configuration Reference

## Quick Reference: Optimized Voice Settings for Smooth Audio

### South Indian Languages (Slower for Clarity)
These languages have longer phonetic sequences and benefit from slower delivery.

```
Tamil (ta)
  Pace: 0.78 (SLOWEST - clear vowel emphasis)
  Pitch: 0.15 (high - melodic language)
  Emotion: warm
  → Result: Clear, melodic Tamil with natural pacing

Telugu (te)
  Pace: 0.82 (slow - consonant clarity)
  Pitch: 0.12 (medium-high)
  Emotion: natural
  → Result: Clear Telugu consonants, natural rhythm

Kannada (kn)
  Pace: 0.76 (SLOWEST - measured delivery)
  Pitch: 0.08 (medium)
  Emotion: calm
  → Result: Deliberate, precise Kannada pronunciation

Tulu (tcy)
  Pace: 0.77 (slow - similar to Kannada)
  Pitch: 0.10 (medium)
  Emotion: warm
  → Result: Warm, clear Tulu with melodic flow

Malayalam (ml)
  Pace: 0.90 (moderate - balanced phonetics)
  Pitch: 0.10 (medium)
  Emotion: warm
  → Result: Natural melodic Malayalam
```

### North Indian Languages (Natural Pace)
These languages mix with Hindi/Urdu and use Devanagari script.

```
Hindi (hi)
  Pace: 0.93 (standard - reference speed)
  Pitch: 0.0 (neutral reference)
  Emotion: natural
  → Result: Standard, clear Hindi delivery

Marathi (mr)
  Pace: 0.88 (slightly slower than Hindi)
  Pitch: 0.10 (slight expression)
  Emotion: warm
  → Result: Warm, expressive Marathi

Konkani (kok)
  Pace: 0.87 (similar to Marathi)
  Pitch: 0.10 (medium expression)
  Emotion: warm
  → Result: Smooth, warm Konkani tone

Bhojpuri (bho)
  Pace: 0.86 (slower - rural phonetics)
  Pitch: 0.12 (more expressive)
  Emotion: warm
  → Result: Warm, expressive Bhojpuri

Dogri (doi)
  Pace: 0.92 (moderate)
  Pitch: 0.08 (slight variation)
  Emotion: warm
  → Result: Warm Dogri delivery

Awadhi (awa)
  Pace: 0.90 (moderate)
  Pitch: 0.10 (expression)
  Emotion: warm
  → Result: Warm Awadhi tone

Haryanvi (bgc)
  Pace: 0.94 (moderate-fast)
  Pitch: 0.10 (slight expression)
  Emotion: natural
  → Result: Natural Haryanvi delivery

Marwadi (mwr)
  Pace: 0.92 (moderate)
  Pitch: 0.08 (slight variation)
  Emotion: natural
  → Result: Natural Marwadi tone

Maithili (mai)
  Pace: 0.90 (moderate)
  Pitch: 0.10 (expression)
  Emotion: warm
  → Result: Warm Maithili delivery
```

### Eastern Languages (Smooth Neutral)
These languages use Bengali/Odia scripts and benefit from smooth, neutral delivery.

```
Bengali (bn)
  Pace: 0.90 (moderate)
  Pitch: 0.05 (minimal variation - neutral)
  Emotion: natural
  → Result: Smooth, neutral Bengali

Odia (or)
  Pace: 0.88 (slightly slower)
  Pitch: 0.08 (slight variation)
  Emotion: natural
  → Result: Smooth, measured Odia

Assamese (as)
  Pace: 0.91 (moderate)
  Pitch: 0.07 (slight variation)
  Emotion: natural
  → Result: Smooth, natural Assamese
```

### Western Languages (Energetic)
These languages benefit from faster, more energetic delivery.

```
Gujarati (gu)
  Pace: 0.96 (fast - energetic)
  Pitch: 0.15 (high - lively)
  Emotion: warm
  → Result: Lively, warm Gujarati delivery

Punjabi (pa)
  Pace: 0.95 (fast - energetic)
  Pitch: 0.12 (medium-high)
  Emotion: natural
  → Result: Energetic, clear Punjabi delivery
```

### Other Languages

```
English (en)
  Pace: 0.98 (neutral-fast)
  Pitch: 0.0 (neutral)
  Emotion: natural
  → Result: Clear, natural English

Sinhala (si)
  Pace: 0.91 (moderate)
  Pitch: 0.10 (medium)
  Emotion: warm
  → Result: Warm Sinhala tone

Urdu (ur)
  Pace: 0.88 (moderate)
  Pitch: 0.10 (medium)
  Emotion: warm
  → Result: Warm Urdu delivery
```

---

## How These Settings Work Together

### Scenario: Georgian complaint in Tamil

1. **Language Detection**: STT identifies Tamil (ta) with high confidence
2. **Speaker Selection**: Selects "ritu" (Ritu) female voice
3. **Pace Application**: Uses 0.78 pace → slower, clearer Tamil
4. **Pitch Control**: Applies 0.15 pitch → melodic Tamil characteristics
5. **Emotion Setting**: Uses "warm" → friendly, approachable tone
6. **Text Chunking**: Splits at 400 chars max for natural pauses
7. **Speech Naturalizer**: Applies Tamil phonetic rules (if any)
8. **Audio Merging**: Connects chunks with smooth crossfade
9. **Prosody Control**: Applies pause timing and formality adjustments

**Result**: Smooth, natural Tamil audio with clear pronunciation and appropriate pacing!

---

## Configuration Impact by Language Family

### South Indian (Pace Range: 0.76-0.90)
- **Characteristic**: Longer phonetic sequences, distinct consonants
- **Improvement**: Slower pace allows clearer pronunciation
- **User Experience**: Complaint sounds clear, professional, unhurried
- **Example**: Tamil "வணக்கம்" (vanakkam) is clearly pronounced

### North Indian (Pace Range: 0.86-0.95)
- **Characteristic**: Mixed vowel-consonant patterns, dialect variations
- **Improvement**: Moderate pace with warm emotion allows natural expression
- **User Experience**: Complaint sounds friendly, expressive, personable
- **Example**: Hindi "कृपया" (kripaya) sounds warm and genuine

### Eastern (Pace Range: 0.88-0.91)
- **Characteristic**: Neutral phonetics, smooth flowing speech
- **Improvement**: Neutral pitch and emotion for clarity
- **User Experience**: Complaint sounds smooth, professional, balanced
- **Example**: Bengali "অনুগ্রহ" (onugro) flows naturally

### Western (Pace Range: 0.95-0.96)
- **Characteristic**: Energetic language patterns, faster spoken naturally
- **Improvement**: Faster pace with warm emotion captures natural energy
- **User Experience**: Complaint sounds engaging, energetic, lively
- **Example**: Gujarati sounds animated and friendly

---

## Before & After Comparison

### Example: Marathi Complaint Acknowledgment

**Before Enhancement**:
```
Text: "कृपया आपल्या तक्रारीवर लक्ष देण्यात येईल"
Audio: Generic pace (1.0), neutral emotion, abrupt transitions
Sound: Robotic, generic, disconnected
Effect: User feels unheard, generic response
```

**After Enhancement**:
```
Text: "कृपया आपल्या तक्रारीवर लक्ष देण्यात येईल"
Settings: pace=0.88, pitch=0.10, emotion=warm
Sound: Smooth, warm, natural pacing, proper pronunciation
Effect: User feels valued, response is personalized
Audio: "कृ-पया आपल्या [pause] तक्रारीवर [pause] लक्ष देण्यात येईल"
       ↑ Warm tone     ↑ Natural pause  ↑ Professional delivery
Result: Professional, caring, personalized audio response
```

---

## Loudness Consistency

**All languages**: Loudness = 1.5 (uniform)
- Ensures no volume jumps when switching languages
- Maintains consistent listening experience
- Prevents ear fatigue from volume spikes

---

## Emotion Settings

### Warm (Used for Languages That Benefit from Expressiveness)
- Languages: Tamil, Telugu, Marathi, Konkani, Bhojpuri, Gujarati, etc.
- Effect: Adds friendliness, approachability, genuine care
- Use Case: Complaint acknowledgment (show you care about the issue)

### Natural (Used for Neutral/Professional Delivery)
- Languages: Hindi, Telugu, Odia, Assamese, Bengali, English, etc.
- Effect: Clear, professional, unbiased delivery
- Use Case: Information delivery, announcements

### Calm (Used for Careful, Deliberate Delivery)
- Languages: Kannada, Tulu
- Effect: Measured, careful, thoughtful tone
- Use Case: Important information, sensitive topics

---

## Pitch Variation Explanation

**Pitch = 0.0** (None): English, Hindi
- Neutral reference, no tonal variation
- Result: Clear, standard pronunciation

**Pitch = 0.05-0.08** (Low): Bengali, Odia, Assamese, Kannada, Dogri
- Minimal melodic variation
- Result: Smooth, measured delivery

**Pitch = 0.10-0.12** (Medium): Marathi, Konkani, Bhojpuri, Gujarati, Telugu, Malayalam, Sinhala, Urdu
- Balance between clarity and melodic flow
- Result: Natural, expressive delivery

**Pitch = 0.15** (High): Tamil, Gujarati
- Emphasizes melodic language characteristics
- Result: Melodic, engaging delivery

---

## Practical Usage

### To generate smooth audio for a native language complaint:

```python
from awaaz.src.pipeline.tts import SARVAM_SPEAKER_MAP, synthesize_speech

# Example: Tamil complaint acknowledgment
complaint_text_ta = "உங்கள் புகாரை உடனடியாக தீர்க்க நாங்கள் செயல்பட்டு வருகிறோம்"
lang_code = "ta"

# The system automatically uses optimized settings:
# pace=0.78, pitch=0.15, emotion=warm → smooth, clear Tamil

# Generate audio
audio_bytes = synthesize_speech(
    text=complaint_text_ta,
    lang=lang_code,
    lang_name="Tamil"
)

# Result: Smooth, natural Tamil audio with:
#   - Clear pronunciation
#   - Warm, caring tone
#   - Natural pacing
#   - Melodic flow (pitch=0.15)
#   - Professional sound
```

---

**Key Takeaway**: All 22 core languages + 30+ variants now have voice settings optimized for smooth, natural-sounding audio delivery that respects each language's unique characteristics! 🎙️
