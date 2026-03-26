# 🎯 Grievance Processing AI System - Complete Documentation

**Last Updated:** March 26, 2026  
**Status:** ✅ Production Ready v2.0  
**Single Source of Truth:** This document  

---

## 📑 Quick Navigation

- [Quick Start](#-quick-start) - Get running in 3 minutes
- [System Overview](#-system-overview) - What this system does
- [Architecture](#-architecture) - How it works
- [Directory Structure](#-directory-structure) - Where everything is
- [Core Components](#-core-components) - Detailed explanation of each module
- [API Endpoints](#-api-endpoints) - All 17 endpoints documented
- [Policies & Procedures](#-policies--procedures) - Rules and workflows
- [Data Models](#-data-models) - JSON structures and schemas
- [Configuration](#-configuration--setup) - How to configure
- [Running the System](#-running-the-system) - 3 ways to run
- [Examples](#-examples--workflows) - Real-world scenarios
- [Troubleshooting](#-troubleshooting) - Common issues and fixes
- [Keyword Reference](#-keyword-reference) - 250+ keywords database

---

## 🚀 Quick Start

### Get Running in 3 Minutes

```bash
# Step 1: Activate environment
cd /Users/ashwinagarkhed/integration1
source .venv/bin/activate

# Step 2: Start API server
python -m uvicorn api_endpoints.grievance_api:app --port 8000

# Step 3: Test (in new terminal)
curl http://localhost:8000/

# Step 4: Submit a grievance
curl -X POST http://localhost:8000/grievance/text \
  -H "Content-Type: application/json" \
  -d '{
    "complaint_text": "My house is on fire!",
    "user_name": "Raj Kumar",
    "user_phone": "9876543210",
    "user_location": "Mumbai"
  }'
```

### Run Examples

```bash
# Test all scenarios
python test_analytical_model.py --all

# Test text only
python test_analytical_model.py --text

# Test audio only
python test_analytical_model.py --audio
```

---

## 📋 System Overview

### What This System Does

The Grievance Processing AI is an intelligent complaint management system that:

1. **Accepts Complaints** - Text or audio in 12+ Indian languages
2. **Analyzes Urgency** - CRITICAL/HIGH/MEDIUM/LOW with confidence scores (0-4)
3. **Detects Emotions** - Anger, frustration, stress from voice patterns
4. **Routes Intelligently** - To 15+ government departments (Fire, Police, Electricity, Water, etc.)
5. **Follows Policies** - Escalation rules, SLAs, response templates
6. **Generates Output** - JSON results + user-friendly responses
7. **Integrates with Live Feeds** - 9 policy endpoints for dashboard display

### Key Features

✅ **250+ Keywords** across 4 urgency levels + 3 languages  
✅ **Emotion Detection** from voice (anger, stress, frustration)  
✅ **Evidence-Based Confidence** (no more hallucinating 50)  
✅ **Anger Detection** with pitch/intensity/speech rate analysis  
✅ **Gov Service Mapping** (15+ departments, 3 states, expanding)  
✅ **Escalation Rules** (4 automatic triggers)  
✅ **SLA Policies** (6 departments with response times)  
✅ **Response Templates** (5+ scenarios, multi-language)  
✅ **REST API** (17 endpoints, fully documented)  
✅ **JSON Output** (structured, session-based storage)  

---

## 🏗️ Architecture

### End-to-End Data Flow

```
USER INPUT (Text/Audio)
         ↓
    INPUT VALIDATION
    • Format check
    • Language detect
         ↓
LAYER 1: FEATURE EXTRACTION
    • STT/Transcription (Groq Whisper)
    • Voice Activity Detection
    • Emotion Analysis (Pitch/Intensity)
    • Confidence Calculation
         ↓
LAYER 2: NLP ANALYSIS
    • Urgency Classification (250+ keywords)
    • Intent Identification (8 patterns)
    • AI Summary Generation (Groq LLM)
         ↓
LAYER 3: DECISION MAKING
    • Department Routing
    • Escalation Triggers
    • SLA Assignment
    • Severity Flags
         ↓
LAYER 4: POLICY APPLICATION
    • Escalation Policies (4 rules)
    • SLA Policies (6 depts)
    • Response Templates
    • Department Guidelines
         ↓
OUTPUT GENERATION
    • JSON Result File (outputs/json_results/)
    • User Response Message
    • Department Routing Info
    • Follow-up Schedule
         ↓
USER OUTPUT (JSON + Response)
    • Ticket Number
    • Status
    • Next Steps
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.100+ | REST API |
| **Speech-to-Text** | Groq Whisper | Audio transcription |
| **NLP** | spaCy + patterns | Intent detection |
| **Audio Analysis** | librosa, numpy | Voice features |
| **Async** | asyncio | Background tasks |
| **Storage** | JSON + PostgreSQL | Results |

---

## 📁 Directory Structure

```
integration1/
│
├── 📂 INPUT LAYER
│   └── api_endpoints/                 # REST API - FastAPI app
│       ├── __init__.py
│       └── grievance_api.py          # 17 endpoints (text, audio, policies)
│
├── 📂 PROCESSING LAYER
│   ├── core/                          # NLP & Emotion Analysis
│   │   ├── __init__.py
│   │   ├── nlp_routing.py            # Urgency classification (250+ keywords)
│   │   ├── emotion_detection.py      # Anger/stress detection from voice
│   │   └── policies.py               # Policy definitions (SLA, escalation)
│   │
│   ├── routing/                       # ✨ NEW - Intelligent Routing Logic
│   │   ├── __init__.py
│   │   ├── route_dispatcher.py       # Multi-criteria department routing
│   │   └── escalation_engine.py      # Automatic escalation rules
│   │
│   ├── analytics/                     # Orchestration
│   │   ├── __init__.py
│   │   └── analytical_model.py       # Pipeline processor
│   │
│   ├── models/                        # Data Structures
│   │   ├── __init__.py
│   │   └── grievance_models.py       # All dataclasses
│   │
│   └── external_services/             # Gov Service Mapping
│       ├── __init__.py
│       └── gov_services_map.py       # 15+ departments, 3 states
│
├── 📂 OUTPUT LAYER
│   ├── outputs/
│   │   ├── json_results/
│   │   │   ├── by_urgency/
│   │   │   │   ├── CRITICAL/        # Emergency level grievances
│   │   │   │   ├── HIGH/            # Urgent grievances
│   │   │   │   ├── MEDIUM/          # Standard grievances
│   │   │   │   └── LOW/             # Non-urgent grievances
│   │   │   ├── by_department/
│   │   │   │   ├── fire/            # Fire department results
│   │   │   │   ├── police/          # Police results
│   │   │   │   ├── electricity/     # Electricity results
│   │   │   │   ├── water/           # Water supply results
│   │   │   │   ├── gas/             # Gas supply results
│   │   │   │   └── municipal/       # Municipal results
│   │   │   └── by_date/             # Date-organized results
│   │   └── audio_responses/         # TTS audio output
│   │
│   └── logs/                         # System logs
│
├── 📂 TESTING & EXAMPLES
│   └── test_analytical_model.py      # Example scenarios
│
├── 📂 CONFIGURATION
│   ├── requirements.txt              # Dependencies
│   ├── setup_database.py             # Optional DB initialization
│   └── .env                          # Environment variables
│
└── 📄 SYSTEM_COMPLETE_DOCUMENTATION.md  # This file - Complete reference
```

### Directory Flow Architecture

```
USER SUBMITS COMPLAINT (Text/Audio)
                ↓
        api_endpoints/          ← Receives request
        grievance_api.py
                ↓
        core/nlp_routing.py     ← Analyzes urgency (250+ keywords)
                ↓
        core/emotion_detection.py ← Detects anger/stress
                ↓
        analytics/analytical_model.py ← Orchestrates processing
                ↓
        routing/route_dispatcher.py ← Determines best department
                ↓
        routing/escalation_engine.py ← Checks auto-escalation rules
                ↓
        external_services/      ← Maps to gov department
        gov_services_map.py
                ↓
        outputs/json_results/   ← Stores by urgency/department/date
                ↓
        USER RECEIVES RESPONSE + TICKET
```

---

## 🧩 Core Components

### 1. Data Models (`models/grievance_models.py`)

**Urgency Levels:**
```python
CRITICAL (4) - Emergency: fire, police, medical
HIGH (3)     - Urgent: power outage, water break
MEDIUM (2)   - Standard: municipal issues
LOW (1)      - Non-urgent: feedback, suggestions
```

**Emotion States:**
```python
ANGRY       - High pitch (>150Hz), intensity (>-10dB), fast speech (>200 WPM)
FRUSTRATED  - Multiple pauses, slow speech (<80 WPM), variable pitch
ANXIOUS     - Trembling voice, fast speech with pauses, elevated pitch
CALM        - Normal patterns, even tone, regular speech
NEUTRAL     - No specific emotion detected
```

**Confidence Score Formula:**
```
confidence = (keyword_match×0.3 + urgency_consistency×0.25 + 
              pattern_match×0.25 + emotion_alignment×0.2) × 4

Result: 0-4 scale (replaces old hardcoded 50)
- > 3.5 = Very High (>87.5%)
- 3.0-3.5 = High (75-87.5%)
- 2.0-3.0 = Medium (50-75%)
- 1.0-2.0 = Low (25-50%)
- < 1.0 = Very Low (<25%)
```

**Main Dataclasses:**
```python
@dataclass
class GrievanceResponse:
    session_id: str
    timestamp: str
    transcript: str
    urgency_level: UrgencyLevel
    emotion_analysis: EmotionAnalysis
    intent: IntentClassification
    routing: RoutingDecision
    ai_summary: str
    confidence_score: float  # 0-4
    severity_flags: List[str]  # Escalation triggers
```

### 2. NLP Routing (`core/nlp_routing.py`)

**Urgency Classification:**
```python
def classify_urgency(text: str, voice_emotion=None):
    """
    Returns: (urgency_level, matched_keywords, confidence)
    
    Process:
    1. Keyword matching (URGENCY_KEYWORDS database)
    2. Emotion alignment (anger = higher urgency)
    3. Pattern consistency
    4. Confidence calculation
    """
```

**Keyword Database (250+ total):**

| Urgency | English | Hindi | Marathi |
|---------|---------|-------|---------|
| CRITICAL | fire, emergency, accident, attack | aag, emergency, hamlaa, chot | ag, madbhag, dourgtna |
| HIGH | power, electric, steal, water | bijli, chori, pani, gas | vidyut, chori, pani |
| MEDIUM | road, construction, noise | sadak, nirman, shor | rasta, nirman, shabd |
| LOW | complaint, feedback | shamil, jaankari | suchna, vichar |

**Intent Patterns (8 types):**
```python
report_fire, electricity_issue, water_shortage, theft_report,
harassment, property_damage, medical_emergency, other_complaint
```

### 3. Emotion Detection (`core/emotion_detection.py`)

**Voice Features Extracted:**
```python
- mean_pitch (Hz)
- max_pitch (Hz)
- min_pitch (Hz)
- pitch_variance
- mean_intensity (dB)
- speech_rate (words/min)
- pause_count
- pause_duration
- zero_crossing_rate
```

**Emotion Classification Logic:**
```
ANGRY:
  ✓ Mean pitch > 150Hz
  ✓ Intensity > -10dB
  ✓ Speech rate > 200 WPM
  ✓ Few pauses
  → anger_score 0-1

FRUSTRATED:
  ✓ Multiple pauses (>3)
  ✓ Speech rate < 80 WPM
  ✓ Variable pitch
  → frustration_score 0-1

ANXIOUS:
  ✓ High zero-crossing rate
  ✓ Fast speech with pauses
  ✓ Elevated pitch variance
  → stress_level 0-1
```

### 4. Gov Services Mapping (`external_services/gov_services_map.py`)

**15+ Services Across 3 States:**

Maharashtra:
- 🔥 MSEDCL (Electricity)
- 💧 JDVN (Water)
- 🔧 MGCL (Gas)
- 🚔 Police (100, 112)
- 🔥 Fire (101)
- 🏛️ Municipal Corp

Tamil Nadu, Delhi (similar coverage)

**Service Details:**
```python
{
    "electricity_maharashtra": {
        "service": "MSEDCL",
        "phone": "1912",
        "priority": 2,
        "sla_minutes": 120,
        "team_size": 3
    }
}
```

### 5. Analytical Model (`analytics/analytical_model.py`)

**Complete Pipeline Orchestrator:**
```python
def process_grievance(text: str, audio_path: str = None):
    """
    1. Transcription (if audio)
    2. Feature extraction
    3. Voice activity detection
    4. Emotion analysis
    5. NLP routing
    6. Intent classification
    7. Gov service mapping
    8. AI summary generation
    9. Severity flags
    
    Returns: GrievanceResponse (JSON-ready)
    """
```

### 6. REST API (`api_endpoints/grievance_api.py`)

**17 Total Endpoints:**

**Grievance Endpoints (6):**
- `POST /grievance/text` - Text complaint
- `POST /grievance/audio` - Audio upload
- `GET /grievance/{session_id}` - Retrieve result
- `GET /grievance/{session_id}/download` - Download JSON
- `GET /` - Health check
- `GET /status` - System status

**Policy Endpoints (9):**
- `GET /policies/escalation` - Escalation rules
- `GET /policies/sla` - All SLAs
- `GET /policies/sla/{department}` - Department SLA
- `GET /policies/response-templates` - Templates
- `GET /policies/response-templates/{scenario}` - Specific template
- `GET /policies/department-guidelines` - Guidelines
- `GET /policies/department-guidelines/{department}` - Department guide
- `GET /policies/grievance-handling-procedure` - Procedure
- `GET /policies/summary` - Policy summary

**Policy Module (1):**
- `core/policies.py` - All policy definitions

---

## 🔌 API Endpoints

### Submit Text Grievance

**POST** `/grievance/text`

```bash
curl -X POST http://localhost:8000/grievance/text \
  -H "Content-Type: application/json" \
  -d '{
    "complaint_text": "My electricity connection is not working for 3 days",
    "user_name": "Raj Kumar",
    "user_phone": "9876543210",
    "user_location": "Mumbai, Maharashtra",
    "language": "en"
  }'
```

**Response:**
```json
{
  "session_id": "a1b2c3d4-e5f6",
  "status": "success",
  "message": "Text grievance processed successfully",
  "data": {
    "session_id": "a1b2c3d4-e5f6",
    "timestamp": "2026-03-26T10:30:45.123456",
    "transcript": "My electricity connection is not working for 3 days",
    "urgency_level": "HIGH",
    "keywords_detected": ["electricity", "not working"],
    "emotion": {
      "state": "FRUSTRATED",
      "anger_score": 0.4,
      "frustration_score": 0.7,
      "stress_level": 0.5
    },
    "routing": {
      "department": "electricity",
      "service": "MSEDCL",
      "phone": "1912",
      "priority": 2,
      "sla_minutes": 120
    },
    "confidence_score": 3.5,
    "ai_summary": "Customer reports 3-day electricity outage. Likely power interruption. Requires immediate technician visit.",
    "severity_flags": ["EXTENDED_OUTAGE"],
    "json_file": "outputs/json_results/a1b2c3d4-e5f6_2026-03-26_103045.json"
  }
}
```

### Submit Audio Grievance

**POST** `/grievance/audio`

```bash
curl -X POST http://localhost:8000/grievance/audio \
  -F "file=@complaint.wav" \
  -F "user_name=Priya Singh" \
  -F "user_phone=8765432109" \
  -F "user_location=Delhi"
```

### Get Escalation Policies

**GET** `/policies/escalation`

```bash
curl http://localhost:8000/policies/escalation
```

**Response:**
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
    }
  ]
}
```

### Get Department SLA

**GET** `/policies/sla/electricity`

```bash
curl http://localhost:8000/policies/sla/electricity
```

**Response:**
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

### Get Response Template

**GET** `/policies/response-templates/fire_emergency?language=hi`

```bash
curl "http://localhost:8000/policies/response-templates/fire_emergency?language=hi"
```

### Get Policies Summary

**GET** `/policies/summary`

```bash
curl http://localhost:8000/policies/summary
```

---

## 📋 Policies & Procedures

### Escalation Policies (4 Rules)

| Trigger | From | To | Time | Action |
|---------|------|----|----|--------|
| anger_score > 0.8 & CRITICAL | Tier 1 | Tier 2 | 5 min | Call user, escalate |
| no_response > 30 min & HIGH | Tier 1 | Tier 2 | 30 min | Call, check status |
| anger_score > 0.6 & stress > 0.7 | Tier 1 | Tier 2 | 10 min | Call with empathy |
| multiple_calls > 2 | Tier 1 | Mgmt | 60 min | Full review |

### SLA Policies (6 Departments)

| Dept | Urgency | 1st Response | Resolution | Escalation | Team |
|------|---------|--------------|-----------|-----------|------|
| Fire | CRITICAL | 1 min | 5 min | 2 min | 5 |
| Police | CRITICAL | 1 min | 15 min | 5 min | 4 |
| Electricity | HIGH | 30 min | 120 min | 90 min | 3 |
| Water | HIGH | 60 min | 240 min | 180 min | 2 |
| Municipal | MEDIUM | 240 min | 1440 min | 720 min | 2 |
| Gas | HIGH | 15 min | 60 min | 30 min | 4 |

### Response Templates (5+ Scenarios)

**Fire Emergency (English):**
```
🚨 EMERGENCY: Fire services are being alerted immediately. 
Please evacuate to a safe location. Do not use elevators.
```

**Fire Emergency (Hindi):**
```
🚨 आपातकाल: अग्निशमन सेवाएं तुरंत सतर्क की जा रही हैं। 
कृपया सुरक्षित स्थान पर जाएं। लिफ्ट का उपयोग न करें।
```

**Power Outage:**
```
Your electricity complaint has been registered. Our technicians 
will inspect your area within 2 hours. Ticket #: {ticket_id}
```

**Water Shortage:**
```
Your water supply complaint is being forwarded to the Water Board. 
Normal supply should resume within 24 hours. Tanker assistance available.
```

### Grievance Handling Procedure (4 Phases)

**Phase 1: INTAKE (15 min)**
- Greet in user's language
- Record: name, contact, location
- Listen without interruption
- Extract details and keywords
- Assign urgency level

**Phase 2: ANALYSIS (5 min)**
- NLP classification
- Emotion detection
- Department routing
- SLA calculation
- Set escalation triggers

**Phase 3: ROUTING (10 min)**
- Identify correct department
- Generate ticket number
- Notify receiving department
- Set follow-up reminder

**Phase 4: RESPONSE (Variable)**
- Generate appropriate response
- Provide ticket info
- Set timeline expectations
- Offer assistance options
- Close or schedule follow-up

---

## 📊 Data Models

### Complete Grievance JSON

```json
{
  "session_id": "4dac4888-da83",
  "timestamp": "2026-03-25T17:58:15.288807",
  "transcript": "My house is on fire!",
  "urgency_level": "CRITICAL",
  "keywords_detected": ["fire", "house"],
  "emotion_analysis": {
    "state": "ANGRY",
    "anger_score": 0.95,
    "frustration_score": 0.3,
    "stress_level": 0.9,
    "voice_features": {
      "mean_pitch": 285,
      "max_pitch": 450,
      "intensity": 2.5,
      "speech_rate": 280,
      "pause_count": 1
    }
  },
  "intent": {
    "primary_intent": "report_fire",
    "secondary_intents": ["emergency", "immediate_help"],
    "confidence_score": 4.0,
    "reasoning": "Critical keywords, high anger, emergency patterns"
  },
  "routing": {
    "department": "fire",
    "service": "Fire Department",
    "contact_info": "101",
    "priority": 1,
    "sla_minutes": 5,
    "status": "routed"
  },
  "ai_summary": "EMERGENCY: Active fire at residential location. User in extreme distress.",
  "confidence_score": 4.0,
  "severity_flags": ["EMERGENCY_ESCALATE", "ANGRY_CUSTOMER", "HIGH_STRESS"],
  "vad_analysis": {
    "voice_activity_detected": true,
    "speech_segments": 3,
    "clarity": 0.85
  },
  "metadata": {
    "language": "en",
    "transcription_confidence": 0.98,
    "system_version": "2.0.0"
  }
}
```

---

## ⚙️ Configuration & Setup

### Environment Variables (.env)

```bash
# Groq API (for LLM summaries)
GROQ_API_KEY=your_groq_api_key_here

# Optional Database
DATABASE_URL=postgresql://user:password@localhost/grievance_db

# System
LOG_LEVEL=INFO
OUTPUT_DIR=outputs/json_results
AUDIO_OUTPUT_DIR=outputs/audio_responses
```

### Dependencies (requirements.txt)

```txt
fastapi==0.100.0
uvicorn==0.23.0
pydantic==2.0.0
numpy==1.24.0
librosa==0.10.0
soundfile==0.12.1
groq==0.4.0
python-multipart==0.0.6
```

### Install & Setup

```bash
# Navigate to project
cd /Users/ashwinagarkhed/integration1

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create output directories
mkdir -p outputs/json_results
mkdir -p outputs/audio_responses

# (Optional) Setup database
python setup_database.py
```

---

## 🎮 Running the System

### Option 1: Start API Server

```bash
source .venv/bin/activate
python -m uvicorn api_endpoints.grievance_api:app --port 8000
```

Then access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Option 2: Run Examples

```bash
# All examples
python test_analytical_model.py --all

# Text only
python test_analytical_model.py --text

# Audio only  
python test_analytical_model.py --audio
```

### Option 3: Direct Python Usage

```python
from analytics.analytical_model import AnalyticalModelProcessor

# Initialize
processor = AnalyticalModelProcessor(use_groq=True)

# Process
result = processor.process_grievance(
    text="My electricity is down",
    language="en"
)

# Save
result.save_to_json("outputs/json_results")
```

---

## 💡 Examples & Workflows

### Example 1: Fire Emergency (Hindi)

**Input:** Audio - "हमारे घर में आग है! तुरंत मदद करो!"

**Analysis:**
1. Features: Pitch 320Hz, intensity 3.2dB, speech rate 250 WPM
2. NLP: Keyword "आग" (fire) → CRITICAL
3. Emotion: anger_score=0.93
4. Routing: Fire (101)
5. Confidence: 4.0

**Output JSON:**
```json
{
  "urgency_level": "CRITICAL",
  "confidence_score": 4.0,
  "routing": {"department": "fire", "phone": "101"},
  "severity_flags": ["EMERGENCY_ESCALATE"]
}
```

**Action:**
- ✅ Fire department alert (1 min)
- ✅ Emergency response dispatch (2 min)
- ✅ Medical standby

---

### Example 2: Power Outage (English)

**Input:** Text - "My electricity is not working for 3 days in Dadar area"

**Analysis:**
1. Keywords: "electricity", "not working"
2. Urgency: HIGH
3. Emotion: FRUSTRATED
4. Routing: MSEDCL

**Output JSON:**
```json
{
  "urgency_level": "HIGH",
  "confidence_score": 3.7,
  "routing": {
    "department": "electricity",
    "service": "MSEDCL",
    "sla_minutes": 120
  }
}
```

**Action:**
- ✅ Open ticket
- ✅ Notify lineman team
- ✅ Visit within 2 hours
- ✅ Follow-up call

---

### Example 3: Water Shortage (Marathi)

**Input:** Text - "पाणी २ दिवसून मिळत नाही"

**Analysis:**
1. Keywords: "पाणी" (water)
2. Urgency: HIGH
3. Routing: Water Board

**Action:**
- ✅ Ticket created
- ✅ Board notified
- ✅ Area verification
- ✅ Tanker offered if needed

---

## 🔧 Troubleshooting

### Confidence Score Showing 50

**Problem:** Old JSON files with hardcoded 50  
**Solution:** These are legacy. New submissions use v2.0 formula (0-4 scale)

```bash
# Verify new system
curl -X POST http://localhost:8000/grievance/text \
  -H "Content-Type: application/json" \
  -d '{"complaint_text":"test"}' | grep confidence_score
# Should show 0-4, not 50
```

### Audio Not Processing

**Problem:** WAV upload fails  
**Solution:** 
```bash
# Install audio libs
pip install librosa soundfile

# Verify format
file complaint.wav
# Expected: RIFF WAV

# Test
python -c "import soundfile as sf; data, sr = sf.read('complaint.wav'); print(f'OK')"
```

### Groq API Error

**Problem:** LLM summaries failing  
**Solution:**
```bash
# Set key
export GROQ_API_KEY="gsk_..."

# System works without Groq (uses templates)
```

### Department Not Found

**Problem:** "No SLA policies found"  
**Solution:**
```bash
# Check available
curl http://localhost:8000/policies/summary

# Current: fire, police, electricity, water, gas, municipal
```

### Missing JSON Results

**Problem:** Output files not saving  
**Solution:**
```bash
# Create directories
mkdir -p outputs/json_results
mkdir -p outputs/audio_responses

# Check permissions
chmod 755 outputs

# Verify response has json_file path
```

---

## 🔍 Keyword Reference

### Hindi Keywords by Urgency

**CRITICAL:**
- aag (आग) - fire
- emergency (आपातकाल) - emergency
- accident (दुर्घटना) - accident
- hamlaa (हमला) - attack

**HIGH:**
- bijli (बिजली) - electricity
- chori (चोरी) - theft
- pani (पानी) - water
- gas (गैस) - gas

**MEDIUM:**
- sadak (सड़क) - road
- nirman (निर्माण) - construction
- shor (शोर) - noise

**LOW:**
- sujhau (सुझाव) - suggestion
- jaankari (जानकारी) - information

### English Keywords by Urgency

**CRITICAL:** fire, emergency, accident, attack, bleeding, unconscious  
**HIGH:** power, electric, steal, water, leak, injured, police  
**MEDIUM:** road, construction, noise, defect, broken  
**LOW:** complaint, feedback, suggestion, information

### Marathi Keywords by Urgency

**CRITICAL:**
- ag (अग्नि) - fire
- madbhag (मदभाग) - emergency

**HIGH:**
- vidyut (विद्युत) - electricity
- pani (पाणी) - water

---

## 📞 Support

**System Status:** ✅ Production Ready v2.0  
**Last Tested:** March 26, 2026  
**API Health:** http://localhost:8000/  
**Documentation:** This file (SYSTEM_COMPLETE_DOCUMENTATION.md)

### Quick Help

```bash
# Check logs
tail -f logs/system.log

# Run diagnostics
python service_check.py

# Test everything
python test_analytical_model.py --all
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

**End of System Documentation | Version 2.0.0 | March 26, 2026**

*This document supersedes all previous .md files and is the single source of truth.*
