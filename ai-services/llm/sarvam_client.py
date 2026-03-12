from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import sys

RAG_PATH = Path(__file__).resolve().parents[2] / "rag-engine"
if str(RAG_PATH) not in sys.path:
    sys.path.append(str(RAG_PATH))

try:
    from retrieval import retrieve_context
    RAG_ENABLED = True
except Exception:
    RAG_ENABLED = False

    def retrieve_context(query: str, k: int = 3) -> dict:
        return {
            "documents": [],
            "message": "rag_unavailable",
        }

app = FastAPI(title="LLM Service")


class GenerateRequest(BaseModel):
    query: str


def detect_department(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["water", "sewer", "drain", "pipeline"]):
        return "water"
    if any(word in lowered for word in ["road", "pothole", "street", "traffic"]):
        return "roads"
    if any(word in lowered for word in ["garbage", "waste", "clean", "sanitation"]):
        return "sanitation"
    if any(word in lowered for word in ["electric", "power", "light"]):
        return "electricity"
    return "general"


@app.post("/generate")
def generate(payload: GenerateRequest):
    query = payload.query.strip()
    department = detect_department(query)
    context_result = retrieve_context(query)
    docs = context_result.get("documents", [])

    context_snippets = [doc.get("text", "") for doc in docs[:2] if doc.get("text")]
    context_text = " ".join(context_snippets)

    if context_text:
        response_text = (
            "Thank you for reporting this issue. "
            f"I have categorized it under {department}. "
            f"Based on guidance: {context_text} "
            "Your complaint has been registered and forwarded to the relevant department."
        )
    else:
        response_text = (
            "Thank you for reporting this issue. "
            f"I have categorized it under {department}. "
            "Your complaint has been registered and forwarded to the relevant department."
        )

    return {
        "response_text": response_text,
        "department": department,
        "priority": "medium",
        "rag": {
            "enabled": RAG_ENABLED,
            "status": context_result.get("message"),
            "sources": docs,
        },
    }
