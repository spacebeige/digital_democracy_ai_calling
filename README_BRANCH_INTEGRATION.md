# Branch Integration README (aarya)

This document summarizes everything changed on branch `aarya` compared to `origin/main`, with special focus on database impact and practical integration steps for merging with other branches.

## 1. Scope and Baseline

- Branch: `aarya`
- Baseline used for this summary: `origin/main`
- Net diff summary: 24 files changed, 811 insertions, 24 deletions
- Main themes:
  - Database model expansion and migration path to Neon PostgreSQL
  - New complaint lifecycle APIs (create, conversation logs, summary generation, view)
  - New SMS + QR code flow using Twilio + static QR serving
  - Environment/configuration hardening for `.env` loading and DB URL support

## 2. Commit History in This Branch

1. `4d080fc` - twillio sms api working
2. `9bdc3bb` - added db tables#1
3. `2cad70b` - added sqldb and qr#2
4. `3fcffcb` - fixed db bugs
5. `daa7d31` - added qr in sms
6. `47b52a7` - neondb connected

## 3. File-by-File Change Highlights

### Environment and Repo Settings

- `.env.example`
  - Service host defaults adjusted:
    - `LLM_API=http://llm:9002`
    - `STT_API=http://stt:9000`
    - `TTS_API=http://tts:9001`
  - Added SMS/Twilio variables:
    - `TWILIO_ACCOUNT_SID`
    - `TWILIO_AUTH_TOKEN`
    - `TWILIO_FROM_NUMBER`
    - `TWILIO_PUBLIC_BASE_URL` (commented placeholder)
    - `SMS_DEFAULT_COUNTRY_CODE`
    - `SMS_DRY_RUN`
    - `QR_IMAGE_DIR`

- `.gitignore`
  - Added ignore entries for `.env.example` and `.env.*`
  - Removed blanket `*.db` ignore in this branch version (DB files are now trackable unless ignored elsewhere)

### Backend Core Configuration

- `backend/app/config.py`
  - Loads env in two layers:
    - `backend/.env` with override enabled
    - workspace `.env` as fallback
  - Added bool parser helper for config values
  - Added Twilio/SMS/QR config constants

- `backend/app/database.py`
  - Switched hardcoded SQLite URL to env-driven `DATABASE_URL`
  - Default now: `sqlite:///./governance.db`
  - Added SQLite-specific `check_same_thread=False`
  - Added pooled connection pre-ping for reliability

- `backend/app/__init__.py`
  - Added package marker file to ensure correct local package resolution

### Database Models and Schema Surface

- `backend/app/models.py`
  - `complaints` table expanded and field names changed:
    - old shape (from main): `phone_number`, `issue`, `department`, `status`, `created_at`
    - new shape: `phone`, `issue_text`, `summary`, `language`, `sentiment`, `priority`, `status`, `assigned_to`, `location`, `expected_resolution`, `created_at`
  - Added `conversation_logs` table:
    - `id`, `complaint_id` (FK to complaints), `speaker`, `message`, `timestamp`
  - Added `audit_logs` table:
    - `id`, `complaint_id` (FK to complaints), `action`, `actor`, `timestamp`
  - Added ORM relationships and cascade delete behavior from complaint to logs

- `backend/app/schemas.py`
  - Added new API contracts for:
    - ticket SMS request/response
    - create complaint
    - log conversation
    - generate summary
    - complaint view with nested conversation and audit arrays

### Routes and Service Behavior

- `backend/app/main.py`
  - Added SMS router at `/sms`
  - Added static mount for QR images at `/public/qr`

- `backend/app/routes/call_routes.py`
  - Updated persistence to match new complaint columns:
    - stores `phone`, `issue_text`, derived `summary`, and status/priority defaults

- `backend/app/routes/complaint_routes.py`
  - Existing `/complaints/` query endpoint retained
  - Added:
    - `POST /complaints/create-complaint`
    - `POST /complaints/log-conversation`
    - `POST /complaints/generate-summary`
    - `GET /complaints/complaint/{id}`
  - Integrates DB writes, reads, and audit logging

- `backend/app/routes/sms_routes.py` (new)
  - Adds `POST /sms/send-ticket`
  - Optional QR generation + MMS media URL composition
  - Validates generated path is under configured QR directory

- `backend/app/services/sms_service.py` (new)
  - Phone normalization helper
  - Message body builder with optional metadata lines
  - Dry-run support via request flag or env default
  - Twilio API integration and graceful failure response

- `backend/app/services/qr_service.py` (new)
  - Generates PNG QR code files under configured QR directory
  - Sanitizes ticket/session fragments for safe filenames

### Documentation, Dependencies, and Tooling

- `backend/requirements.txt`
  - Added:
    - `psycopg[binary]`
    - `twilio`
    - `qrcode`
    - `pillow`

- `backend/NEON_SETUP.md` (new)
  - Documents Neon setup and startup-based table creation
  - Documents optional SQLite -> Neon data copy process

- `backend/scripts/migrate_sqlite_to_neondb.py` (new)
  - Reflects source and target metadata
  - Creates target tables if missing
  - Replaces target table contents from source snapshot
  - Skips tables with column mismatch

### Binary/Data Artifacts Added in Branch

- SQLite DB binaries committed:
  - `backend/complaints.db`
  - `backend/governance.db`
  - `database/sqlite/grievance_system.db`
  - `governance.db`
- QR sample files committed:
  - `backend/data/qr/*.png`
  - `backend/backend/data/qr/*.png`

These are useful examples for local testing but can cause merge noise and repository bloat if retained permanently.

## 4. Database Change Log (Comprehensive)

## 4.1 DB Connection Model Changes

- DB target is now runtime-configurable using `DATABASE_URL`.
- Supported modes:
  - SQLite local (default)
  - Neon PostgreSQL via `postgresql+psycopg://...`
- Startup creates tables automatically using SQLAlchemy metadata.

## 4.2 Logical Schema Changes

### complaints (breaking changes vs main)

- Column rename/mapping changes:
  - `phone_number` -> `phone`
  - `issue` -> `issue_text`
  - `department` removed as direct column; department is now inferred and can be represented in summary/metadata
- New optional operational fields:
  - `summary`, `language`, `sentiment`, `priority`, `assigned_to`, `location`, `expected_resolution`
- `status` semantics changed from `pending/processed` style to values like `OPEN` used by new flows

### new table: conversation_logs

- Stores ordered conversational turns for a complaint.
- Enables later summarization and traceability.

### new table: audit_logs

- Stores internal actions (`created`, `summary_generated`, etc.) with actor and timestamp.
- Adds operational audit trail.

## 4.3 Migration Script Semantics

- Script path: `backend/scripts/migrate_sqlite_to_neondb.py`
- Source defaults to `sqlite:///./governance.db`
- Target requires `TARGET_NEON_URL`
- Migration behavior is replace-style per table:
  - target table rows are deleted before inserting source rows
- If table exists but columns differ, table is skipped and listed

## 5. Integration Guide with Other Branches

Use this sequence to integrate safely and avoid DB/API regressions.

### Step 1: Pre-merge Preparation

1. Fetch all remotes and ensure local baseline is current.
2. Decide target branch for integration (for example, `main` or a feature integration branch).
3. Snapshot current databases before schema work.

Recommended commands:

```powershell
git fetch --all --prune
git checkout <target-branch>
git pull --ff-only
git checkout -b integrate/aarya-into-<target>
```

### Step 2: Merge and Resolve High-Risk Conflict Areas

Merge branch:

```powershell
git merge --no-ff aarya
```

Prioritize careful review in these files:

- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/routes/complaint_routes.py`
- `backend/app/routes/call_routes.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `.env.example`
- `.gitignore`

Conflict policy recommendation:

- Keep this branch's model/schema evolution as source of truth if integrating complaint lifecycle features.
- Reconcile any other branch logic that still uses old fields (`phone_number`, `issue`, `department`) by adapting to the new model.

### Step 3: Dependency Alignment

From `backend` folder:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Confirm these packages are present in final merged lock/environment:

- fastapi
- uvicorn
- sqlalchemy
- psycopg[binary]
- twilio
- qrcode
- pillow

### Step 4: Environment File Integration

Ensure final merged `.env` has at least:

```dotenv
DATABASE_URL=sqlite:///./governance.db
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
TWILIO_PUBLIC_BASE_URL=
SMS_DEFAULT_COUNTRY_CODE=+91
SMS_DRY_RUN=true
QR_IMAGE_DIR=backend/data/qr
```

Notes:

- For Neon production/staging, set `DATABASE_URL` to Neon URL with SSL.
- `TWILIO_PUBLIC_BASE_URL` must be publicly reachable if using MMS image attachments.
- Avoid committing real credentials.

### Step 5: Database Strategy During Integration

Choose one path:

1. SQLite-first local testing
   - Keep `DATABASE_URL=sqlite:///./governance.db`
   - Start app to auto-create schema
2. Neon-first integration
   - Set Neon `DATABASE_URL`
   - Start app to create schema
   - Optionally run migration script from local SQLite snapshot

Migration command (optional):

```powershell
cd backend
$env:PYTHONPATH='.'
$env:SOURCE_SQLITE_URL='sqlite:///./governance.db'
$env:TARGET_NEON_URL='postgresql+psycopg://user:password@host/neondb?sslmode=require'
..\.venv\Scripts\python.exe scripts\migrate_sqlite_to_neondb.py
```

### Step 6: API Contract Regression Checks

After merge, validate these endpoints:

- `GET /` health
- `GET /calls/health`
- `POST /calls/handle-turn`
- `POST /complaints/`
- `POST /complaints/create-complaint`
- `POST /complaints/log-conversation`
- `POST /complaints/generate-summary`
- `GET /complaints/complaint/{id}`
- `POST /sms/send-ticket`
- `GET /public/qr/<file>.png` (when QR generated)

### Step 7: Data and Artifact Hygiene Decision

Before final merge to shared branch, decide whether to keep or remove committed binary artifacts:

- `.db` files in repo
- generated QR PNGs in repo

Recommended for long-term cleanliness:

1. Remove generated test data from source control.
2. Add explicit ignore patterns for runtime DB and QR output paths.
3. Keep only deterministic fixtures if needed for tests.

## 6. Backward Compatibility Notes

If another branch still reads old complaint fields:

- Replace references:
  - `phone_number` -> `phone`
  - `issue` -> `issue_text`
- Remove assumptions that `department` is a persisted DB column.
- Update serializers and frontend mapping accordingly.

## 7. Suggested Post-merge Validation Checklist

1. App starts without SQLAlchemy errors.
2. Tables `complaints`, `conversation_logs`, `audit_logs` exist in target DB.
3. `POST /complaints/create-complaint` inserts rows successfully.
4. `POST /complaints/log-conversation` and `/generate-summary` work on same complaint.
5. `POST /sms/send-ticket` works in dry-run mode.
6. `POST /sms/send-ticket` works with Twilio credentials in non-dry-run mode.
7. QR static file route serves generated image.
8. No secrets are committed in tracked files.

## 8. Integration Risks to Watch

- Schema incompatibility if parallel branches changed complaint model differently.
- Runtime errors if env keys are missing after merge.
- Merge conflicts in centralized files (`models.py`, `schemas.py`, `complaint_routes.py`).
- Accidental shipping of local `.db` binaries or generated QR artifacts.

## 9. Quick Decision Summary for Integrators

- If your target branch does not need the new complaint lifecycle, isolate route/model additions before merge.
- If your target branch needs SMS/QR ticket dispatch, keep all config + route + service additions as a unit.
- For shared environments, prefer Neon and run migration once after schema verification.
