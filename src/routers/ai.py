# src/routers/ai.py

from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

from src.core.rag_answer import answer_question, summarize_repo
from src.core.user_activity import get_user_activity


router = APIRouter(tags=["AI"])


# ---------------------------
# REQUEST MODELS
# ---------------------------

class AIQueryRequest(BaseModel):
    url: HttpUrl
    question: str


class AISummaryRequest(BaseModel):
    url: HttpUrl
    time_window_days: int = 7     # unified naming


class UserActivityRequest(BaseModel):
    url: HttpUrl
    user: str
    time_window_days: int = 1     # default: "today"


# ---------------------------
# ENDPOINT: Free-form AI Query
# ---------------------------

@router.post("/query")
def query_ai(req: AIQueryRequest):
    """
    Universal natural-language GitHub RAG question.
    Example:
    {
        "url": "https://github.com/karpathy/nanoGPT",
        "question": "Who worked on this repo yesterday?"
    }
    """
    result = answer_question(
        repo_url=str(req.url),
        question=req.question,
    )
    return {"status": "success", "data": result}


# ---------------------------
# ENDPOINT: Executive Summary
# ---------------------------

@router.post("/summary")
def summarize_repo_api(req: AISummaryRequest):
    """
    Summarizes recent repository activity for managers.
    """
    result = summarize_repo(
        repo_url=str(req.url),
        time_window_days=req.time_window_days,
    )
    return {"status": "success", "data": result}


# ---------------------------
# ENDPOINT: User Activity (Dev-level summary)
# ---------------------------

@router.post("/user-activity")
def user_activity_api(req: UserActivityRequest):
    """
    Returns commit/PR/file/folder activity for a specific developer.
    Example:
    {
        "url": "https://github.com/karpathy/nanoGPT",
        "user": "karpathy",
        "time_window_days": 7
    }
    """
    result = get_user_activity(
        repo_url=str(req.url),
        username=req.user,
        time_window_days=req.time_window_days,
    )
    return {"status": "success", "data": result}
