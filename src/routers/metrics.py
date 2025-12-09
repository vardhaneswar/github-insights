from fastapi import APIRouter, HTTPException
from src.services.github_service import get_commits
from src.core.metrics import commits_per_day, commits_per_week, top_contributors

router = APIRouter()

DEFAULT_REPO = "https://github.com/vardhaneswar/Image-classification"

@router.get("/activity/daily")
def daily_commit_activity():
    try:
        commits = get_commits(DEFAULT_REPO)
        return commits_per_day(commits)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/activity/weekly")
def weekly_commit_activity():
    try:
        commits = get_commits(DEFAULT_REPO)
        return commits_per_week(commits)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contributors/top")
def top_contributors_api(limit: int = 10):
    try:
        commits = get_commits(DEFAULT_REPO)
        return top_contributors(commits, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
