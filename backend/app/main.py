from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine, verify_database_connection
from app.middleware.db_middleware import DatabaseSessionMiddleware
from app.routes.call_routes import router as call_router
from app.routes.complaint_routes import router as complaint_router
from app.routes.sms_routes import router as sms_router
from app.config import QR_IMAGE_DIR

app = FastAPI(title="Digital Democracy AI")
app.add_middleware(DatabaseSessionMiddleware)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {"status": "running"}


@app.get("/db-health")
def db_health_check():
    verify_database_connection()
    return {"status": "ok"}

app.include_router(complaint_router, prefix="/complaints")
app.include_router(call_router, prefix="/calls")
app.include_router(sms_router, prefix="/sms")

QR_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/public/qr", StaticFiles(directory=str(QR_IMAGE_DIR)), name="qr_public")