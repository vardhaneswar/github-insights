from fastapi import APIRouter, HTTPException
from src.services.github_service import get_commits
from src.core.metrics import commits_per_day, commits_per_week, top_contributors

router = APIRouter()

@router.get("/activity/daily")
def daily_commit_activity(url: str):
    try:
        commits = get_commits(url)
        data = commits_per_day(commits)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/activity/weekly")
def weekly_commit_activity(url: str):
    try:
        commits = get_commits(url)
        data = commits_per_week(commits)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contributors/top")
def top_contributors_api(url: str, limit: int = 10):
    try:
        commits = get_commits(url)
        data = top_contributors(commits, limit)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
