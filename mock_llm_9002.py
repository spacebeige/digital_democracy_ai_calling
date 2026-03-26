from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Mock LLM 9002")


class QueryRequest(BaseModel):
    query: str


@app.get("/")
def health():
    return {"status": "healthy", "service": "llm"}


@app.post("/generate")
def generate(payload: QueryRequest):
    return {
        "response_text": f"Grievance recorded: {payload.query}",
        "department": "Water & Sewerage",
        "status": "success",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9002)
