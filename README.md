# AI-Powered Public Grievance System - Hackathon Edition

A complete web application for managing public grievances with AI-like processing, built with FastAPI, PostgreSQL, and vanilla HTML/CSS/JavaScript.

## Features

✅ **User Complaint Portal** - Citizens can submit grievances  
✅ **Government Officer Dashboard** - Manage tickets, filter, and update status  
✅ **Legal Compliance Dashboard** - SLA tracking and breach monitoring  
✅ **Smart Priority Detection** - AI-like keyword-based priority assignment  
✅ **Automatic Issue Classification** - Categorize complaints automatically  
✅ **SLA Management** - Track resolution timelines per priority  
✅ **Insights & Analytics** - Real-time compliance metrics  

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **No external dependencies** for frontend (zero frameworks)

## Project Structure

```
.
├── main.py                  # FastAPI backend application
├── user.html               # User complaint submission page
├── officer.html            # Government officer dashboard
├── compliance.html         # Legal compliance dashboard
├── requirements_hackathon.txt  # Python dependencies
├── database_setup.sql      # PostgreSQL schema and sample data
└── README.md              # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Modern web browser

### 1. Database Setup

```bash
# Start PostgreSQL (Windows)
pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start

# Or use:
psql -U postgres

# Run the setup script
psql -U postgres -f database_setup.sql
```

### 2. Install Python Dependencies

```bash
pip install -r requirements_hackathon.txt
```

### 3. Run the Backend

```bash
python main.py
```

Backend will start at: `http://localhost:8000`  
API Documentation: `http://localhost:8000/docs`

### 4. Open Frontend

Simply open in your browser:

```
file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/user.html
file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/officer.html
file:///C:/Users/91961/Desktop/digital_democracy_ai_calling/compliance.html
```

Or serve with Python:

```bash
# From the project directory
python -m http.server 8001
# Then visit: http://localhost:8001/user.html
```

## API Endpoints

### Create Ticket
```
POST /create-ticket
Body: { "user_input": "There is a flood at Main Street" }
Response: Ticket object with ID, priority, SLA, summary
```

### Get All Tickets
```
GET /tickets
Response: Array of all tickets
```

### Update Ticket Status
```
PUT /update-status/{ticket_id}
Body: { "status": "In Progress" }
Statuses: Open, In Progress, Resolved
```

### Get Insights
```
GET /insights
Response: Analytics with complaint counts, high priority tickets, most common issues
```

## Priority Detection Logic

- **HIGH**: Contains "flood", "fire", "accident", "urgent" (SLA: 1 hour)
- **MEDIUM**: Contains "water", "electricity" (SLA: 6 hours)
- **LOW**: Everything else (SLA: 24 hours)

## Issue Classification

- "garbage" → waste
- "flood"/"water" → flood
- "smoke" → pollution
- else → other

## User Roles

### 1. Citizen (User Page)
- Submit complaints via text input
- See generated ticket ID, priority, SLA
- Automatic issue classification

### 2. Government Officer (Officer Dashboard)
- View all tickets in a table
- Filter by location and priority
- Update ticket status
- Generate insights and analytics
- Visual highlighting of high-priority tickets

### 3. Legal Compliance Officer (Compliance Dashboard)
- Monitor SLA compliance
- See breach alerts (red highlight)
- Track time passed for each ticket
- View analytics: resolution rate, priority breakdown
- Key metrics: resolved, pending, breached

## Sample Data

Database comes pre-populated with 5 sample tickets:
- 2 HIGH priority (flood-related)
- 2 MEDIUM priority
- 1 LOW priority (resolved)

Use these for testing all features.

## Troubleshooting

### Connection Error
- Ensure PostgreSQL is running
- Check DATABASE_URL in main.py
- Verify database name is "grievance_db"

### CORS Error in Browser
- Already configured in FastAPI
- Ensure backend is running on http://localhost:8000

### Port Already in Use
- FastAPI: Change port in main.py line 236
- Python server: `python -m http.server 8002`

### Database Connection
- Default: postgres user, password "password"
- Modify CONNECTION_URL in main.py if different

## Sample Ticket Submission

Try submitting:
```
"There is a fire in the forest near the highway entrance"
Priority: HIGH
SLA: 1 hour

"Water is leaking from the municipal pipeline at East Side"
Priority: MEDIUM
SLA: 6 hours

"Garbage piled up on the street"
Priority: LOW
SLA: 24 hours
```

## Database Schema

```sql
tickets
├── id (PRIMARY KEY)
├── issue (VARCHAR) - Classified issue type
├── location (VARCHAR) - Extracted location
├── priority (VARCHAR) - HIGH/MEDIUM/LOW
├── status (VARCHAR) - Open/In Progress/Resolved
├── sla_hours (INTEGER) - Hours based on priority
├── summary (TEXT) - AI-generated summary
└── created_at (TIMESTAMP) - Creation time
```

## Performance

- Database queries indexed on: status, priority, location
- Frontend loads 100+ tickets without lag
- No external API calls (all processing local)

## Deployment Ready

- Can be deployed to AWS, Heroku, or any cloud platform
- CORS enabled for cross-origin requests
- Uses standard PostgreSQL (no cloud-specific features)

## Testing Checklist

✅ Submit complaint → Get ticket ID  
✅ View all tickets in officer dashboard  
✅ Filter by location and priority  
✅ Update ticket status  
✅ Generate insights  
✅ Check SLA breaches in compliance dashboard  
✅ Verify time passed calculation  
✅ Check priority highlighting  

---

**Built for Hackathon** - Simple, complete, and working! 🚀
