# Remote Branch Comparison for aarya

This document compares the current branch `aarya` against every remote branch under `origin/*`.

Comparison date: 2026-03-25
Repository: digital_democracy_ai_calling

## 1. Branches Compared

Included remote branches:

- origin/main
- origin/B1
- origin/b1
- origin/oomkar
- origin/parth
- origin/aarya

Note:

- The symbolic ref `origin/HEAD -> origin/main` is excluded from analysis.
- A pseudo ref named `origin/origin` appeared in local ref listing and is ignored for practical integration planning.

## 2. Quick Divergence Matrix (vs current HEAD = aarya)

Interpretation:

- ahead = commits in aarya not in target branch
- behind = commits in target branch not in aarya
- files = symmetric diff file count from `git diff target...HEAD`

| Target remote branch | ahead | behind | files |
| -------------------- | ----: | -----: | ----: |
| origin/aarya         |     0 |      0 |     0 |
| origin/main          |     6 |      0 |    24 |
| origin/B1            |     6 |      0 |    24 |
| origin/b1            |     6 |      3 |    24 |
| origin/oomkar        |     6 |      2 |    24 |
| origin/parth         |     6 |     10 |    24 |

## 3. Commits unique to aarya (when compared to other remote branches)

The following 6 commits are present in `aarya` and missing from `origin/main`, `origin/B1`, `origin/b1`, `origin/oomkar`, and `origin/parth`:

1. 47b52a7 - neondb connected
2. daa7d31 - added qr in sms
3. 3fcffcb - fixed db bugs
4. 2cad70b - added sqldb and qr#2
5. 9bdc3bb - added db tables#1
6. 4d080fc - twillio sms api working

## 4. Commits unique to each remote branch

### origin/main

- none

### origin/B1

- none

### origin/b1

1. 7db3b9b - "3 DASHBOARDS OF 1.CITIZEN 2.GOVERMENT 3.LEGAL COMPLIANCE OFFICER"
2. 7350c99 - 3 DASHBOARDS OF 1.CITIZEN 2.GOVERMENT 3.LEGAL COMPLIANCE OFFICER
3. 11ce659 - Initial commit: Ticketing State Machine (Layer 4)

### origin/oomkar

1. 356a28c - updated the logic for south indian languages and urdu
2. 4b71292 - asr stt tts done

### origin/parth

1. 647e252 - Integration attempt 1
2. c1408f5 - Add voice-to-analysis integration and testing guide
3. 5376556 - Fix post-call analyzer integration with SmartRouter
4. c6c119e - Add implementation complete summary
5. 468788c - Add voice-to-NLP pipeline with Python 3.12 support
6. 653a978 - Managing the changes on multiple devices
7. 356a28c - updated the logic for south indian languages and urdu
8. 4b71292 - asr stt tts done
9. f119a96 - a little few changes

## 5. File-Level Delta from aarya to each target branch

The symmetric file diff set is currently the same 24 files for all non-aarya targets:

- .env.example (modified)
- .gitignore (modified)
- backend/NEON_SETUP.md (added)
- backend/app/**init**.py (added)
- backend/app/config.py (modified)
- backend/app/database.py (modified)
- backend/app/main.py (modified)
- backend/app/models.py (modified)
- backend/app/routes/call_routes.py (modified)
- backend/app/routes/complaint_routes.py (modified)
- backend/app/routes/sms_routes.py (added)
- backend/app/schemas.py (modified)
- backend/app/services/qr_service.py (added)
- backend/app/services/sms_service.py (added)
- backend/backend/data/qr/TCK1234ABCD-TCK1234ABCD.png (added)
- backend/complaints.db (added)
- backend/data/qr/TCK1234ABCD-TCK1234ABCD.png (added)
- backend/data/qr/TKT-QR-001-session.png (added)
- backend/data/qr/TKT-REAL-001-session.png (added)
- backend/governance.db (added)
- backend/requirements.txt (modified)
- backend/scripts/migrate_sqlite_to_neondb.py (added)
- database/sqlite/grievance_system.db (added)
- governance.db (added)

## 6. Integration Priority Recommendation

Given divergence and likely conflict probability:

1. Integrate with origin/main (or origin/B1) first

- lowest complexity (behind=0)
- validates your 6 commits in clean baseline

2. Integrate with origin/oomkar next

- moderate complexity (behind=2)
- likely overlap in speech pipeline and service endpoints

3. Integrate with origin/b1

- higher complexity (behind=3)
- potential product/dashboard-level contract overlap

4. Integrate with origin/parth last

- highest complexity (behind=10)
- broad integration surface and likely route/schema conflicts

## 7. Suggested Merge Sequence Commands

```powershell
# Example: integration branch from main
git checkout main
git pull --ff-only
git checkout -b integrate/aarya-all-remotes

# Merge aarya first
git merge --no-ff aarya

# Then merge other target branch work in priority order
git merge --no-ff origin/oomkar
git merge --no-ff origin/b1
git merge --no-ff origin/parth
```

## 8. High-Conflict Hotspots Across Branches

Review these files first during each merge:

- backend/app/models.py
- backend/app/schemas.py
- backend/app/routes/complaint_routes.py
- backend/app/routes/call_routes.py
- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- backend/requirements.txt

## 9. Clear Merge Conflicts You Can Expect

Use this as a practical conflict-resolution map while merging `origin/oomkar`, `origin/b1`, and `origin/parth` into work that already contains `aarya`.

### 9.1 backend/app/models.py

Likely conflict:

- other branches may still use old complaint fields (`phone_number`, `issue`, `department`)
- `aarya` uses new complaint shape (`phone`, `issue_text`, `summary`, `priority`, etc.) plus `conversation_logs` and `audit_logs`

Resolution rule:

- keep `aarya` model structure as source of truth
- port any business logic from other branches by remapping field usage to new names
- do not drop `conversation_logs` or `audit_logs`

### 9.2 backend/app/schemas.py

Likely conflict:

- request/response models added by other branches for voice analysis may overlap with the new complaint and SMS schemas
- duplicate model names or conflicting required/optional fields

Resolution rule:

- keep all `aarya` models for complaint lifecycle and SMS (`SendTicketSMS*`, `CreateComplaint*`, `ConversationLog*`, `GenerateSummary*`, `ComplaintViewResponse`)
- merge additional schemas from other branches without renaming existing contracts unless absolutely required
- if rename is unavoidable, update all affected routers and clients in same merge commit

### 9.3 backend/app/routes/complaint_routes.py

Likely conflict:

- both sides may add new endpoints or modify imports/session handling
- route body logic may conflict around summary generation and DB writes

Resolution rule:

- preserve these endpoints from `aarya`:
  - `POST /complaints/create-complaint`
  - `POST /complaints/log-conversation`
  - `POST /complaints/generate-summary`
  - `GET /complaints/complaint/{id}`
- reconcile extra endpoints from other branches by adding, not replacing, unless behavior is intentionally superseded

### 9.4 backend/app/routes/call_routes.py

Likely conflict:

- `aarya` persists calls using new complaint fields
- voice branches (`oomkar` and `parth`) may change STT/LLM/TTS flow and returned metadata

Resolution rule:

- keep latest voice pipeline improvements from incoming branch
- ensure final persistence call writes to `phone`, `issue_text`, `summary`, `priority`, `status`
- reject merges that reintroduce old columns (`phone_number`, `issue`, `department`)

### 9.5 backend/app/main.py

Likely conflict:

- router includes may diverge
- static file mounting for QR may be removed accidentally

Resolution rule:

- final merged file must include all required routers (`complaints`, `calls`, `sms`)
- keep QR static mount:
  - `app.mount("/public/qr", StaticFiles(...), name="qr_public")`

### 9.6 backend/app/config.py and backend/app/database.py

Likely conflict:

- env loading strategy and `DATABASE_URL` handling may differ
- some branches may assume hardcoded local SQLite

Resolution rule:

- keep env-first configuration from `aarya`
- keep `DATABASE_URL` support and SQLite `check_same_thread=False` handling
- keep Twilio/SMS/QR config variables

### 9.7 backend/requirements.txt

Likely conflict:

- dependency list order/content overlap
- missing packages after manual conflict cleanup

Resolution rule:

- final requirements must include:
  - `psycopg[binary]`
  - `twilio`
  - `qrcode`
  - `pillow`
- then include voice/analysis dependencies from other branches

### 9.8 .env.example and .gitignore

Likely conflict:

- env template keys may be overwritten
- `.gitignore` changes may re-include sensitive/generated files

Resolution rule:

- keep all SMS/Twilio/QR env keys from `aarya`
- keep/restore ignore policy intentionally (decide if `.db` and generated QR files should be tracked)
- never keep real secrets in tracked env files

### 9.9 Binary artifact conflicts

Likely conflict:

- `.db` and `.png` binary files will frequently conflict and cannot be merged line-by-line

Resolution rule:

- prefer one side (usually latest valid test snapshot) or remove binaries from git
- recommended long-term approach: stop tracking runtime DB/QR artifacts and regenerate locally

## 10. Validation Checklist After Each Merge Step

1. Start backend and confirm startup succeeds.
2. Verify DB connection in selected environment (SQLite or Neon).
3. Hit API health endpoints:
   - GET /
   - GET /calls/health
4. Validate complaint lifecycle endpoints.
5. Validate SMS dry-run endpoint behavior.
6. Re-run smoke tests and resolve schema mismatches immediately.

## 11. Notes on Current Repository State

- This branch contains committed binary DB snapshots and generated QR images.
- Keeping these may increase merge conflicts and repo size.
- Consider a policy for runtime-generated artifacts before final integration to shared branches.
