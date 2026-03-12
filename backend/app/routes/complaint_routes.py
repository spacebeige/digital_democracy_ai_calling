from fastapi import APIRouter
from app.services.llm_service import process_query
from app.schemas import ComplaintQueryRequest, ComplaintQueryResponse

router = APIRouter()

@router.post("/")
def create_complaint(payload: ComplaintQueryRequest) -> ComplaintQueryResponse:
    result = process_query(payload.query)
    return {
        "message": "Complaint processed",
        "response": result
    }