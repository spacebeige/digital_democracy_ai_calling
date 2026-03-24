# Testing Voice-to-NLP Pipeline with Live Audio

## Quick Start

### Step 1: Make sure the API server is running

```bash
cd backend
source ../venv/bin/activate
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Wait for: `Uvicorn running on http://127.0.0.1:8000`

### Step 2: Test with live microphone (in another terminal)

```bash
cd /home/parth/Desktop/indiainnovates/digital_democracy_ai_calling
source venv/bin/activate
python3 voice_to_analysis_integration.py --mode mic
```

**What happens:**
1. Microphone records your voice (~10 seconds max)
2. Speech-to-Text transcribes what you said
3. Transcript sent to post-call analyzer
4. Analysis results displayed

**Example interaction:**
```
🎤 Speak now: "Water is leaking from the pipe in my house"
[STT] ✓ Transcribed
[API] ✓ Analysis complete

📊 RESULTS:
  Intent: NEW_COMPLAINT
  Department: Water & Sewerage
  Priority: MEDIUM
  Action: CREATE_TICKET
```

### Step 3: Test with audio file

```bash
python3 voice_to_analysis_integration.py --mode file --input /path/to/audio.wav --lang hi
```

### Step 4: Test with awaaz's test_live_voice.py

This is the original test that captures voice and generates AI response:

```bash
cd awaaz
python3 test_live_voice.py --mode mic --lang hi
```

Options:
- `--mode mic` - Record from microphone (default)
- `--mode file` - Use audio file
- `--lang hi` - Language (hi, en, ta, mr, etc.)
- `--duration 10` - Max recording time in seconds
- `--output response.wav` - Save AI response audio

---

## Testing Scenarios

### Scenario 1: Water Leak Complaint
**What to say:** "There is water leaking from a pipe near my house in Sector 5"
**Expected Result:** 
- Intent: NEW_COMPLAINT
- Department: Water & Sewerage
- Priority: MEDIUM

### Scenario 2: Emergency
**What to say:** "FIRE! My building is on fire! Please help immediately!"
**Expected Result:**
- Emergency: YES (🔴)
- Priority: EMERGENCY
- Action: TRANSFER_TO_HUMAN

### Scenario 3: Status Query
**What to say:** "What is the status of my complaint filed yesterday?"
**Expected Result:**
- Intent: STATUS_QUERY
- Department: General
- Action: TRANSFER_TO_HUMAN (requires lookup)

### Scenario 4: Feedback
**What to say:** "Thank you for fixing the road in my area"
**Expected Result:**
- Intent: FEEDBACK
- Priority: LOW
- Action: STORE_FEEDBACK

---

## Pipeline Architecture

```
┌──────────────────┐
│  Live Microphone │
│  or Audio File   │
└────────┬─────────┘
         │
         ↓
┌──────────────────────┐
│  awaaz STT Pipeline  │
│ (Speech-to-Text)     │
└────────┬─────────────┘
         │
         ↓
┌──────────────────────┐
│  Full Transcript     │
│  Saved              │
└────────┬─────────────┘
         │
         ↓
┌──────────────────────────────┐
│  Post-Call Analysis API      │
│  /api/v1/analysis/analyze    │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  NLP Classification:         │
│  • Language Detection        │
│  • Intent Classification     │
│  • Emergency Detection       │
│  • Issue Category Detection  │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  Smart Routing:              │
│  • Department Assignment     │
│  • Priority Level            │
│  • Suggested Action          │
│  • Confidence Scoring        │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  Analysis Results            │
│  (Displayed to User)         │
└──────────────────────────────┘
```

---

## Troubleshooting

### "Analysis API not available"
Make sure the backend server is running:
```bash
cd backend
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### "awaaz_recorder not available"
Either install it or test with a file:
```bash
python3 voice_to_analysis_integration.py --mode file --input sample.wav
```

### "No transcript generated"
- Check microphone input: `arecord -l`
- Try with a test audio file instead
- Ensure audio is not too quiet or noisy

### "API returns error"
Check the backend terminal for detailed error messages. The error will show which step failed.

---

## Advanced Testing

### Test batch analysis
```bash
curl -X POST http://127.0.0.1:8000/api/v1/analysis/batch-analyze \
  -H "Content-Type: application/json" \
  -d '[
    {"call_id": "1", "session_id": "s1", "transcript": "Water leak", "call_duration_seconds": 180},
    {"call_id": "2", "session_id": "s2", "transcript": "Fire!", "call_duration_seconds": 60}
  ]'
```

### Test with Hindi input
```bash
python3 voice_to_analysis_integration.py --mode mic --lang hi
```
(Speak in Hindi and the system will detect the language automatically)

### Test with different languages
Supported: hi, en, ta, te, kn, ml, gu, bn, pa, mr, and more

---

## Monitoring Performance

The API returns `processing_time_ms` which shows how fast the analysis runs:
- **Expected:** 10-50ms for NLP classification
- **Good:** < 100ms total including routing

---

## Next Steps After Testing

1. ✅ Voice capture works
2. ✅ Transcription works
3. ✅ Analysis API works
4. **Next:** Connect to database to store results
5. **Next:** Implement action execution (create tickets, send notifications)
6. **Next:** Add human fallback for complex cases
7. **Next:** Deploy to production
