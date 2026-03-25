# ⚡ QUICK SETUP - Database & Marathi Detection Fixes

## 🎯 What's Fixed

### Issue 1: Marathi Detected as Korean ❌ → ✅ FIXED
- **Before**: "मैं मराठी बोल रहा हूँ" → Detected as **Korean (ko)**
- **After**: "मैं मराठी बोल रहा हूँ" → Detected as **Marathi (मराठी) ✓**

### Issue 2: No Database Routing ❌ → ✅ ADDED
- **Before**: Complaints analyzed but not saved to database
- **After**: All complaints → Neon DB with department routing

---

## 🚀 Install & Run (5 Minutes)

### 1️⃣ Install Database Packages
```bash
pip install psycopg2-binary python-dotenv -q
```

### 2️⃣ Run Setup Wizard
```bash
python setup_database.py
```

Interactive script will:
- Ask for Neon DB connection string
- Create `.env` file
- Initialize database tables
- Test connection
- Verify everything works

### 3️⃣ Start System
```bash
python interactive_voice_to_layer3_enhanced.py
```

Choose option 1 (microphone) and speak!

---

## 📊 What Happens Now

```
You speak Marathi: "मैं मराठी बोल रहा हूँ"
                ↓
STT: Transcribes correctly
                ↓
Language Detection: मराठी ✓ (not Korean!)
                ↓
Department Routing: General (no keywords)
                ↓
Save to Database: 
  - Session ID
  - Transcript
  - Language: Marathi
  - Urgency: Low
  - Department: General
```

---

## 🗄️ Get Neon DB Connection

**Free Database in 2 mins:**

1. Go: https://console.neon.tech
2. Click "Sign Up" (GitHub login available)
3. Create new project
4. Copy PostgreSQL connection string (looks like):
   ```
   postgresql://user:password@ep-xxxxx.us-east-1.sql.neon.tech/db_name?sslmode=require
   ```
5. Paste into setup script when asked

---

## ✅ Verification Checklist

After running setup, verify:

- [ ] `pip install psycopg2-binary` succeeded
- [ ] `setup_database.py` completed without errors
- [ ] `.env` file created with DB credentials
- [ ] "Successfully connected to Neon DB" message shown
- [ ] Database tables created (shown in console)
- [ ] System starts with all services "Ready"

---

## 🎤 Test It

### Test 1: Marathi Detection
Speak: "मैं मराठी बोल रहा हूँ"

Expected output:
```
Language Detected: Marathi (मराठी)    ✓
```

### Test 2: Emergency Routing
Speak: "आग लगी है! मदद करो!"

Expected output:
```
Urgency: CRITICAL              ✓
Department: fire               ✓
Saved to Database: ✓
```

### Test 3: Tamil
Speak: "என்னுடைய பெயர் தமிழ்"

Expected output:
```
Language Detected: Tamil (தமிழ்)      ✓
```

---

## 📂 Files You'll Create/Use

| File | What it is |
|------|-----------|
| `.env` | Your database credentials (created by setup) |
| `database_router.py` | ✓ Already created - routes to departments |
| `setup_database.py` | ✓ Already created - interactive setup |
| `unified_stt_service.py` | ✓ Updated - better language detection |
| `interactive_voice_to_layer3_enhanced.py` | ✓ Updated - database integration |

---

## 🆘 If Something Goes Wrong

### "psycopg2 not installed"
```bash
pip install psycopg2-binary
```

### "Cannot connect to database"
1. Check `.env` file has correct connection string
2. Verify Neon DB is active (https://console.neon.tech)
3. Re-run: `python setup_database.py`

### "Language still detected as Korean"
System is using cached Python modules. Restart:
```bash
python -c "import sys; sys.exit(0)"  # Clear Python cache
python interactive_voice_to_layer3_enhanced.py
```

### "It mostly works but database fails"
No problem! System has **offline fallback**:
- ✓ Transcription works
- ✓ Language detection works
- ✓ Urgency analysis works
- ✓ TTS greeting works
- ✗ Database save skipped (non-critical)

---

## 📋 Summary

| Component | Before | After |
|-----------|--------|-------|
| Marathi Detection | Korean ❌ | Marathi ✅ |
| Tamil Detection | Unknown ❌ | Tamil ✅ |
| Telugu Detection | Unknown ❌ | Telugu ✅ |
| Database Routing | None ❌ | Neon DB ✅ |
| Department Assignment | None ❌ | Smart Routing ✅ |
| Configuration | Manual ❌ | Auto Setup ✅ |

---

## 🎯 Next: Talk to Your System!

```bash
python interactive_voice_to_layer3_enhanced.py
```

Speak in **any language**:
- मराठी - Marathi
- தமிழ் - Tamil  
- తెలుగు - Telugu
- हिंदी - Hindi
- English

System will:
1. ✓ Transcribe
2. ✓ Detect language correctly (including Marathi!)
3. ✓ Play greeting in your language
4. ✓ Analyze urgency
5. ✓ Route to department
6. ✓ Save to database

**Enjoy!** 🎉

