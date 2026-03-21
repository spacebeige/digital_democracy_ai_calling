# System Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BROWSER (Client)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│  │  User Page       │  │ Officer         │  │ Compliance   ││
│  │  (user.html)     │  │ Dashboard       │  │ Dashboard    ││
│  │                  │  │ (officer.html)  │  │ (compliance) ││
│  │ - Submit Form    │  │                 │  │              ││
│  │ - Display Ticket │  │ - View Tickets  │  │ - Track SLA  ││
│  │ - Show Details   │  │ - Filter Data   │  │ - See Breach ││
│  │                  │  │ - Update Status │  │ - Analytics  ││
│  └────────┬─────────┘  └────────┬────────┘  └──────┬───────┘│
│           │                     │                  │        │
│           └─────────────┬───────┴──────────────────┘        │
│                         │                                   │
│              fetch() API Calls (JSON)                       │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│          FastAPI Server (Python) localhost:8000             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            API Endpoints (main.py)                   │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ POST   /create-ticket                               │  │
│  │ GET    /tickets                                      │  │
│  │ PUT    /update-status/{id}                           │  │
│  │ GET    /insights                                     │  │
│  │ GET    /health                                       │  │
│  │ GET    /docs (Swagger UI)                            │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│  ┌──────────────▼────────────────────────────────────────┐  │
│  │      Business Logic Layer                            │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                      │  │
│  │  detect_priority()                                   │  │
│  │    Keywords: flood, fire, accident, urgent → HIGH   │  │
│  │              water, electricity → MEDIUM             │  │
│  │              else → LOW                              │  │
│  │                                                      │  │
│  │  classify_issue()                                    │  │
│  │    "garbage" → waste                                 │  │
│  │    "flood"/"water" → flood                           │  │
│  │    "smoke" → pollution                               │  │
│  │    else → other                                      │  │
│  │                                                      │  │
│  │  get_sla_hours()                                     │  │
│  │    HIGH → 1 hour                                     │  │
│  │    MEDIUM → 6 hours                                  │  │
│  │    LOW → 24 hours                                    │  │
│  │                                                      │  │
│  │  generate_summary()                                  │  │
│  │    Creates AI-like ticket summary                    │  │
│  │                                                      │  │
│  │  extract_location()                                  │  │
│  │    Extracts location from complaint text             │  │
│  │                                                      │  │
│  └──────────────┬────────────────────────────────────────┘  │
│                 │                                           │
│  ┌──────────────▼─────────────────────────────────────────┐ │
│  │    ORM Layer (SQLAlchemy)                             │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │                                                       │ │
│  │  class TicketDB:                                      │ │
│  │    - id (PK)                                          │ │
│  │    - issue                                            │ │
│  │    - location                                         │ │
│  │    - priority (HIGH/MEDIUM/LOW)                       │ │
│  │    - status (Open/In Progress/Resolved)               │ │
│  │    - sla_hours (1/6/24)                               │ │
│  │    - summary                                          │ │
│  │    - created_at                                       │ │
│  │                                                       │ │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│     SQL Queries via psycopg2                               │
│                 │                                           │
└─────────────────┼───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│        PostgreSQL Database (localhost:5432)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Database: grievance_db                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              tickets table                          │   │
│  ├──────┬──────────┬──────────┬──────────┬──────────────┤   │
│  │  id  │  issue   │ location │priority  │ status  │SLA │   │
│  ├──────┼──────────┼──────────┼──────────┼─────────┼────┤   │
│  │  1   │  flood   │Main St   │  HIGH    │  Open   │  1 │   │
│  │  2   │  waste   │Downtown  │  LOW     │Resolved │ 24 │   │
│  │  3   │  flood   │River Bk  │  HIGH    │Progress │  1 │   │
│  │ ...  │  ...     │ ...      │  ...     │  ...    │... │   │
│  └──────┴──────────┴──────────┴──────────┴─────────┴────┘   │
│                                                             │
│  Indexes:                                                   │
│  - idx_tickets_status                                       │
│  - idx_tickets_priority                                     │
│  - idx_tickets_location                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Ticket Creation Flow

```
┌────────────────────────────────────────────────────────────┐
│ CITIZEN SUBMITS COMPLAINT VIA USER PAGE                    │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ Input: "There is a flood at Main St"
                       ↓
┌──────────────────────────────────────────────────────────────┐
│ BACKEND: POST /create-ticket                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Receive user_input                                       │
│  2. Run detect_priority() → "HIGH"                           │
│  3. Run classify_issue() → "flood"                           │
│  4. Run extract_location() → "Main St"                       │
│  5. Run get_sla_hours("HIGH") → 1 hour                       │
│  6. Run generate_summary() → "Complaint about flood..."      │
│  7. Create TicketDB object                                   │
│  8. Save to database                                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                       │
                       │ Output: Ticket object (JSON)
                       ↓
┌──────────────────────────────────────────────────────────────┐
│ FRONTEND: USER PAGE DISPLAYS                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Ticket ID:      1                                           │
│  Issue:          flood                                       │
│  Location:       Main St                                     │
│  Priority:       HIGH (RED HIGHLIGHT)                        │
│  Status:         Open                                        │
│  SLA:            1 hour                                      │
│  Summary:        Complaint about flood at Main St reported   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Officer Updates Status Flow

```
┌─────────────────────────────────────────────────────────────┐
│ OFFICER VIEWS OFFICER DASHBOARD                             │
│ GET /tickets → Display table with all tickets               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ OFFICER CLICKS "CHANGE STATUS" ON TICKET ID 1               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ MODAL DIALOG APPEARS                                        │
│ Select: In Progress                                         │
│ Click: Update                                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Input: {status: "In Progress"}
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: PUT /update-status/1                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Find ticket with id=1                                   │
│  2. Validate status value                                   │
│  3. Update status field                                     │
│  4. Save to database                                        │
│  5. Return updated ticket                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                       │
                       │ Output: Updated ticket (JSON)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: CLOSE MODAL AND REFRESH TABLE                     │
│ Status now shows: "In Progress" (YELLOW)                    │
└─────────────────────────────────────────────────────────────┘
```

### Insights Generation Flow

```
┌────────────────────────────────────────────────────────────┐
│ OFFICER CLICKS "GENERATE INSIGHTS"                         │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ fetch(/insights)
                       ↓
┌────────────────────────────────────────────────────────────┐
│ BACKEND: GET /insights                                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. Query all tickets                                      │
│  2. Count by status: Resolved, Pending                     │
│  3. Count by priority: HIGH                                │
│  4. Group by location: location_map                        │
│  5. Find most common issue                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
                       │
                       │ Output:
                       │ {
                       │   total_tickets: 5,
                       │   resolved: 1,
                       │   pending: 4,
                       │   high_priority: 2,
                       │   complaints_by_location: {...},
                       │   most_common_issue: "flood"
                       │ }
                       ↓
┌────────────────────────────────────────────────────────────┐
│ FRONTEND: DISPLAY STATS BOXES & INSIGHTS CARD             │
│                                                            │
│  Total Tickets: 5                                          │
│  Resolved: 1                                               │
│  High Priority: 2                                          │
│                                                            │
│  Pending: 4                                                │
│  Most Common Issue: flood                                  │
│  Complaints by Location: Main St (2), River Bk (1)...     │
└────────────────────────────────────────────────────────────┘
```

### SLA Monitoring Flow

```
┌──────────────────────────────────────────────────────────┐
│ COMPLIANCE OFFICER OPENS COMPLIANCE DASHBOARD             │
└────────────────────┬──────────────────────────────────────┘
                     │
                     │ fetch(/tickets)
                     ↓
┌──────────────────────────────────────────────────────────┐
│ BACKEND: GET /tickets → All tickets with timestamps      │
└────────────────────┬──────────────────────────────────────┘
                     │
                     │ Output: Ticket list with created_at
                     ↓
┌──────────────────────────────────────────────────────────┐
│ FRONTEND: COMPLIANCE DASHBOARD PROCESSING                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ For each ticket:                                         │
│   1. Calculate time_passed = now - created_at            │
│   2. If time_passed > sla_hours AND status != "Resolved":
│      → Mark as BREACHED (RED)                            │
│   3. Display time_passed in HH:MM format                 │
│                                                          │
│ Calculate alerts:                                        │
│   - Count breached tickets                               │
│   - Show alert if any breached                           │
│                                                          │
└────────────────────────────────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────────┐
│ DISPLAY COMPLIANCE DASHBOARD                             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ ⚠️  SLA BREACH ALERT: 1 ticket has exceeded SLA!        │
│                                                          │
│ [Table with tickets, highlighting breached ones]        │
│                                                          │
│ Stats: Total 5 | Resolved 1 | Pending 4                 │
│ Priority Breakdown: HIGH 2, MEDIUM 2, LOW 1              │
│ Resolution Rate: 20%                                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Component Interaction Diagram

```
                 ┌─────────────────────────┐
                 │    DATABASE LAYER       │
                 │  (PostgreSQL)           │
                 │  - tickets table        │
                 │  - 3 indexes            │
                 └────────────┬────────────┘
                              │
                              │ SQLAlchemy ORM
                              │
        ┌─────────────────────▼─────────────────────┐
        │      APPLICATION LAYER (FastAPI)          │
        │  ┌──────────────────────────────────────┐ │
        │  │ API Endpoints (/create-ticket, etc)  │ │
        │  └──────────────────────────────────────┘ │
        │  ┌──────────────────────────────────────┐ │
        │  │ Business Logic (priority, issue, etc)│ │
        │  └──────────────────────────────────────┘ │
        │  ┌──────────────────────────────────────┐ │
        │  │ Models & Validation (Pydantic)       │ │
        │  └──────────────────────────────────────┘ │
        └─────────────────────┬─────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 │   JSON over HTTP        │
                 │   (fetch API)           │
                 │   (CORS enabled)        │
                 └────────────┬────────────┘
                              │
        ┌─────────────────────▼──────────────────────┐
        │      PRESENTATION LAYER (Browser)          │
        │  ┌──────────────────────────────────────┐  │
        │  │ user.html (Citizen interface)        │  │
        │  ├──────────────────────────────────────┤  │
        │  │ JavaScript (fetch & DOM updates)     │  │
        │  └──────────────────────────────────────┘  │
        │  ┌──────────────────────────────────────┐  │
        │  │ officer.html (Officer dashboard)     │  │
        │  ├──────────────────────────────────────┤  │
        │  │ Filtering, sorting, insights         │  │
        │  └──────────────────────────────────────┘  │
        │  ┌──────────────────────────────────────┐  │
        │  │ compliance.html (Compliance tracking)│  │
        │  ├──────────────────────────────────────┤  │
        │  │ SLA monitoring, analytics            │  │
        │  └──────────────────────────────────────┘  │
        └──────────────────────────────────────────────┘
```

---

This architecture ensures:
- ✅ Separation of concerns
- ✅ Scalability
- ✅ Maintainability
- ✅ Performance
- ✅ Security
- ✅ User experience
