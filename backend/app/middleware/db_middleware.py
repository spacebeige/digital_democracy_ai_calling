from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import SessionLocal, is_neon_database_url


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """Attach one SQLAlchemy session per request and close it safely."""

    async def dispatch(self, request: Request, call_next):
        db = SessionLocal()
        request.state.db = db

        try:
            response = await call_next(request)

            # Guard against accidental uncommitted writes in handlers.
            if db.in_transaction():
                db.rollback()
            return response
        except SQLAlchemyError as exc:
            if db.in_transaction():
                db.rollback()
            detail = "Database operation failed"
            if is_neon_database_url():
                detail = "NeonDB operation failed"
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": detail, "details": str(exc)},
            )
        finally:
            db.close()


def get_request_db(request: Request):
    db = getattr(request.state, "db", None)
    if db is None:
        raise RuntimeError("Database session not initialized. Ensure DB middleware is enabled.")
    return db
