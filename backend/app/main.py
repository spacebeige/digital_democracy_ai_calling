from fastapi import FastAPI
from app.database import Base, engine
from app.routes.call_routes import router as call_router
from app.routes.complaint_routes import router as complaint_router
from app.routes.router_routes import router as router_router
from app.routes.analysis_routes import router as analysis_router
from app.routes.enhanced_grievance_routes import router as enhanced_router
from app.routes.enhanced_grievance_routes_db import router as enhanced_db_router  # NEW: DB-integrated

app = FastAPI(title="Digital Democracy AI - Enhanced Edition with DB")


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

app.include_router(complaint_router, prefix="/complaints")
app.include_router(call_router, prefix="/calls")
app.include_router(router_router)
app.include_router(analysis_router)
app.include_router(enhanced_router)  # Original enhanced routes
app.include_router(enhanced_db_router)  # NEW: DB-integrated routes