from fastapi import APIRouter, HTTPException, Query
from src.services.github_service import (
    get_repo_info,
    get_commits,
    get_pull_requests,
    get_contributors,
    get_branches
)

router = APIRouter()

# Default repo (fallback)
DEFAULT_REPO = "https://github.com/vardhaneswar/Image-classification"


def resolve_repo(url: str | None):
    """Return URL if provided, else default repo."""
    return url if url else DEFAULT_REPO


# -------------------------
#   REPO INFO
# -------------------------
@router.get("/info")
def repo_info(url: str = Query(None)):
    try:
        repo = resolve_repo(url)
        return get_repo_info(repo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------
#   COMMITS
# -------------------------
@router.get("/commits")
def repo_commits(url: str = Query(None)):
    try:
        repo = resolve_repo(url)
        return get_commits(repo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------
#   PULL REQUESTS
# -------------------------
@router.get("/pulls")
def repo_pull_requests(url: str = Query(None), state: str = "all"):
    try:
        repo = resolve_repo(url)
        return get_pull_requests(repo, state=state)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------
#   CONTRIBUTORS
# -------------------------
@router.get("/contributors")
def repo_contributors(url: str = Query(None)):
    try:
        repo = resolve_repo(url)
        return get_contributors(repo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------
#   BRANCHES
# -------------------------
@router.get("/branches")
def repo_branches(url: str = Query(None)):
    try:
        repo = resolve_repo(url)
        return get_branches(repo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
