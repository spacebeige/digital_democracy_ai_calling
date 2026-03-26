# NeonDB Setup (same tables as SQLite)

This project uses SQLAlchemy models from `app/models.py`, so NeonDB (PostgreSQL) will use the same table structure (`complaints`, `conversation_logs`, `audit_logs`).

## 1. Install dependency

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Get Neon connection string

From Neon Console, copy your SQLAlchemy-compatible URL and ensure SSL is required.

Example:

```env
DATABASE_URL=postgresql+psycopg://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require
```

If your password has special characters like `@`, `:`, `/`, `%`, URL-encode it before putting it in `DATABASE_URL`.

## 3. Set backend DB URL

Set `DATABASE_URL` in `backend/.env`.

## 4. Create same tables in NeonDB

Run backend startup once (it calls `Base.metadata.create_all`):

```powershell
cd backend
$env:PYTHONPATH='.'
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8014
```

Then stop it after startup logs indicate app initialized.

## 5. Migrate existing SQLite data (optional)

If you already have data in SQLite and want it copied:

```powershell
cd backend
$env:PYTHONPATH='.'
$env:SOURCE_SQLITE_URL='sqlite:///./governance.db'
$env:TARGET_NEON_URL='postgresql+psycopg://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require'
..\.venv\Scripts\python.exe scripts\migrate_sqlite_to_neondb.py
```

## 6. Verify

From backend host:

```powershell
cd backend
$env:PYTHONPATH='.'
..\.venv\Scripts\python.exe -c "from app.database import engine; conn = engine.connect(); print('DB OK'); conn.close()"
```

## 7. Schema and Middleware Change Checklist

For every table or schema update, follow:

- `backend/app/middleware/SCHEMA_CHANGE_CHECKLIST.md`

This checklist explains what to update in models, schemas, routes, migration flow, and when middleware changes are actually required.
