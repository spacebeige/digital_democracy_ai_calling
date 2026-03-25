# 🚀 QUICK START - 3 MINUTES TO WORKING SYSTEM

## 🌐 NEW: Automatic Language Detection

**The system now automatically detects whether you're speaking:**
- 🇮🇳 **Hindi (हिंदी)** 
- 🇬🇧 **English**
- 🔀 **Hinglish** (Mixed Hindi-English)

No setup needed - just speak naturally in any language!

---

## Choose Your Path

### 🟢 **Option A: Test Right Now (No Microphone)**
```bash
python urgency_tester.py
```
**Time:** 2 minutes
**What happens:** Type complaints, see instant urgency classification

**Try these:**
```
आग लगी है!
बिजली नहीं है
सड़क खराब है
जानकारी चाहिए
exit
```

---

### 🟡 **Option B: See Real Examples (Demo)**
```bash
python urgency_demo.py
```
**Time:** 1 minute
**What happens:** Analyzes 10 real complaints, shows accuracy stats

---

### 🔴 **Option C: Go Full Voice (Live Microphone)**
```bash
python interactive_voice_to_layer3_enhanced.py
```
**Time:** 3 minutes
**What happens:**
1. Choose `1` (microphone)
2. Speak your complaint (see live meter!)
3. System analyzes and routes
4. See results on screen

---

## What You'll See (Live Example)

### When Recording:
```
🔴 RECORDING...
Speak your complaint now!

  04s ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

### After Speaking:
```
YOU SAID:
"बिजली 5 दिन से नहीं है"

⚠️ LEVEL: HIGH
Confidence: 3/4
Keywords: बिजली, नहीं
```

### Final Result:
```
Department: ELECTRICITY_BOARD
Priority: 4/5
✓ Complete!
```

---

## 📊 Urgency Levels (Cheat Sheet)

| Emoji | Level | Response | Examples |
|-------|-------|----------|----------|
| 🚨 | CRITICAL | < 1 min | आग, accident, emergency |
| ⚠️ | HIGH | same-day | बिजली, robbery, hospital |
| ⏱️ | MEDIUM | 3-5 days | सड़क, गड्ढा, water |
| ℹ️ | LOW | on-demand | जानकारी, सवाल, suggestion |

---

## 📁 All Tools at a Glance

```
urgency_tester.py
├─ Use for: Quick text testing
├─ Time: 2 minutes
└─ No setup needed

urgency_demo.py
├─ Use for: See 10 real examples
├─ Time: 1 minute
└─ Shows accuracy metrics

interactive_voice_to_layer3_enhanced.py
├─ Use for: Full system with voice
├─ Time: 3+ minutes
└─ Real-time visualization
```

---

## ⚡ Features You're Getting

```
✓ Real-time audio meter
✓ Live countdown timer
✓ Transcription display
✓ Language detection (Hindi/English/Hinglish)
✓ Urgency level (🚨 to ℹ️)
✓ Keyword extraction
✓ Confidence scoring
✓ Auto-routing based on urgency
✓ Department assignment
✓ JSON reports
✓ Multi-language (Hindi/English)
```

---

## 🌐 Language Detection

The system automatically detects which language you're speaking:

### Supported Languages
- **हिंदी (Hindi)** - Full support with 70+ keywords
- **English** - Full support 
- **Hinglish** - Mixed Hindi-English detected automatically

### How It Works
```
You say: "Mere ghar ke pani ki supply nahi aa rahi"
System detects: Hindi
Urgency detected: MEDIUM
Keywords: ["पानी", "supply"]
```

```
You say: "There's a fire in the building"
System detects: English
Urgency detected: CRITICAL
Keywords: ["fire"]
```

```
You say: "Electricity ka bill bohot zyada aa gya"
System detects: Hinglish (Mixed)
Urgency detected: LOW
Keywords: ["electricity"]
```

---

## 🎯 What Each Script Does

### **urgency_tester.py** - Interactive Test
```
>> Type your complaint
>> See instant urgency level
>> Repeats until you exit

Perfect for: Testing different scenarios
No setup: Just run it!
```

### **urgency_demo.py** - Automated Demo
```
Complaint #1: "आग लगी है!"
Result: 🚨 CRITICAL (4/4) ✓

Complaint #2: "बिजली नहीं है"
Result: ⚠️ HIGH (3/4) ✓

[10 total examples...]
Final: 90% accuracy
```

### **interactive_voice_to_layer3_enhanced.py** - Live System
```
Choose input method:
1. Microphone (with visualization)
2. Audio file
3. Exit

Then: Real-time processing with all features
```

---

## 🎤 Microphone Test (Detailed)

```bash
python interactive_voice_to_layer3_enhanced.py

# System checks services
Checking services...
  ✓ STT Service          OK
  ✓ Backend API          OK

# Shows menu
INPUT METHOD
  1. Speak into microphone ← Select this
  2. Use audio file
  3. Exit

Select (1-3): 1

# Recording starts with visualization
🎤 Initializing microphone...
🔴 RECORDING...
Speak your complaint now!

  01s ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  02s ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  03s ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  [Stop by pressing Ctrl+C or let it reach 10s]

# After speaking
✓ Recording complete!
Duration: 4.2s | Max level: 0.45

YOU SAID:
"बिजली 5 दिन से नहीं है"

⚠️ LEVEL: HIGH
Confidence: 3/4

KEY TERMS DETECTED:
• बिजली गई

✓ Routed successfully

✓ Complaint recorded and routed
Results saved to: complaint_analysis_abc123.json
```

---

## 🔧 Troubleshooting (30 seconds)

**If microphone not available:**
```bash
pip install sounddevice soundfile
python interactive_voice_to_layer3_enhanced.py
# Try again
```

**If services fail:**
```bash
# Check services running:
curl http://localhost:9000  # STT
curl http://localhost:8000  # Backend

# If not, start them:
python start_all.py
```

---

## 📱 Complete Flow Diagram

```
START HERE
    ↓
[Want to test NOW?]
    ↓
YES → python urgency_tester.py (2 min)
      Type complaints, see results instantly
    
NO → [Want to see examples?]
     ↓
     YES → python urgency_demo.py (1 min)
           See 10 real complaints analyzed
     
     NO → [Ready for full system?]
          ↓
          YES → python interactive_voice_to_layer3_enhanced.py
                Choose 1 (microphone) or 2 (file)
                See real-time visualization
```

---

## ✨ Key Innovations

1. **Real-Time Meter**: See your voice level as you speak
2. **Live Timer**: Know how long you're speaking
3. **Text Confirmation**: "YOU SAID: ..." proves understanding
4. **Smart Urgency**: 🚨 CRITICAL to ℹ️ LOW automatic
5. **Keywords Shown**: See what triggered the urgency
6. **Instant Routing**: No manual triage needed
7. **Multi-Language**: Hindi, English, Hinglish

---

## 🎓 Learning as You Go

### First Run
```
python urgency_tester.py
>> आग लगी है!
🚨 CRITICAL (4/4)  ← Understand CRITICAL level
```

### Second Run
```
>> बिजली नहीं है
⚠️ HIGH (3/4)  ← Understand HIGH level
```

### Third Run
```
>> What's the bus time?
ℹ️ LOW (1/4)  ← See how LOW is handled
```

---

## 📊 Success Metrics You'll See

### For Text Tester:
```
Complaints processed: 10
🚨 CRITICAL: 2  (20%)
⚠️ HIGH: 3      (30%)
⏱️ MEDIUM: 3    (30%)
ℹ️ LOW: 2       (20%)
```

### For Voice System:
```
Recording: 4.2s completed ✓
Transcription: "YOUR_TEXT" ✓
Urgency: HIGH (3/4) ✓
Routing: DEPT_ID ✓
Saved: JSON report ✓
```

---

## 🎯 Next Steps After Testing

1. **Test all 3 scripts** (5 minutes)
2. **Check JSON reports** from voice input
3. **Add your keywords** to URGENCY_KEYWORDS dict
4. **Deploy to production** with real phone system

---

## 📞 Real-World Use Case

```
Citizen calls → Speaks complaint
                ↓ (Real-time meter shown)
           YOU SAID: "..."
                ↓ (Confirms understanding)
           ⚠️ URGENCY: HIGH
           Keywords: बिजली
                ↓ (Smart analysis)
           Department: ELECTRICITY_BOARD
           Priority: 4/5
                ↓ (Instant routing)
           ✓ Complaint recorded
           Expected response: Same-day
                ↓
           Engineer dispatched by next morning
```

---

## 🚀 You're Ready!

Pick any script and run:

```bash
# Easiest (no setup)
python urgency_tester.py

# Or see examples
python urgency_demo.py

# Or go full voice
python interactive_voice_to_layer3_enhanced.py
```

**Let's go!** 🎉

---

## 📚 More Info

- Detailed guide: `ENHANCED_VOICE_GUIDE.md`
- System overview: `SYSTEM_OVERVIEW.md`
- Before/after: `BEFORE_AFTER_COMPARISON.md`
- Enhancement summary: `ENHANCEMENTS_SUMMARY.md`

---

Made for India's Digital Democracy Initiative 🇮🇳
