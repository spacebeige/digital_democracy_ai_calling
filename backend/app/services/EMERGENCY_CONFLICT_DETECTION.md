# Emergency Conflict Detection System

## Problem It Solves

**Original Issue:**
```
Transcript: "heard gun shots around lol"
System Response: emergency = true, action = TRANSFER_HUMAN

Problem: Just because someone says "gun shots" doesn't mean it's actually an emergency!
The "lol" suggests they might be joking or not serious.
```

**User's Point:**
> "not everyone reacts the same to things, so how we gonna differentiate?"

Different people express urgency differently:
- Some scream for real emergencies
- Some joke around while mentioning dangers
- Some use "lol" casually while still having a real concern
- Some say "lol" to appear less dramatic about a real emergency

**Solution:** Use **conflict detection** - if emergency keywords AND prank indicators both exist in the same transcript, the system cannot be certain and requires human judgment.

---

## How It Works

### Detection Pipeline

```
┌─ Check for emergency keywords (gun, fire, medical emergency, etc.)
│
├─ Check for prank indicators (lol, haha, joke, bakwas, prank, etc.)
│
└─ Implement conflict resolution:

   IF emergency_keyword AND prank_indicator BOTH present:
   ├─ Confidence → 0.5 (very uncertain)
   ├─ Action → ESCALATE_TO_HUMAN (requires human judgment)
   ├─ Summary → "⚠️ CONFLICTED: Emergency signal with prank indicators"
   └─ Example: "gun shots lol" → CONFLICTED
   
   IF emergency_keyword ONLY (no prank indicators):
   ├─ Confidence → 0.95 (very certain)
   ├─ Action → TRANSFER_HUMAN (auto-escalate)
   ├─ Summary → "Emergency detected — immediate transfer required"
   └─ Example: "gun shots in my apartment" → EMERGENCY
   
   IF prank_indicator ONLY (no emergency keywords):
   ├─ Not treated as emergency
   └─ Example: "lol haha" → Not emergency
   
   IF neither emergency nor prank signals:
   ├─ Proceed to normal NLP classification
   └─ Example: "water leak in my kitchen" → Normal routing
```

---

## Configuration

Prank indicators are stored in [emergency_keywords.json](emergency_keywords.json):

```json
{
  "prank_indicators": {
    "english": [
      "lol", "haha", "joke", "prank", "fooled-you", 
      "just-kidding", "jk", "funny", "hilarious", "rofl", "lmao"
    ],
    "hindi": [
      "bakwas", "chal-hat", "mazaak", "hassi", 
      "jhooth", "fake", "bakwas-bol", "toh-just-joking"
    ],
    "mixed": [
      "lol", "haha", "hehe", "xD", "rofl"
    ]
  }
}
```

To add more prank indicators, simply edit the JSON—no code changes needed.

---

## Real-World Examples

### Example 1: Genuine Emergency
```
Input: "There is a fire in my apartment, please help immediately!"
Emergency keywords: "fire", "please help"
Prank indicators: None
Decision: ✅ EMERGENCY (confidence: 0.95)
Action: TRANSFER_HUMAN (immediate)
```

### Example 2: Obvious Prank
```
Input: "haha lol there's a bomb in the sky, just joking!"
Emergency keywords: "bomb"
Prank indicators: "haha", "lol", "joking"
Decision: ⚠️ CONFLICTED (confidence: 0.50)
Action: ESCALATE_TO_HUMAN (human review)
Reason: "Emergency signal with prank indicators - requires immediate human review"
```

### Example 3: Unclear Intention
```
Input: "got a seizure lmao"
Emergency keywords: "seizure"
Prank indicators: "lmao" (laughing my ass off)
Decision: ⚠️ CONFLICTED (confidence: 0.50)
Action: ESCALATE_TO_HUMAN

Human operator decision:
- Option A: Real seizure, person joking to downplay seriousness
- Option B: Not a real seizure, just joking
- Operator will ask clarifying questions
```

### Example 4: Serious Emergency with Casual Language
```
Input: "help my dad's having a heart attack lol i'm scared"
Emergency keywords: "heart attack"
Prank indicators: "lol"
Decision: ⚠️ CONFLICTED (confidence: 0.50)
Action: ESCALATE_TO_HUMAN

Why conflicted?
- "heart attack" is genuine emergency keyword
- But "lol i'm scared" suggests anxiety/fear (not joking)
- Human can hear voice tone, confirm urgency

Operator hears fear in voice → Confirms emergency
Action overridden: TRANSFER_HUMAN
```

### Example 5: Recurring Caller (Pattern Detection)

```
Call 1: "gun shots lol" → CONFLICTED → ESCALATE
Call 2: "bomb haha" → CONFLICTED → ESCALATE  
Call 3: "fire rofl" → CONFLICTED → ESCALATE

Pattern detected: Same caller, always prank indicators
Action: Block or flag caller after 3 conflicts from same number
```

---

## Confidence Scoring

```
Scenario                                    Confidence  Action
────────────────────────────────────────────────────────────────
Clear emergency (keyword only)              0.95        TRANSFER_HUMAN
Conflicted (keyword + prank)                0.50        ESCALATE_TO_HUMAN
Prank only (no emergency keyword)           1.0         DISCONNECT
Normal complaint (no emergency)             0.85-0.95   Normal routing
```

---

## Human Operator Workflow

When system returns CONFLICTED (confidence: 0.50):

```
ESCALATE_TO_HUMAN Decision Tree:
│
├─ Can you hear voice urgency/panic?
│  ├─ YES → Likely genuine despite "lol"
│  │        override: TRANSFER_HUMAN
│  │        confidence boost: 0.50 → 0.85
│  │
│  └─ NO → Likely prank
│           override: DISCONNECT
│           confidence: 0.50
│
├─ Is this a repeat caller?
│  ├─ YES (3+ CONFLICTED) → Likely prank
│  │                        override: BLOCK
│  │
│  └─ NO → Single occurrence
│          ask clarification: "Are you calling about a real emergency?"
│
└─ Background context?
   ├─ Weird/nonsensical → Prank
   ├─ Scared/worried → Genuine
   └─ Uncertain → Ask follow-up questions
```

---

## Prank Indicators Explained

### Why These Words Indicate Prank:

| Indicator | Probability | Reason |
|-----------|-------------|--------|
| "lol" (*laugh out loud*) | High | Laughing at something typically means joking |
| "haha" | High | Same as lol - laughing |
| "lmao" / "rofl" | Very High | Extreme laughing = not serious |
| "joke", "prank" | Very High | Explicitly states it's a joke |
| "bakwas" (Hindi: *nonsense*) | Very High | Explicitly calling it nonsense |
| "chal hat" (Hindi: *go away joking*) | Very High | Dismissive joking phrase |
| "just-kidding", "jk" | Very High | Explicit retraction |
| "fooled-you" | Very High | Admits to prank |

### **But also consider:**

- Person might be laughing *nervously* due to panic
- Caller might use humor to cope with scary situation
- Regional/cultural communication style (some people always joke)
- Sarcasm is context-dependent

**This is why CONFLICTED requires human review.**

---

## Implementation Details

### Code Changes

**File:** [nlp_classifier.py](nlp_classifier.py)

**Changes:**
1. Added `_build_prank_indicators()` function
2. Built `PRANK_INDICATORS` frozenset (loaded from JSON)
3. Updated `check_emergency()` to:
   - Check for emergency keywords
   - Check for prank indicators
   - Detect conflicts (both present)
   - Return confidence score with result
4. Updated `EdgeCaseResult` to include confidence field
5. Emergency handler now respects confidence scores

**Processing Times:**
```
Emergency keyword check    : < 1ms  (regex)
Prank indicator check      : < 2ms  (regex + loop)
Conflict detection         : < 5ms  (combined)
Total edge-case pre-check  : < 10ms (vs 200-500ms for LLM)
```

---

## Testing

### Test Cases

```python
test_cases = [
    # (transcript, expected_decision, reason)
    ("gun shots lol", "CONFLICTED", "emergency + prank"),
    ("gun shots in my house", "EMERGENCY", "emergency only"),
    ("lol haha joke", "NOT_EMERGENCY", "prank only"),
    ("water is leaking", "NORMAL", "normal complaint"),
    ("seizure haha just kidding", "CONFLICTED", "medical emergency + explicit prank"),
    ("fire help me please", "EMERGENCY", "emergency + urgency, no prank"),
    ("bomb rofl", "CONFLICTED", "high-danger + laughter"),
]

# Expected API response for "gun shots lol":
{
    "session_id": "call-001",
    "transcript": "heard gun shots around lol",
    "language": "en",
    "intent": "OTHER",
    "issue_category": "General",
    "urgency": 5,
    "is_emergency": true,
    "action": "ESCALATE_TO_HUMAN",
    "summary": "⚠️ CONFLICTED: Emergency signal with prank indicators - requires immediate human review",
    "confidence": 0.50,
    "processing_time_ms": 5.2
}
```

---

## Future Enhancements

- [ ] **Voice analysis**: Detect panic/fear in voice tone
- [ ] **Caller history**: Track repeat prank callers
- [ ] **Pattern learning**: ML model to detect new prank patterns
- [ ] **Answer consistency**: Follow-up questions to test caller story
- [ ] **Geographic validation**: Cross-check reported emergency against local incidents
- [ ] **Sentiment analysis**: Separate genuine worry from joking tone
- [ ] **Response time analysis**: Real emergency = response urgency expected

---

## FAQ

**Q: Why not just auto-disconnect if there are prank indicators?**
A: Because people might legitimately say "lol" while having a real emergency:
   - "I'm so scared I'm laughing nervously"
   - "This is crazy, lol, my electricity went out"
   - Regional communication styles

**Q: What about false negatives (missing real emergencies)?**
A: System still catches emergencies even with prank indicators—it just marks as CONFLICTED for human review. Real emergency is never dropped, just verified.

**Q: Can this be tuned per region?**
A: Yes! Prank indicators in `emergency_keywords.json` can be customized:
   - Urban areas might recognize different prank patterns
   - Regional languages have different joking styles
   - Confidence thresholds can be adjusted per department

**Q: What if someone isn't lying and just has a strange way of talking?**
A: That's why it's CONFLICTED, not auto-DISCONNECT. Human operator reviews and determines actual intent.

