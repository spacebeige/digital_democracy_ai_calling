from fastapi import APIRouter
from app.services.llm_service import process_query

router = APIRouter()

@router.post("/")
def create_complaint(query: str):
    result = process_query(query)
    return {
        "message": "Complaint processed",
        "response": result
    }