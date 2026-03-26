# 🎯 GRIEVANCE PROCESSING AI - COMPLETE SYSTEM GUIDE v2.1

**Status:** ✅ Production Ready | **Version:** 2.1.0 | **Last Updated:** March 26, 2026

> **Single Source of Truth** - This document contains everything needed to understand, setup, and operate the complete grievance processing system with intelligent NLP, emotion detection, and government routing.

---

## 📑 Table of Contents

1. [Quick Start](#quick-start)-2. [Directory Structure](#directory-structure)
3. [Complete Setup Guide](#complete-setup-guide)
4. [NLP Urgency Classification](#nlp-urgency-classification)
5. [Anger & Emotion Detection](#anger--emotion-detection)
6. [Intelligent Routing](#intelligent-routing)
7. [Government Policy Endpoints](#government-policy-endpoints)
8. [API Endpoints](#api-endpoints)
9. [Policies & Procedures](#policies--procedures)
10. [Data Models](#data-models)
11. [Examples & Workflows](#examples--workflows)
12. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### 3-Minute Setup

```bash
# Activate and install
cd /Users/ashwinagarkhed/integration1
source .venv/bin/activate
pip install -r requirements.txt

# Create output directories
mkdir -p outputs/json_results/by_urgency/{CRITICAL,HIGH,MEDIUM,LOW}
mkdir -p outputs/json_results/by_department/{fire,police,electricity,water,gas,municipal}
mkdir -p outputs/json_results/by_date outputs/audio_responses logs

# Start API
python -m uvicorn api_endpoints.grievance_api:app --port 8000

# In another terminal - Test
curl http://localhost:8000/
curl -X POST http://localhost:8000/grievance/text \
  -H "Content-Type: application/json" \
  -d '{"complaint_text":"fire in house","user_name":"User","user_phone":"98765","user_location":"Mumbai"}'
```

---

## 📁 Directory Structure (Organized by Logic)

```
integration1/
│
├─ 📥 INPUT LAYER
│  └─ api_endpoints/
│     ├─ __init__.py
│     └─ grievance_api.py           # 17 endpoints (text, audio, policies)
│
├─ 🧠 PROCESSING LAYER
│  ├─ core/                          # NLP & Emotion
│  │  ├─ __init__.py
│  │  ├─ nlp_routing.py             # 250+ keywords, urgency classification
│  │  ├─ emotion_detection.py       # Anger/stress from voice (pitch, intensity)
│  │  └─ policies.py                # SLA, escalation, response templates
│  │
│  ├─ routing/                       # ✨ ROUTING LOGIC (NEW)
│  │  ├─ __init__.py
│  │  ├─ route_dispatcher.py        # Multi-criteria department routing
│  │  └─ escalation_engine.py       # Auto escalation triggers (4 rules)
│  │
│  ├─ analytics/                     # Orchestration
│  │  ├─ __init__.py
│  │  └─ analytical_model.py        # Combines all components
│  │
│  ├─ models/                        # Data structures
│  │  ├─ __init__.py
│  │  └─ grievance_models.py        # Dataclasses (UrgencyLevel, EmotionState, etc)
│  │
│  └─ external_services/             # Gov Mapping
│     ├─ __init__.py
│     └─ gov_services_map.py        # 15+ departments, 3 states
│
├─ 📤 OUTPUT LAYER
│  └─ outputs/
│     ├─ json_results/               # Results organized 3 ways:
│     │  ├─ by_urgency/
│     │  │  ├─ CRITICAL/             # Emergency responses
│     │  │  ├─ HIGH/                 # Urgent responses
│     │  │  ├─ MEDIUM/               # Standard responses
│     │  │  └─ LOW/                  # Non-urgent responses
│     │  │
│     │  ├─ by_department/           # Fire, police, water, electricity, etc
│     │  │  ├─ fire/
│     │  │  ├─ police/
│     │  │  ├─ electricity/
│     │  │  ├─ water/
│     │  │  ├─ gas/
│     │  │  └─ municipal/
│     │  │
│     │  └─ by_date/                 # Organized by date (YYYY-MM-DD)
│     │
│     ├─ audio_responses/            # TTS audio output
│     └─ logs/                       # System logs
│
├─ 🧪 TESTING
│  └─ test_analytical_model.py       # 4 example scenarios
│
├─ ⚙️  CONFIG
│  ├─ requirements.txt               # All dependencies
│  ├─ setup_database.py              # Optional DB init
│  └─ .env                           # Environment variables
│
└─ 📚 DOCUMENTATION
   └─ SYSTEM_COMPLETE_DOCUMENTATION_v2.1.md  # THIS FILE
```

### Data Flow Through Directories

```
USER INPUT
    ↓
api_endpoints/grievance_api.py  (receives request)
    ↓
core/nlp_routing.py             (analyzes text)
    ↓
core/emotion_detection.py       (analyzes voice)
    ↓
analytics/analytical_model.py   (orchestrates)
    ↓
routing/route_dispatcher.py     (finds department)
    ↓
routing/escalation_engine.py    (checks auto-escalation)
    ↓
external_services/gov_services_map.py (maps to gov)
    ↓
outputs/json_results/          (stores by urgency/dept/date)
    ↓
USER RECEIVES RESPONSE + TICKET
```

---

## 🔧 Complete Setup Guide

### Step 1: Environment Setup

```bash
# Navigate to project
cd /Users/ashwinagarkhed/integration1

# Create fresh virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Verify activation (should show .venv)
which python
```

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import numpy; import librosa; print('✅ All packages installed')"
```

### Step 3: Create Directory Structure

```bash
# Create all output directories organized by urgency
mkdir -p outputs/json_results/by_urgency/{CRITICAL,HIGH,MEDIUM,LOW}

# Create directories organized by department
mkdir -p outputs/json_results/by_department/{fire,police,electricity,water,gas,municipal}

# Create date-based directory
mkdir -p outputs/json_results/by_date

# Create audio output directory
mkdir -p outputs/audio_responses

# Create logs directory
mkdir -p logs

# Verify structure
tree outputs/json_results -L 3
```

### Step 4: Configure Environment Variables

Create `.env` file:

```bash
cat > .env << 'EOF'
# 🔑 API Configuration
GROQ_API_KEY=gsk_your_api_key_here
LOG_LEVEL=INFO

# 📂 Storage Paths
OUTPUT_DIR=outputs/json_results
AUDIO_OUTPUT_DIR=outputs/audio_responses
LOG_DIR=logs

# 🌍 Defaults
DEFAULT_LANGUAGE=en
DEFAULT_REGION=maharashtra
SUPPORTED_LANGUAGES=en,hi,mr,ta,te
EOF
```

### Step 5: Verify Setup

```bash
# Test imports
python3 << 'EOF'
print("Testing imports...")
try:
    from api_endpoints.grievance_api import app
    print("✅ FastAPI app imports OK")
    
    from core.nlp_routing import classify_urgency
    print("✅ NLP routing OK")
    
    from core.emotion_detection import analyze_emotions
    print("✅ Emotion detection OK")
    
    from routing.route_dispatcher import RouteDispatcher
    print("✅ Route dispatcher OK")
    
    from routing.escalation_engine import EscalationEngine
    print("✅ Escalation engine OK")
    
    print("\n✅ ALL SYSTEMS READY FOR PRODUCTION")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
EOF
```

---

## 🧠 NLP Urgency Classification

### How NLP Urgency Works

The NLP system classifies complaints into 4 urgency levels using **250+ keywords** across **3 languages** (English, Hindi, Marathi).

### Urgency Levels

```python
CRITICAL (4) - Emergency/life-threatening
   Examples: fire, accident, attack, emergency, bleeding, unconscious
   Action: Immediate emergency response (<5 min)
   Department: Fire, Police, Medical

HIGH (3) - Urgent but not emergency
   Examples: power outage, water leak, gas smell, theft, assault
   Action: Urgent response (30-120 min)
   Department: Electricity, Water, Police, Gas

MEDIUM (2) - Standard complaints
   Examples: potholes, noise, construction, drainage
   Action: Standard response (240 min = 4 hours)
   Department: Municipal, Public Works

LOW (1) - Non-urgent feedback
   Examples: complaint, suggestion, feedback, inquiry
   Action: Response within business day (240+ min)
   Department: Information, Feedback
```

### 250+ Keyword Database

**CRITICAL Keywords:**

| English | Hindi | Marathi | Category |
| --- | --- | --- | --- |
| fire | aag (आग) | ag (अग्नि) | Emergency |
| emergency | emergency (आपातकाल) | madbhag (मदभाग) | Emergency |
| accident | durghagna (दुर्घटना) | dourgtna (दुर्घटना) | Emergency |
| attack | hamlaa (हमला) | hamla (हमला) | Emergency |
| bleeding | khoon (खून) | raktastrav (रक्तस्राव) | Medical |

**HIGH Keywords:**

| English | Hindi | Marathi | Category |
| --- | --- | --- | --- |
| power | bijli (बिजली) | vidyut (विद्युत) | Electricity |
| electric | vidyut (विद्युत) | electrical (विद्युत) | Electricity |
| steal/theft | chori (चोरी) | chori (चोरी) | Crime |
| water | pani (पानी) | pani (पाणी) | Water |
| leak | risav (रिसाव) | risuva (रिसुवा) | Water |
| gas | gas (गैस) | gas (गॅस) | Gas |

**MEDIUM Keywords:**

| English | Hindi | Marathi | Category |
| --- | --- | --- | --- |
| road | sadak (सड़क) | rasta (रास्ता) | Municipal |
| construction | nirman (निर्माण) | nirman (निर्माण) | Municipal |
| noise | shor (शोर) | shabd (शब्द) | Complaint |
| pothole | khadd (खड्ड) | khadd (खड्ड) | Municipal |
| drain | nali (नाली) | nali (नाली) | Municipal |

### NLP Classification Process

```
INPUT TEXT (any language)
    ↓
1. LANGUAGE DETECTION
   → Identify if English, Hindi, Marathi, etc.
    ↓
2. KEYWORD MATCHING
   → Search for keywords in URGENCY_KEYWORDS database
   → Extract matched keywords
   → Calculate keyword density
    ↓
3. PATTERN MATCHING
   → Check for emergency patterns (e.g., "fire in house" = CRITICAL)
   → Check for urgent patterns
   → Check for standard patterns
    ↓
4. CONFIDENCE CALCULATION
   → keyword_match_score: 0-1 (how many keywords match)
   → pattern_match_score: 0-1 (pattern confidence)
   → Calculate combined confidence
    ↓
OUTPUT: (UrgencyLevel, [keywords], confidence_0_to_4)
```

### Example NLP Classifications

**Input:** "बिजली २ दिन से नहीं है" (Power not working for 2 days - Hindi)

```
Language: DETECTED → HINDI
Keywords matched: ["bijli", "nahi"]
Urgency Keywords: Find in dataset
Pattern match: "no power for X days" → HIGH pattern
Emotion boost: If frustrated → boost to HIGH
Final: UrgencyLevel.HIGH, confidence 3.2
```

**Input:** "My house is on fire!"

```
Language: DETECTED → ENGLISH
Keywords: ["fire", "house"]
Pattern: "X on fire" → CRITICAL pattern
Emotion: High if audio stressed
Final: UrgencyLevel.CRITICAL, confidence 4.0
```

### Code Implementation

```python
from core.nlp_routing import classify_urgency

# Example 1: English text
urgency, keywords, confidence = classify_urgency(
    "My electricity is not working for 3 days",
    language="en"
)
# Returns: (UrgencyLevel.HIGH, ["electricity", "not_working"], 3.5)

# Example 2: Hindi text
urgency, keywords, confidence = classify_urgency(
    "आग लग गई!",  # "Fire!"
    language="hi"
)
# Returns: (UrgencyLevel.CRITICAL, ["aag"], 4.0)

# Example 3: With emotion context
urgency, keywords, confidence = classify_urgency(
    "power is out",
    voice_emotion_score=0.8  # User is angry
)
# confidence boosted due to emotion
```

---

## 😠 Anger & Emotion Detection

### How Anger Detection Works

The system analyzes voice recordings to detect emotional states, particularly **anger**, **frustration**, and **stress** using **acoustic features**.

### Voice Features Analyzed

```python
Feature                  What It Means              Anger Indicator?
─────────────────────────────────────────────────────────────────
mean_pitch              Average frequency          HIGH pitch = anger
max_pitch               Highest frequency          Peak pitch > 150Hz = anger
pitch_variance          Pitch fluctuations         High variance = emotion
mean_intensity          Average loudness (dB)      >-10dB = anger
speech_rate             Words per minute           >200 WPM = anger/stress
pause_count             Number of pauses           Few pauses = anger
pause_duration          Length of silent breaks    Hesitation = frustration
zero_crossing_rate      Voice trembling            High ZCR = anxiety
```

### Anger Detection Logic

```
VOICE INPUT (.wav file)
    ↓
1. AUDIO PROCESSING
   → Read WAV file
   → Normalize audio signal
   → Remove silence
    ↓
2. FEATURE EXTRACTION
   → Calculate mean pitch (Hz)
   → Calculate intensity (dB)
   → Calculate speech rate (words/min)
   → Count pauses
   → Calculate zero-crossing rate
    ↓
3. EMOTION CLASSIFICATION
   
   IF mean_pitch > 150Hz AND intensity > -10dB AND speech_rate > 200 WPM:
       EMOTION = ANGRY
       anger_score = 0.9-1.0
   
   ELSE IF pause_count > 3 AND speech_rate < 80 WPM:
       EMOTION = FRUSTRATED
       frustration_score = 0.7-0.9
   
   ELSE IF zero_crossing_rate > threshold AND pitch_variance high:
       EMOTION = ANXIOUS
       stress_level = 0.6-0.8
   
   ELSE:
       EMOTION = CALM/NEUTRAL
       scores = 0.0-0.3
    ↓
OUTPUT: EmotionAnalysis
   {
     "state": "ANGRY",
     "anger_score": 0.95,      # 0-1
     "frustration_score": 0.2,
     "stress_level": 0.8,
     "voice_features": { ... }
   }
```

### Emotion Classification Thresholds

```python
ANGRY Detection:
   ✓ Mean pitch > 150 Hz (normal ~100-120 Hz)
   ✓ Intensity > -10 dB (normal ~-20 to -15 dB)
   ✓ Speech rate > 200 WPM (normal ~100-150 WPM)
   ✓ Pause count < 2 (continuous speech)
   → RESULT: anger_score = 0.8-1.0

FRUSTRATED Detection:
   ✓ Pause count > 3 (hesitation)
   ✓ Speech rate < 80 WPM (slow, struggling)
   ✓ Pitch variance > normal (wavering voice)
   → RESULT: frustration_score = 0.6-0.9

ANXIOUS Detection:
   ✓ Zero-crossing rate high (trembling)
   ✓ Speech rate variable (inconsistent)
   ✓ Pitch elevated and wavering
   → RESULT: stress_level = 0.6-0.8

CALM/NEUTRAL:
   ✓ Normal pitch (100-120 Hz)
   ✓ Normal intensity (-20 to -15 dB)
   ✓ Normal speech rate (100-150 WPM)
   ✓ Regular pauses
   → RESULT: all scores = 0.0-0.3
```

### Example Anger Detection

**Input:** Audio of angry complaint about fire

```
Audio Analysis:
  mean_pitch: 285 Hz        ← HIGH (anger indicator)
  intensity: 2.5 dB         ← HIGH (anger indicator)
  speech_rate: 280 WPM      ← HIGH (anger indicator)
  pause_count: 1            ← LOW (anger indicator)
  zero_crossing_rate: 0.45  ← MODERATE

Emotion Classification:
  Multiple anger indicators detected
  anger_score = 0.95
  
  state = ANGRY
  frustration_score = 0.1
  stress_level = 0.8

OUTPUT:
  EmotionAnalysis(
    state='ANGRY',
    anger_score=0.95,
    frustration_score=0.1,
    stress_level=0.8
  )
```

### Code Implementation

```python
from core.emotion_detection import analyze_emotions
import soundfile as sf

# Load audio
audio_data, sample_rate = sf.read("complaint.wav")

# Analyze emotions
emotion_analysis = analyze_emotions(audio_data, sample_rate)

print(f"Emotion: {emotion_analysis.state}")
print(f"Anger: {emotion_analysis.anger_score:.2f}")
print(f"Frustration: {emotion_analysis.frustration_score:.2f}")
print(f"Stress: {emotion_analysis.stress_level:.2f}")

# Output:
# Emotion: ANGRY
# Anger: 0.95
# Frustration: 0.10
# Stress: 0.80
```

---

## 🚦 Intelligent Routing

### How Routing Works (Multi-Criteria Decision)

The routing system determines the **optimal government department** to handle each complaint using intelligent scoring.

### Routing Process

```
ANALYZED GRIEVANCE
    ↓
1. SCORE EACH DEPARTMENT
   For EACH department in [fire, police, electricity, water, etc]:
   
   a) KEYWORD SCORE (0-1)
      → How many keywords match this department?
      → fire report → fire dept = 1.0
      → power outage → electricity dept = 0.9
   
   b) URGENCY ALIGNMENT SCORE (0-1)
      → Is department's capability suitable for urgency?
      → CRITICAL + fire dept = 1.0 (perfect)
      → HIGH + electricity dept = 0.8
      → LOW + fire dept = 0.5 (overkill)
   
   c) EMOTION SEVERITY SCORE (0-1)
      → How severe is emotional state?
      → anger_score 0.95 → score 0.95
      → All calm → score 0.1
   
   d) FINAL SCORE (0-10)
      = (keyword × 0.4 + urgency × 0.35 + emotion × 0.25) × 10
   
   ✓ Boost if detected service matches
    ↓
2. SELECT TOP DEPARTMENT
   → Pick department with highest score
    ↓
3. DETERMINE PRIORITY (1-5)
   → 1 = Highest (emergency)
   → 5 = Lowest (routine)
   
   Priority Logic:
   - CRITICAL → P1 or P2
   - HIGH → P2 or P3
   - If anger > 0.7 → bump up priority
   - If stress > 0.7 → bump up priority
    ↓
4. GET SLA (Response Times)
   → Look up SLA for: department + urgency
   → First response time (e.g., 30 min for electricity)
   → Resolution time (e.g., 120 min)
   → Escalation point (e.g., 90 min)
    ↓
5. RETURN ROUTING DECISION
   {
     department: "electricity",
     priority: 2,
     service: "MSEDCL",
     phone: "1912",
     first_response_minutes: 30,
     resolution_minutes: 120,
     confidence: 0.85
   }
```

### Scoring Examples

**Example 1: Power Outage**

```
Input Text: "My electricity is not working for 3 days"
Urgency: HIGH
Emotion: frustrated (not angry)

Department Scores:
├─ electricity
│  ├─ keyword_score: 0.95 (strong match)
│  ├─ urgency_score: 0.8 (HIGH = electricity suitable)
│  ├─ emotion_score: 0.6 (frustration present)
│  └─ final_score: 8.5/10 ✓ SELECTED
│
├─ fire: 2.1/10 (no match)
├─ police: 1.8/10 (no match)
└─ water: 2.5/10 (no match)

ROUTING DECISION:
  department: "electricity"
  priority: P2 (HIGH urgency)
  service: "MSEDCL"
  phone: "1912"
  confidence: 0.85
```

**Example 2: Fire Emergency**

```
Input: "हमारे घर में आग है!" (Our house is on fire!)
Urgency: CRITICAL
Emotion: ANGRY (anger_score: 0.95)

Department Scores:
├─ fire
│  ├─ keyword_score: 1.0 (perfect match "aag")
│  ├─ urgency_score: 1.0 (CRITICAL = fire emergency)
│  ├─ emotion_score: 0.95 (very angry)
│  ├─ final_score: 9.95/10 × 1.5 boost = MAX ✓ SELECTED
│
├─ police: 7.8/10 (also can help)
├─ medical: 6.5/10
└─ water: 1.2/10

ROUTING DECISION:
  department: "fire"
  priority: P1 (CRITICAL urgency + anger)
  service: "Fire Department"
  phone: "101"
  confidence: 0.99
  escalation: IMMEDIATE
```

### Code Implementation

```python
from routing.route_dispatcher import RouteDispatcher
from models.grievance_models import AnalyticalModel

# Initialize dispatcher
dispatcher = RouteDispatcher()

# Get routing decision for grievance
routing_decision = dispatcher.dispatch_route(analytical_model)

print(f"Routing to: {routing_decision.department}")
print(f"Priority: P{routing_decision.priority}")
print(f"Service: {routing_decision.mapped_service.service_name}")
print(f"Phone: {routing_decision.mapped_service.contact_info}")
print(f"Confidence: {routing_decision.confidence:.2f}")
```

---

## 🏛️ Government Policy Endpoints

### All Policy Endpoints (9 Total)

The API provides **9 dedicated policy endpoints** for live feed integration:

| Endpoint | Method | Purpose | Response |
| --- | --- | --- | --- |
| `/policies/escalation` | GET | All escalation rules | JSON array of 4 rules |
| `/policies/sla` | GET | All SLA policies | JSON array of 6 departments |
| `/policies/sla/{dept}` | GET | Department SLA only | JSON for specific dept |
| `/policies/response-templates` | GET | All response templates | JSON array of 5+ templates |
| `/policies/response-templates/{scenario}` | GET | Specific template | Single template JSON |
| `/policies/department-guidelines` | GET | All department guides | JSON array |
| `/policies/department-guidelines/{dept}` | GET | Department guide only | Single department JSON |
| `/policies/grievance-handling-procedure` | GET | Full 4-phase procedure | Complete JSON |
| `/policies/summary` | GET | Quick overview | Summary with endpoints list |

### Policy Endpoint Examples

**1. Get All Escalation Rules**

```bash
curl http://localhost:8000/policies/escalation
```

Response:
```json
{
  "status": "success",
  "policy_type": "escalation",
  "total_policies": 4,
  "policies": [
    {
      "trigger": "anger_score > 0.8 and urgency == CRITICAL",
      "from_level": "tier_1_operator",
      "to_level": "tier_2_supervisor",
      "timeframe_minutes": 5,
      "responsible_team": "Grievance Supervisor",
      "action_required": "Immediate call to user, escalate to senior management"
    },
    {
      "trigger": "no_response_since_30_minutes and urgency == HIGH",
      "from_level": "tier_1_operator",
      "to_level": "tier_2_supervisor",
      "timeframe_minutes": 30,
      "responsible_team": "Supervisor",
      "action_required": "Call user, check with assigned department, update ticket"
    }
  ]
}
```

**2. Get Department-Specific SLA**

```bash
curl http://localhost:8000/policies/sla/electricity
```

Response:
```json
{
  "status": "success",
  "department": "electricity",
  "policies": [
    {
      "department": "electricity",
      "urgency_level": "HIGH",
      "first_response_minutes": 30,
      "resolution_minutes": 120,
      "escalation_point_minutes": 90,
      "team_size": 3
    }
  ]
}
```

**3. Get Response Template**

```bash
curl "http://localhost:8000/policies/response-templates/fire_emergency?language=hi"
```

Response:
```json
{
  "status": "success",
  "template": {
    "response_text": "🚨 आपातकाल: अग्निशमन सेवाएं तुरंत सतर्क की जा रही हैं। कृपया सुरक्षित स्थान पर जाएं।",
    "required_info": ["exact_location", "people_count", "injuries"],
    "next_action": "Connect to fire_department_101"
  }
}
```

**4. Get Department Guidelines**

```bash
curl http://localhost:8000/policies/department-guidelines/electricity
```

Response:
```json
{
  "status": "success",
  "department": "electricity",
  "guideline": {
    "complaint_types": ["no_power", "high_bill", "meter_issue"],
    "required_documents": ["meter_photo", "bill_copy", "id_proof"],
    "processing_steps": [
      "1. Verify meter number and connection",
      "2. Check outage status in system",
      "3. Dispatch lineman if needed",
      "4. Provide ETA to customer",
      "5. Follow up after 24 hours"
    ],
    "contact_escalation_point": "MSEDCL Circle Office - 1912"
  }
}
```

**5. Get Policies Summary**

```bash
curl http://localhost:8000/policies/summary
```

Response:
```json
{
  "status": "success",
  "summary": {
    "escalation_policies": 4,
    "sla_policies": 6,
    "response_templates": 5,
    "department_guidelines": 4,
    "available_departments": ["electricity", "water", "fire", "police"],
    "available_scenarios": ["fire_emergency", "power_outage", "water_shortage"]
  },
  "endpoints": [
    "/policies/escalation",
    "/policies/sla",
    "/policies/sla/{department}",
    "/policies/response-templates",
    "/policies/response-templates/{scenario}",
    "/policies/department-guidelines",
    "/policies/department-guidelines/{department}",
    "/policies/grievance-handling-procedure",
    "/policies/summary"
  ]
}
```

---

## 🔌 All API Endpoints (17 Total)

### Grievance Processing (6 endpoints)

```
POST   /grievance/text              # Submit text complaint
POST   /grievance/audio             # Submit audio complaint
GET    /grievance/{session_id}      # Retrieve result
GET    /grievance/{session_id}/download # Download JSON
GET    /                            # Health check
GET    /status                      # System status
```

### Policy Display (9 endpoints)

```
GET    /policies/escalation
GET    /policies/sla
GET    /policies/sla/{department}
GET    /policies/response-templates
GET    /policies/response-templates/{scenario}
GET    /policies/department-guidelines
GET    /policies/department-guidelines/{department}
GET    /policies/grievance-handling-procedure
GET    /policies/summary
```

### Module Organization (2 folders)

```
routing/                            # Routing & Escalation
- route_dispatcher.py
- escalation_engine.py
```

---

## 📋 Policies & Procedures

### 4 Automatic Escalation Rules

| # | Rule | Trigger | From | To | Time | Action |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ANGER_CRITICAL | anger > 0.8 + CRITICAL | Tier 1 | Tier 2 | 5 min | Call + escalate |
| 2 | TIMEOUT | no response > 30 min + HIGH | Tier 1 | Tier 2 | 30 min | Check status |
| 3 | STRESS | anger > 0.6 + stress > 0.7 | Tier 1 | Tier 2 | 10 min | Empathy call |
| 4 | REPEATED | multiple calls > 2 | Tier 1 | Mgmt | 60 min | Full review |

### 6 SLA Policies

| Department | Urgency | 1st Response | Resolution | Escalation | Team |
| --- | --- | --- | --- | --- | --- |
| Fire | CRITICAL | 1 min | 5 min | 2 min | 5 |
| Police | CRITICAL | 1 min | 15 min | 5 min | 4 |
| Electricity | HIGH | 30 min | 120 min | 90 min | 3 |
| Water | HIGH | 60 min | 240 min | 180 min | 2 |
| Municipal | MEDIUM | 240 min | 1440 min | 720 min | 2 |
| Gas | HIGH | 15 min | 60 min | 30 min | 4 |

### 4-Phase Grievance Handling

```
PHASE 1: INTAKE (15 min)
- Greet in user's language
- Record: name, phone, location
- Listen without interruption
- Extract keywords and details
- Assign urgency level

PHASE 2: ANALYSIS (5 min)
- NLP classification
- Emotion detection
- Department routing decision
- SLA calculation
- Set escalation triggers

PHASE 3: ROUTING (10 min)
- Identify correct department
- Generate ticket number
- Notify receiving department
- Set follow-up reminder

PHASE 4: RESPONSE (Variable by SLA)
- Generate appropriate response
- Provide ticket information
- Set time expectations
- Offer assistance options
- Schedule follow-up or close
```

---

## 📊 Data Models

### Urgency Levels (0-4)

```
CRITICAL (4) - Emergency
  Examples: fire, accident, assault, medical emergency
  Response: < 5 minutes

HIGH (3) - Urgent
  Examples: power outage, water leak, theft
  Response: 30-120 minutes

MEDIUM (2) - Standard
  Examples: potholes, noise, municipal issues
  Response: 240+ minutes

LOW (1) - Routine
  Examples: feedback, suggestion, inquiry
  Response: 24+ hours
```

### Emotion States

```
ANGRY
  Indicators: high pitch (>150Hz), high intensity (>-10dB), fast speech (>200 WPM)
  anger_score: 0.8-1.0

FRUSTRATED
  Indicators: multiple pauses, slow speech (<80 WPM), variable pitch
  frustration_score: 0.6-0.9

ANXIOUS
  Indicators: trembling voice, fast speech with pauses, elevated pitch
  stress_level: 0.6-0.8

CALM/NEUTRAL
  Indicators: normal acoustic properties
  all_scores: 0.0-0.3
```

### Confidence Score (0-4 scale)

```
4.0 ← Very High (>90%)
3.5 ← High (75-90%)
3.0 ← Medium (60-75%)
2.0 ← Low (40-60%)
1.0 ← Very Low (20-40%)
0.5 ← Lowest (<20%)

Formula:
confidence = (keyword_match×0.3 + urgency_consistency×0.25 + 
              pattern_match×0.25 + emotion_alignment×0.2) × 4
```

---

## 💡 Examples & Workflows

### Scenario 1: Fire Emergency (Audio, Hindi)

**Input:** Audio recording - "हमारे घर में आग है! तुरंत मदद करो!" (Our house is on fire!)

**Processing:**

```
STEP 1: NLP Analysis
  Language: Hindi detected
  Keywords: ["aag" (fire), "turant" (immediate)]
  Pattern: "house on fire" → CRITICAL
  Urgency: CRITICAL (4)

STEP 2: Emotion Analysis
  Audio Features:
    - mean_pitch: 285 Hz (HIGH - normal 100-120)
    - intensity: 2.5 dB (HIGH - normal -20 to -15)
    - speech_rate: 280 WPM (HIGH - normal 100-150)
    - pause_count: 1 (LOW)
  Emotion State: ANGRY
  anger_score: 0.95, stress_level: 0.9

STEP 3: Intelligent Routing
  Department Scores:
    - fire: 9.9/10 (perfect match) ✓ SELECTED
    - police: 7.8/10 (also capable)
  Priority: P1 (CRITICAL + ANGRY)
  Service: Fire Department (101)

STEP 4: Escalation Check
  Trigger: anger_score > 0.8 AND urgency == CRITICAL
  Action: IMMEDIATE escalation to Tier 2
  Time: 5 minutes max

STEP 5: Response
  Template (Hindi): "🚨 आपातकाल: अग्निशमन सेवाएं तुरंत सतर्क की जा रही हैं..."
  SLA: 1 minute first response, 5 minute resolution
  Ticket: FIRE-2026-03-26-001
  Status: ESCALATED TO MANAGEMENT
```

**Output JSON:**

```json
{
  "session_id": "fire-001",
  "urgency_level": "CRITICAL",
  "confidence_score": 4.0,
  "emotion": {"state": "ANGRY", "anger_score": 0.95},
  "routing": {
    "department": "fire",
    "phone": "101",
    "priority": 1,
    "sla_minutes": 5
  },
  "ai_summary": "EMERGENCY: Active fire at residential location. User in extreme distress.",
  "severity_flags": ["EMERGENCY_ESCALATE", "ANGRY_CUSTOMER"],
  "escalation_triggers": ["ANGER_CRITICAL_ESCALATION"]
}
```

**Storage:**

```
outputs/json_results/by_urgency/CRITICAL/fire-001_2026-03-26_timestamp.json
outputs/json_results/by_department/fire/fire-001_2026-03-26_timestamp.json  
outputs/json_results/by_date/2026-03-26/fire-001_timestamp.json
```

### Scenario 2: Power Outage (Text, English)

**Input:** "My electricity is not working for 3 days in Dadar area"

**Processing:** → Routes to MSEDCL (Electricity) with P2 priority, HIGH urgency → Output JSON saved to 3 locations → SLA: 30 min first response, 120 min resolution

---

## 🔧 Troubleshooting

### Issue: Anger Not Detected

**Problem:** Audio processing returns low anger score even for angry voice  
**Solution:**  
```bash
# Check audio file
ffprobe -show_format complaint.wav

# Verify audio quality
python -c "import soundfile as sf; print('Sample rate:', sf.info('complaint.wav').samplerate)"

# Test emotion detection
python -c "from core.emotion_detection import analyze_emotions; import soundfile as sf; 
d,sr=sf.read('complaint.wav'); a=analyze_emotions(d,sr); print(f'Anger: {a.anger_score}')"
```

### Issue: Wrong Department Routing

**Problem:** Grievance routed to wrong department  
**Solution:**  
```bash
# Debug routing scores
python << 'EOF'
from routing.route_dispatcher import RouteDispatcher
from models.grievance_models import AnalyticalModel

dispatcher = RouteDispatcher()
text = "My water is not coming"

# Get scores for all departments
scores = dispatcher._calculate_routing_scores(analytical_model)
for s in scores:
    print(f"{s.department}: {s.final_score:.2f} - {s.reasoning}")
EOF
```

### Issue: API Not Starting

**Problem:** `python -m uvicorn api_endpoints.grievance_api:app` fails  
**Solution:**  
```bash
# Check imports
python -c "from api_endpoints.grievance_api import app; print('✅ OK')"

# Check port availability  
lsof -i :8000

# Try different port
python -m uvicorn api_endpoints.grievance_api:app --port 8001
```

---

## 📞 Support & Contact

- **System Status:** ✅ Production Ready v2.1
- **Last Updated:** March 26, 2026
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/

---

**End of Documentation v2.1 | Complete System Reference**

*This master document contains all information needed to understand, setup, and operate the complete grievance processing system.*
