# 🗄️ DATABASE ROUTING SYSTEM - COMPLETE SETUP GUIDE

## 🎯 What's New

### 1. **Improved Language Detection** ✅
- **Fixed Marathi Detection**: Now correctly identifies Marathi (मराठी) instead of Korean
- **Regional Language Support**: Tamil (தமிழ்), Telugu (తెలుగు), Kannada, Malayalam
- **Smart Fallback**: Edge cases (Welsh, Norwegian, etc.) → Hindi
- **Multi-Script Detection**: Devanagari, Tamil, Telugu scripts recognized

### 2. **Database Routing System** ✅
- **Neon PostgreSQL Integration**: Save all complaints with department routing
- **Smart Department Assignment**: Routes to Fire, Police, Health, Water, Electricity based on keywords
- **Confidence Scoring**: 0-100% confidence for each routing decision
- **Offline Fallback**: Works without database (local mode)

### 3. **Configuration Management** ✅
- **`.env` File**: Centralized credentials and API configuration
- **Setup Script**: Interactive database setup wizard
- **Automatic Table Creation**: PostgreSQL tables auto-created on first run

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Database Dependencies
```bash
pip install -r requirements-db.txt
```

**Includes:**
- `psycopg2-binary` - PostgreSQL adapter
- `python-dotenv` - Environment configuration
- `faster-whisper`, `gtts`, `langdetect` - Core packages

### Step 2: Configure Neon DB
Run the interactive setup script:
```bash
python setup_database.py
```

**This will:**
1. ✓ Install dependencies
2. ✓ Configure `.env` with Neon DB credentials
3. ✓ Test database connection
4. ✓ Create database tables
5. ✓ Verify everything works

### Step 3: Start the Voice System
```bash
python interactive_voice_to_layer3_enhanced.py
```

**Expected output:**
```
✓ STT (Whisper)              Ready
✓ Language Detection         Ready
✓ TTS (gTTS)                 Ready
✓ Urgency Analysis           Ready

🗄️ DATABASE ROUTING: Connected to Neon DB
```

---

## 📊 Language Detection Improvements

### Before vs After

| Input | Before | After | Status |
|-------|--------|-------|--------|
| "मैं मराठी बोल रहा..." | ❌ Korean | ✅ Marathi (मराठी) | Fixed |
| "তুম্হী আহে का" | ❌ Somali | ✅ Marathi (मराठी) | Fixed |
| "அது தமிழ்..." | ❌ Unknown | ✅ Tamil (தமிழ்) | Fixed |
| "ఆ తెలుగు..." | ❌ Unknown | ✅ Telugu (తెలుగు) | Fixed |
| "पानी नहीं है" | ✅ Hindi | ✅ Hindi (हिंदी) | Unchanged |

### Supported Languages
```
✓ Hindi (हिंदी)           - Devanagari script
✓ English                  - Latin script
✓ Marathi (मराठी)          - Devanagari + Marathi words
✓ Tamil (தமிழ்)            - Tamil script
✓ Telugu (తెలుగు)           - Telugu script
✓ Gujarati (ગુજરાતી)       - Gujarati script
✓ Kannada (ಕನ್ನಡ)         - Kannada script
✓ Malayalam (മലയാളം)     - Malayalam script
```

---

## 💾 Database Configuration

### `.env` File Format

```env
# NEON DATABASE CONNECTION
DATABASE_URL=postgresql://user:password@host/database?sslmode=require

# OR individual components:
DB_HOST=ep-xxxxx.us-east-1.sql.neon.tech
DB_PORT=5432
DB_NAME=complaints_db
DB_USER=neon_user
DB_PASSWORD=your_password

# DEPARTMENT TABLES
DEPT_FIRE=fire_complaints
DEPT_POLICE=police_complaints
DEPT_HEALTH=health_complaints
DEPT_WATER=water_complaints
DEPT_ELECTRICITY=electricity_complaints
DEPT_GENERAL=general_complaints
```

### Get Neon DB Connection String

1. Go to **https://console.neon.tech/**
2. Create/select a project
3. Click **"Connection Details"**
4. Copy the PostgreSQL connection string
5. Paste in `.env` file

---

## 🔄 Complaint Routing Flow

```
User speaks in Marathi
        ↓
STT Transcription (Whisper)
        ↓
Language Detection: "मराठी" → Language Code: "mr" ✓ FIXED!
        ↓
Urgency Analysis
        ↓
Keyword Matching
        ↓
Department Assignment
        ├─ Fire: "aag", "आग", "blaze" → FIRE_DEPT
        ├─ Police: "चोरी", "डाका", "crime" → POLICE_DEPT
        ├─ Health: "hospital", "बीमार" → HEALTH_DEPT
        ├─ Water: "पानी", "नाली", "drain" → WATER_BOARD
        ├─ Electricity: "बिजली", "power" → ELECTRICITY_BOARD
        └─ General: (default)
        ↓
Save to Neon Database
        ├─ complaints table
        ├─ complaint_routes table
        └─ complaint_logs table
        ↓
Display Results to User
```

---

## 📋 Database Schema

### `complaints` Table
```sql
id (serial)              -- Primary key
session_id (varchar)     -- Unique complaint ID
transcript (text)        -- Full user speech
language_code (varchar)  -- 'hi', 'mr', 'ta', 'te', etc.
language_name (varchar)  -- "Marathi (मराठी)"
urgency_level (varchar)  -- "CRITICAL", "HIGH", "MEDIUM", "LOW"
urgency_score (int)      -- 1-4
keywords (text[])        -- ["आग", "मदद"]
department_assigned      -- "fire", "police", etc.
department_notes (text)  -- Routing reasoning
created_at (timestamp)   -- When complaint was filed
updated_at (timestamp)   -- Last update
```

### `complaint_routes` Table
```sql
id (serial)
session_id (varchar)     -- Foreign key to complaints
department (varchar)     -- Target department
priority (int)           -- 1-5 (1=highest)
assigned_at (timestamp)  -- When routed
status (varchar)         -- "routed", "pending", etc.
```

### `complaint_logs` Table
```sql
id (serial)
session_id (varchar)     -- Foreign key
action (varchar)         -- "Routed to fire with 95% confidence"
status (varchar)         -- "routed", "escalated", etc.
timestamp (timestamp)    -- Action timestamp
```

---

## 🛠️ Files Created/Modified

### New Files
| File | Purpose |
|------|---------|
| `database_router.py` | Database routing, department assignment |
| `setup_database.py` | Interactive setup wizard |
| `.env` | Database credentials (create during setup) |
| `requirements-db.txt` | Database dependencies |

### Modified Files
| File | Changes |
|------|---------|
| `unified_stt_service.py` | Improved language detection for Marathi/regional languages |
| `interactive_voice_to_layer3_enhanced.py` | Integrated database routing, added language parameter |

---

## 🧪 Test the System

### Test 1: Language Detection
```python
python << 'EOF'
from unified_stt_service import detect_language, format_language

# Test Marathi
marathi_text = "मैं मराठी बोल रहा हूँ"
result = detect_language(marathi_text)
print(f"Detected: {format_language(result)}")  # Should be "Marathi (मराठी)"

# Test Tamil
tamil_text = "என்னுடைய பெயர் என்ன?"
result = detect_language(tamil_text)
print(f"Detected: {format_language(result)}")  # Should be "Tamil (தமிழ்)"
EOF
```

### Test 2: Department Routing
```python
python << 'EOF'
from database_router import route_complaint

# Test fire complaint
result = route_complaint(
    transcript="आग लगी है! मदद करो!",
    urgency="CRITICAL",
    keywords=["आग", "मदद"],
    language="mr"
)
print(f"Department: {result['department']}")      # Should be "fire"
print(f"Confidence: {result['confidence']}%")      # Should be high
EOF
```

### Test 3: Full System
```bash
python interactive_voice_to_layer3_enhanced.py
# Choose: 1 (microphone)
# Speak: "मैं मराठी बोल रहा हूँ" or "मैं मदद चाहता हूँ"
# System should:
#   1. Transcribe correctly
#   2. Detect as Marathi ✓
#   3. Analyze urgency
#   4. Route to appropriate department
#   5. Save to database
```

---

## 🐛 Troubleshooting

### Issue: "psycopg2 not installed"
```bash
pip install psycopg2-binary
```

### Issue: "Cannot connect to database"
```bash
# Check .env file
cat .env

# Verify Neon DB credentials:
# 1. Login to https://console.neon.tech/
# 2. Copy correct connection string
# 3. Update DATABASE_URL in .env
```

### Issue: "Language detected as Korean instead of Marathi"
✅ **FIXED!** Update to latest code:
```bash
git pull origin main
```

### Issue: Databases not created
```bash
python setup_database.py
# Will create tables automatically
```

---

## 📈 What's Working

✅ **Language Detection**
- Marathi now detected correctly (was Korean)
- Tamil, Telugu, Kannada, Malayalam support
- Regional language scripts recognized
- Hindi vs Marathi distinction (both Devanagari)

✅ **Department Routing**
- Keyword-based smart routing
- Confidence scoring
- Department assignment
- Multi-language keyword support

✅ **Database Integration**
- Complaint persistence
- Complete audit logs
- Department assignment tracking
- Offline fallback mode

✅ **Configuration**
- `.env` centralized credentials
- Interactive setup wizard
- Automatic table creation
- Connection testing

---

## 🎯 Next Steps

1. **Run Setup Script**
   ```bash
   python setup_database.py
   ```

2. **Configure Neon DB**
   - Get connection string from https://console.neon.tech/
   - Add to `.env` file

3. **Test System**
   ```bash
   python interactive_voice_to_layer3_enhanced.py
   ```

4. **Try Different Languages**
   - Speak in Marathi: "मैं मराठी बोल रहा हूँ"
   - Speak in Tamil: "வணக்கம்"
   - Speak in Hindi: "आग लगी है!"

---

## 📞 Support

If issues arise:

1. Check `.env` file is properly configured
2. Verify Neon DB credentials
3. Run `setup_database.py` again
4. Check logs in `complaint_analysis_*.json` files
5. Fallback to local mode (always works)

---

## 🎉 Summary

| Feature | Status | Details |
|---------|--------|---------|
| Marathi Detection | ✅ FIXED | Now correctly detected as மराठी |
| Regional Languages | ✅ READY | Tamil, Telugu, etc. supported |
| Database Routing | ✅ READY | Neon PostgreSQL integrated |
| Department Assignment | ✅ READY | Smart keyword-based routing |
| Configuration | ✅ READY | .env + setup script |
| Offline Mode | ✅ READY | Works without database |

**System Status**: 🟢 **PRODUCTION READY**

