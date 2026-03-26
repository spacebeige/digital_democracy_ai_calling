from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.routes.call_routes import router as call_router
from app.routes.complaint_routes import router as complaint_router
from app.routes.router_routes import router as router_router
from app.routes.analysis_routes import router as analysis_router
from app.routes.sms_routes import router as sms_router
from app.config import QR_IMAGE_DIR

app = FastAPI(title="Digital Democracy AI")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {"status": "running"}

app.include_router(complaint_router, prefix="/complaints")
app.include_router(call_router, prefix="/calls")
app.include_router(router_router)
app.include_router(analysis_router)
app.include_router(sms_router, prefix="/sms")

QR_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/public/qr", StaticFiles(directory=str(QR_IMAGE_DIR)), name="qr_public")