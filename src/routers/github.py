from fastapi import APIRouter, HTTPException, Query
from src.services.github_service import get_repo_info
from src.services.github_service import get_repo_info, get_commits
from src.services.github_service import get_pull_requests
from src.services.github_service import get_contributors
from src.services.github_service import get_branches

router = APIRouter()

@router.get("/info")
def repo_info(url: str = Query(..., description="GitHub repository URL")):
    try:
        data = get_repo_info(url)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/commits")
def repo_commits(url: str):
    try:
        commits = get_commits(url)
        return {"status": "success", "count": len(commits), "data": commits}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


@router.get("/pulls")
def repo_pull_requests(url: str, state: str = "all"):
    try:
        prs = get_pull_requests(url, state=state)
        return {"status": "success", "count": len(prs), "data": prs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contributors")
def repo_contributors(url: str):
    try:
        contributors = get_contributors(url)
        return {"status": "success", "count": len(contributors), "data": contributors}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

    

@router.get("/branches")
def repo_branches(url: str):
    try:
        branches = get_branches(url)
        return {"status": "success", "count": len(branches), "data": branches}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
