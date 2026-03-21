# Quick Reference Card

## 🚀 Quick Start (30 seconds)

```bash
# 1. Open Command Prompt
# 2. Navigate to project folder
cd C:\Users\91961\Desktop\digital_democracy_ai_calling

# 3. Run setup
psql -U postgres -f database_setup.sql
pip install -r requirements_hackathon.txt

# 4. Start backend
python main.py

# 5. Open in browser
http://localhost:8000/docs  (API docs)
```

## 📱 URLs

| Page | URL |
|------|-----|
| API Docs | http://localhost:8000/docs |
| User Page | file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/user.html |
| Officer Dashboard | file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/officer.html |
| Compliance Dashboard | file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/compliance.html |

## 🎯 Test Data

Try submitting these complaints to see different priorities:

| Input | Priority | SLA |
|-------|----------|-----|
| "Fire in the building" | HIGH | 1 hour |
| "Water leaking from pipe" | MEDIUM | 6 hours |
| "Garbage on street" | LOW | 24 hours |
| "Flood at downtown" | HIGH | 1 hour |

## 🔑 Priority Detection Keywords

**HIGH Priority:**
- flood, fire, accident, urgent

**MEDIUM Priority:**
- water, electricity

**LOW Priority:**
- Everything else

## 🏷️ Issue Types

| Input Contains | Issue Type |
|---|---|
| garbage | waste |
| flood, water | flood |
| smoke | pollution |
| (anything else) | other |

## 📊 Dashboard Quick Guide

### User Page
1. Type complaint
2. Click Submit
3. Get ticket ID & details

### Officer Dashboard
1. View all tickets in table
2. Filter by location (text box)
3. Filter by priority (dropdown)
4. Click "Change Status" to update
5. Click "Generate Insights" for analytics

### Compliance Dashboard
1. Check SLA status (green = ok, red = breached)
2. See time passed for each ticket
3. View analytics and metrics
4. Identify breached tickets

## 🛠️ Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| "Cannot connect to database" | Start PostgreSQL service |
| "Port 8000 in use" | `netstat -ano \| findstr :8000` then `taskkill /PID <number> /F` |
| "Module not found" | `pip install -r requirements_hackathon.txt` |
| "CORS error" | Ensure backend running at `http://localhost:8000` |
| "No database" | Run `psql -U postgres -f database_setup.sql` |

## 📡 API Quick Reference

```bash
# Create Ticket
curl -X POST http://localhost:8000/create-ticket \
  -H "Content-Type: application/json" \
  -d '{"user_input": "There is a flood at Main Street"}'

# Get All Tickets
curl http://localhost:8000/tickets

# Update Status
curl -X PUT http://localhost:8000/update-status/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "In Progress"}'

# Get Insights
curl http://localhost:8000/insights
```

## 🗄️ Database Quick Commands

```bash
# Connect to database
psql -U postgres -d grievance_db

# Show all tickets
SELECT * FROM tickets;

# Count tickets
SELECT COUNT(*) FROM tickets WHERE status='Open';

# See latest ticket
SELECT * FROM tickets ORDER BY created_at DESC LIMIT 1;

# Exit
\q
```

## 📂 Important Files

| File | Purpose |
|------|---------|
| main.py | Backend API |
| user.html | Citizen interface |
| officer.html | Officer dashboard |
| compliance.html | Compliance tracking |
| database_setup.sql | Database schema |

## 🎨 Color Scheme

- **HIGH Priority**: Red (#ffcccc)
- **MEDIUM Priority**: Yellow (#fff3cd)
- **LOW Priority**: Green (#d4edda)
- **Status Open**: Red (#dc3545)
- **Status In Progress**: Orange (#ffc107)
- **Status Resolved**: Green (#28a745)

## 💾 Database Credentials

- User: `postgres`
- Password: `password`
- Database: `grievance_db`
- Host: `localhost`
- Port: `5432`

## 📝 Key Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /create-ticket | Create new ticket |
| GET | /tickets | Get all tickets |
| PUT | /update-status/{id} | Update ticket status |
| GET | /insights | Get analytics |
| GET | /health | Health check |

## ⚡ Performance Tips

- Use SQL filters (location/priority) on dashboard
- Don't keep too many browser tabs open
- Restart PostgreSQL if slow
- Clear browser cache if issues
- Use Ctrl+Shift+Delete to clear cache

## 🔄 Typical Workflow

1. **Citizen** submits complaint via User Page → Ticket created
2. **Officer** views in Officer Dashboard → Can update status
3. **Officer** generates insights → See analytics
4. **Compliance Officer** tracks in Compliance Dashboard → Monitors SLA
5. **Officer** updates to "Resolved" → Compliance tracked

## 🎓 Learning Path

1. Read README.md (overview)
2. Follow INSTALLATION_GUIDE.md (setup)
3. Test with sample data
4. Create own tickets
5. Explore all dashboards
6. Check API docs at /docs
7. Modify code as needed

## 📞 Support Commands

```bash
# Check Python version
python --version

# Check pip
pip --version

# List installed packages
pip list | findstr fastapi

# Check if PostgreSQL running
psql -U postgres -c "SELECT 1"

# View live logs (while backend running)
# Just read console output
```

## 🚨 Emergency Stop

```bash
# Stop backend
Ctrl+C (in command prompt)

# Stop frontend server
Ctrl+C (in command prompt)

# Stop PostgreSQL
# Services → postgresql-x → Stop
# OR: pg_ctl stop
```

## ✨ Features at a Glance

✅ Create tickets from text  
✅ Auto priority detection  
✅ Auto issue classification  
✅ Auto location extraction  
✅ Auto SLA assignment  
✅ View all tickets  
✅ Filter by location  
✅ Filter by priority  
✅ Update ticket status  
✅ Generate insights  
✅ Monitor SLA compliance  
✅ Track time passed  
✅ Breach detection  
✅ Analytics dashboard  
✅ Mobile friendly UI  

---

**Everything you need to know on one page!** 📄
