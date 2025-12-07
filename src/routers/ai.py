# src/routers/ai.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.core.rag_answer import summarize_repo


from src.core.rag_answer import answer_question

router = APIRouter()


class AIQueryRequest(BaseModel):
    url: str
    question: str
    time_window_days: int = 7


@router.post("/query")
def ai_query(req: AIQueryRequest):
    try:
        result = answer_question(
            repo_url=req.url,
            question=req.question,
            time_window_days=req.time_window_days,
        )
        return {"status": "success", "data": result}
    except NotImplementedError as e:
        # llm_client not wired yet
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AISummaryRequest(BaseModel):
    url: str
    time_window_days: int = 7


@router.post("/api/ai/summary")
def summarize_repo_api(req: AISummaryRequest):
    summary = summarize_repo(
        repo_url=req.url,
        time_window_days=req.time_window_days
    )
    return summary
