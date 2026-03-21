# Installation & Setup Guide

## Complete Setup Instructions

### Step 1: Prerequisites Installation

#### Python
- Download: https://www.python.org/downloads/ (3.8 or higher)
- During installation, check "Add Python to PATH"
- Verify: Open Command Prompt and run `python --version`

#### PostgreSQL
- Download: https://www.postgresql.org/download/
- Install with default settings
- Remember the password you set for 'postgres' user (default: "postgres")
- Verify: Open Command Prompt and run `psql --version`

### Step 2: Start PostgreSQL

**Windows:**
1. Open Services (services.msc)
2. Find "postgresql-x" service
3. Right-click → Start
OR
4. Open "pgAdmin" from Start Menu
5. It will start PostgreSQL automatically

**Alternative - Command Line:**
```bash
pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start
```

### Step 3: Set Up Database

```bash
# Open Command Prompt and navigate to project folder
cd C:\Users\91961\Desktop\digital_democracy_ai_calling

# Run the database setup script
psql -U postgres -f database_setup.sql
```

You should see output creating the database and inserting sample data.

**If you get password prompt:**
- Default password is usually "postgres"
- If different, edit the `main.py` file:
  ```python
  DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/grievance_db"
  ```

**Verify Database Creation:**
```bash
psql -U postgres -d grievance_db -c "SELECT COUNT(*) FROM tickets;"
```

### Step 4: Install Python Dependencies

```bash
# In the project directory
pip install -r requirements_hackathon.txt
```

Expected output:
```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 sqlalchemy-2.0.23 ...
```

### Step 5: Run the Backend

```bash
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 6: Access the Application

Open in your web browser:

**Option A: Direct file path**
- User Page: `file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/user.html`
- Officer Dashboard: `file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/officer.html`
- Compliance Dashboard: `file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/compliance.html`

**Option B: Python HTTP Server (recommended)**
```bash
# In another Command Prompt window, in the project directory
python -m http.server 8001
```

Then open in browser:
- User Page: `http://localhost:8001/user.html`
- Officer Dashboard: `http://localhost:8001/officer.html`
- Compliance Dashboard: `http://localhost:8001/compliance.html`

**Option C: API Documentation**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Quick Start Scripts

### Windows - Run all at once:
```bash
# Double-click start.bat
# OR from Command Prompt:
start.bat
```

### Linux/Mac - Run all at once:
```bash
chmod +x start.sh
./start.sh
```

## Testing the System

### Test 1: Create a Ticket
1. Go to User Page
2. Submit: "There is a flood at Main Street"
3. Verify:
   - Ticket ID is generated
   - Priority shows "HIGH"
   - SLA shows "1 hour"

### Test 2: View Tickets
1. Go to Officer Dashboard
2. Verify you see the ticket you just created
3. Click "Apply Filter"
4. You should see the ticket

### Test 3: Update Status
1. In Officer Dashboard
2. Click "Change Status" on any ticket
3. Select "In Progress"
4. Click "Update"
5. Verify status changed

### Test 4: Generate Insights
1. In Officer Dashboard
2. Click "Generate Insights"
3. You should see statistics about tickets

### Test 5: Check Compliance
1. Go to Compliance Dashboard
2. You should see:
   - Total tickets count
   - Resolved tickets count
   - SLA status for each ticket

## Troubleshooting

### Issue: "Connection refused" or "Cannot connect to database"

**Solution:**
1. Verify PostgreSQL is running:
   - Windows: Services → postgresql-x → check Status
   - Command: `psql -U postgres -c "SELECT 1"`
2. Check database name:
   - Run: `psql -U postgres -l` (list databases)
   - Should see "grievance_db"
3. Reset database:
   ```bash
   psql -U postgres -c "DROP DATABASE IF EXISTS grievance_db;"
   psql -U postgres -f database_setup.sql
   ```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with the number you found)
taskkill /PID <PID> /F

# Or change port in main.py line 236:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements_hackathon.txt --force-reinstall
```

### Issue: "Frontend pages won't load/APIs return CORS error"

**Solution:**
1. Make sure backend is running: `http://localhost:8000` should show API docs
2. CORS is already configured in FastAPI
3. Clear browser cache: Ctrl+Shift+Delete

### Issue: "FATAL: Ident authentication failed for user 'postgres'"

**Solution:**
This means PostgreSQL password authentication failed.
1. Check your PostgreSQL password
2. If you forgot it, reset it:
   ```bash
   psql -U postgres (you may need to auth differently)
   ALTER USER postgres WITH PASSWORD 'newpassword';
   ```
3. Update main.py with new password:
   ```python
   DATABASE_URL = "postgresql://postgres:newpassword@localhost:5432/grievance_db"
   ```

### Issue: "No module named 'psycopg2'"

**Solution:**
```bash
# psycopg2-binary should install automatically, but if not:
pip install psycopg2-binary
```

## File Structure

```
digital_democracy_ai_calling/
├── main.py                      # FastAPI backend
├── user.html                    # User complaint page
├── officer.html                 # Officer dashboard
├── compliance.html              # Compliance dashboard
├── database_setup.sql           # Database schema & sample data
├── requirements_hackathon.txt   # Python dependencies
├── start.bat                    # Windows starter script
├── start.sh                     # Linux/Mac starter script
├── README.md                    # Project overview
├── INSTALLATION_GUIDE.md        # This file
└── .env.example                 # Environment configuration template
```

## Common Commands

```bash
# Start backend
python main.py

# Start frontend server
python -m http.server 8001

# Check database
psql -U postgres -d grievance_db -c "SELECT * FROM tickets;"

# Reset database
psql -U postgres -f database_setup.sql

# View logs (during backend execution)
# Just read the console output

# Stop backend
# Ctrl+C in the Command Prompt window

# Stop frontend server
# Ctrl+C in the Command Prompt window

# Stop PostgreSQL
# Windows: services.msc → postgresql-x → Stop
```

## Performance Tips

1. If running slow, restart PostgreSQL
2. Close unnecessary browser tabs
3. Clear browser cache (Ctrl+Shift+Delete)
4. Ensure 4GB RAM available
5. Run on SSD for best performance

## Next Steps After Installation

1. **Create test tickets** using the User Page
2. **View them** in the Officer Dashboard
3. **Update statuses** to test functionality
4. **Generate insights** to see analytics
5. **Check compliance** in the Compliance Dashboard
6. **Modify the code** for your needs

## For Developers

### Adding Database Fields
1. Modify `TicketDB` model in `main.py`
2. Run database migration (or drop/recreate)
3. Update HTML forms accordingly

### Adding API Endpoints
1. Add function in `main.py` with `@app.get/post/put/delete`
2. Call from frontend using `fetch()`
3. Handle CORS if needed (already configured)

### Modifying Frontend
1. Edit `.html` files directly
2. Changes reflect immediately (refresh page)
3. Use browser DevTools (F12) for debugging

## Support & Debugging

### Enable Debug Mode
In `main.py`, change:
```python
# Add before uvicorn.run()
import logging
logging.basicConfig(level=logging.DEBUG)
```

### View Database Contents
```bash
# Connect to database
psql -U postgres -d grievance_db

# List tables
\dt

# View tickets
SELECT * FROM tickets;

# Count tickets
SELECT COUNT(*) FROM tickets;

# Exit
\q
```

### Check API Directly
```bash
# In Command Prompt
curl http://localhost:8000/tickets

# Or use browser: http://localhost:8000/docs
```

---

**Ready to go!** 🚀 If you encounter any issues, follow the troubleshooting section above.
