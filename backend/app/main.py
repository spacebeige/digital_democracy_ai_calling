from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine, verify_database_connection
from app.middleware.db_middleware import DatabaseSessionMiddleware
from app.routes.call_routes import router as call_router
from app.routes.complaint_routes import router as complaint_router
from app.routes.router_routes import router as router_router
from app.routes.analysis_routes import router as analysis_router
from app.routes.enhanced_grievance_routes import router as enhanced_router
from app.routes.enhanced_grievance_routes_db import router as enhanced_db_router  # NEW: DB-integrated
from app.routes.sms_routes import router as sms_router
from app.config import QR_IMAGE_DIR

app = FastAPI(title="Digital Democracy AI - Enhanced Edition with DB")
app.add_middleware(DatabaseSessionMiddleware)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {
        "status": "running",
        "version": "2.2.1-db-integrated",
        "features": [
            "vulgarity_detection",
            "state_schemes_mapping",
            "enhanced_ai_summary",
            "urgency_detection",
            "multilingual_support_20_plus",
            "code_mixing_hinglish_tanglish",
            "database_persistence",
            "low_latency_caching"
        ]
    }


@app.get("/db-health")
def db_health_check():
    verify_database_connection()
    return {"status": "ok"}

app.include_router(complaint_router, prefix="/complaints")
app.include_router(call_router, prefix="/calls")
app.include_router(router_router)
app.include_router(analysis_router)
app.include_router(enhanced_router)  # Original enhanced routes
app.include_router(enhanced_db_router)  # NEW: DB-integrated routes
app.include_router(sms_router, prefix="/sms")

QR_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/public/qr", StaticFiles(directory=str(QR_IMAGE_DIR)), name="qr_public")