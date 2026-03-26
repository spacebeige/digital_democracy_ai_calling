# STT Language Resolution Fix - High Confidence Ensemble Preservation

## Problem Identified

When STT received Marathi audio (e.g., "या समस्येवर..."), the ensemble correctly detected **Marathi (mr) with 0.98 confidence** from ElevenLabs. However, the `_resolve_result_language` function was re-voting using Sarvam's **text language detection** on the transcribed text:

```log
Step 5: Sarvam text language detection votes for Hindi with weight 0.70
Result: Hindi (0.70) > Marathi (ensemble votes) → Language switched to Hindi ❌
```

## Root Cause

The voting system was treating all votes equally regardless of ensemble confidence level. When Sarvam detected the transcribed text language, it had enough weight (0.70) to override high-confidence ensemble detection.

## Solution Applied

**File**: [awaaz/src/pipeline/stt.py](awaaz/src/pipeline/stt.py#L799-L804)

Added a **high-confidence check** to skip text-based re-detection when ensemble already has very high confidence:

```python
# NEW LOGIC (lines 799-804):
ensemble_max_conf = max(ensemble_scores.values()) if ensemble_scores else 0.0
if ensemble_max_conf < 0.95:  # Only re-vote if ensemble is uncertain
    sarvam_text_lang = await self.sarvam.detect_language_from_text(text, fallback=None)
    add_vote(sarvam_text_lang, 0.70)
```

## Expected Behavior After Fix

### Scenario 1: High-Confidence Ensemble (e.g., Marathi)

```log
Input: Marathi audio
Step 1-4: Various detectors + Ensemble votes
Ensemble: mr=0.98 (confidence > 0.95) ✅
Step 5: SKIP Sarvam text detection (confidence is high)
Result: Marathi PRESERVED ✅
```

### Scenario 2: Low-Confidence Ensemble (Uncertain)

```log
Input: Ambiguous audio
Ensemble: multiple ~0.5 votes (confidence < 0.95)
Step 5: CALL Sarvam text detection (ensemble is uncertain)
Result: Sarvam vote helps break tie ✅
```

## Impact

- ✅ **Marathi conversations** now preserve language through STT→TTS pipeline
- ✅ **Any high-confidence language** detection (>0.95) is now trusted
- ✅ **Uncertain cases** still benefit from Sarvam's text-based detection as a tie-breaker
- ✅ **Network optimization**: Fewer Sarvam API calls for high-confidence cases

## Verification

The fix ensures that when audio ensemble detection reaches >95% confidence, the transcribed text language detection does NOT override it with a re-vote.
