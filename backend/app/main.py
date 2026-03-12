from fastapi import FastAPI
from app.routes.complaint_routes import router as complaint_router

app = FastAPI(title="Digital Democracy AI")

@app.get("/")
def health_check():
    return {"status": "running"}

app.include_router(complaint_router, prefix="/complaints")