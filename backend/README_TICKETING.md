# 🎫 Ticketing State Machine Backend

A minimal, hackathon-ready Ticketing System backend built with **FastAPI** and **SQLite**.

## Features ✨

- ✅ **State Machine Validation**: Enforced ticket status transitions
- ✅ **Auto Ticket ID Generation**: Unique TCK identifiers
- ✅ **Smart Priority Detection**: Auto-detects priority from issue keywords
- ✅ **SMS Simulation**: Prints SMS notifications on ticket creation
- ✅ **Analytics**: Ticket count grouped by location
- ✅ **SQLite Database**: No external DB needed
- ✅ **SQLAlchemy ORM**: Clean database models
- ✅ **Pydantic Validation**: Strong request/response validation

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & endpoints
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # SQLite configuration
│   └── utils.py             # Ticket ID gen & priority detection
├── requirements.txt         # Python dependencies
└── tickets.db              # SQLite database (auto-created)
```

---

## Installation & Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Database initialized
```

### 3. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Database Schema

### Tickets Table

```sql
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id VARCHAR UNIQUE NOT NULL,
    issue VARCHAR NOT NULL,
    location VARCHAR NOT NULL,
    priority VARCHAR DEFAULT 'MEDIUM',
    status VARCHAR DEFAULT 'OPEN',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Auto-increment primary key
- `ticket_id`: Unique identifier (e.g., TCK1234ABCD)
- `issue`: Issue description
- `location`: Location where issue occurred
- `priority`: LOW | MEDIUM | HIGH
- `status`: OPEN | ASSIGNED | IN_PROGRESS | RESOLVED | CLOSED | REOPENED
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update

---

## API Endpoints

### Health Check

```http
GET /
```

**Response:**
```json
{
  "status": "running",
  "message": "Ticketing State Machine API is active"
}
```

---

### Create Ticket

```http
POST /ticket/create
Content-Type: application/json

{
  "issue": "Road flooded near market",
  "location": "Market Street",
  "priority": "HIGH"
}
```

**Response:**
```json
{
  "id": 1,
  "ticket_id": "TCK1234ABCD",
  "issue": "Road flooded near market",
  "location": "Market Street",
  "priority": "HIGH",
  "status": "OPEN",
  "created_at": "2026-03-21T10:30:00",
  "updated_at": "2026-03-21T10:30:00"
}
```

**Console Output:**
```
📱 SMS: Your complaint is registered. Ticket ID: TCK1234ABCD
```

---

### Get All Tickets

```http
GET /tickets
```

**Response:**
```json
{
  "tickets": [
    {
      "id": 1,
      "ticket_id": "TCK1234ABCD",
      "issue": "Road flooded near market",
      "location": "Market Street",
      "priority": "HIGH",
      "status": "OPEN",
      "created_at": "2026-03-21T10:30:00",
      "updated_at": "2026-03-21T10:30:00"
    }
  ],
  "total_count": 1
}
```

---

### Get Single Ticket

```http
GET /ticket/TCK1234ABCD
```

**Response:**
```json
{
  "id": 1,
  "ticket_id": "TCK1234ABCD",
  "issue": "Road flooded near market",
  "location": "Market Street",
  "priority": "HIGH",
  "status": "OPEN",
  "created_at": "2026-03-21T10:30:00",
  "updated_at": "2026-03-21T10:30:00"
}
```

---

### Update Ticket Status (State Machine)

```http
PUT /ticket/TCK1234ABCD/status
Content-Type: application/json

{
  "status": "ASSIGNED"
}
```

**Response:**
```json
{
  "id": 1,
  "ticket_id": "TCK1234ABCD",
  "issue": "Road flooded near market",
  "location": "Market Street",
  "priority": "HIGH",
  "status": "ASSIGNED",
  "created_at": "2026-03-21T10:30:00",
  "updated_at": "2026-03-21T10:35:00"
}
```

---

## State Machine Transitions

```
OPEN
  ↓
ASSIGNED
  ↓
IN_PROGRESS
  ↓
RESOLVED
  ├→ CLOSED (terminal state)
  └→ REOPENED
      ↓
    IN_PROGRESS

CLOSED is a terminal state - no further transitions
```

### Valid Transitions Table

| Current Status | Valid Next States |
|---|---|
| OPEN | ASSIGNED |
| ASSIGNED | IN_PROGRESS |
| IN_PROGRESS | RESOLVED |
| RESOLVED | CLOSED, REOPENED |
| REOPENED | IN_PROGRESS |
| CLOSED | (none) |

### Invalid Transition Example

```http
PUT /ticket/TCK1234ABCD/status
{
  "status": "CLOSED"
}
```

**Error Response (400):**
```json
{
  "error": "Invalid transition: OPEN → CLOSED. Valid transitions from OPEN: ASSIGNED"
}
```

---

### Get Analytics

```http
GET /analytics
```

**Response:**
```json
{
  "analytics": {
    "Market Street": 5,
    "Hospital Road": 3,
    "Railway Station": 2
  }
}
```

---

## Priority Auto-Detection

The system automatically detects priority based on keywords in the issue:

### HIGH Priority Keywords
- "flood"
- "fire"
- "accident"
- "emergency"
- "critical"

### LOW Priority Keywords
- "garbage"
- "waste"
- "litter"
- "minor"

### Default
- If no keywords match → **MEDIUM**

### Example

```bash
# This will auto-detect as HIGH
POST /ticket/create
{
  "issue": "Major fire outbreak in warehouse",
  "location": "Industrial Area"
}
```

The system will set priority to HIGH automatically.

---

## Testing with cURL

### Create a Ticket
```bash
curl -X POST "http://localhost:8000/ticket/create" \
  -H "Content-Type: application/json" \
  -d '{
    "issue": "Road flooded near market",
    "location": "Market Street"
  }'
```

### Get All Tickets
```bash
curl "http://localhost:8000/tickets"
```

### Get Single Ticket
```bash
curl "http://localhost:8000/ticket/TCK1234ABCD"
```

### Update Status
```bash
curl -X PUT "http://localhost:8000/ticket/TCK1234ABCD/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "ASSIGNED"}'
```

### Get Analytics
```bash
curl "http://localhost:8000/analytics"
```

---

## Testing with Python

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Create a ticket
response = requests.post(f"{BASE_URL}/ticket/create", json={
    "issue": "Pothole on main road",
    "location": "Main Street"
})
ticket = response.json()
ticket_id = ticket["ticket_id"]
print(f"Created: {ticket_id}")

# Get ticket
response = requests.get(f"{BASE_URL}/ticket/{ticket_id}")
print(response.json())

# Update status
response = requests.put(f"{BASE_URL}/ticket/{ticket_id}/status", json={
    "status": "ASSIGNED"
})
print(response.json())

# Get analytics
response = requests.get(f"{BASE_URL}/analytics")
print(response.json())
```

---

## Error Handling

### 404 - Ticket Not Found
```json
{
  "error": "Ticket TCK9999ZZZZ not found",
  "status_code": 404
}
```

### 400 - Invalid Status Transition
```json
{
  "error": "Invalid transition: OPEN → RESOLVED. Valid transitions from OPEN: ASSIGNED"
}
```

---

## Database Files

- **SQLite DB**: `backend/tickets.db` (auto-created on first run)
- **Can be reset**: Just delete `tickets.db` and restart the app

---

## Deployment

### Using Gunicorn (Production)

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### Using Docker (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t ticketing-api .
docker run -p 8000:8000 ticketing-api
```

---

## Development Notes

- **ORM**: SQLAlchemy with SQLite
- **Validation**: Pydantic models for input/output
- **Async**: FastAPI with async endpoints ready
- **CORS**: Can be enabled in `main.py` if needed
- **Logging**: Can be enabled by setting `echo=True` in `database.py`

---

## Hackathon Tips 🚀

1. **Quick Start**: Just run `pip install -r requirements.txt && uvicorn app.main:app --reload`
2. **Test Everything**: Visit http://localhost:8000/docs for interactive API testing
3. **Modify States**: Edit `VALID_TRANSITIONS` in `utils.py` to customize workflows
4. **Add Fields**: Easily add more fields to `Ticket` model in `models.py`
5. **Change Priority Keywords**: Update `detect_priority()` in `utils.py`

---

## License

MIT - Use freely for hackathons!

---

**Made with ❤️ for hackathons**
