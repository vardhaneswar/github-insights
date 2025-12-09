import re
import os
import requests
from typing import Dict, Any, List, Optional
from src.core.cache import load_cache, save_cache

# ---------------------------------------------------------
# GLOBAL CONFIG
# ---------------------------------------------------------

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-insights-app"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
else:
    print("⚠️ WARNING: GitHub token not loaded. Rate limits will be low!")

GITHUB_API_BASE = "https://api.github.com"


# ---------------------------------------------------------
# HELPER
# ---------------------------------------------------------

def extract_owner_repo(repo_url: str):
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, repo_url)
    if not match:
        raise ValueError("Invalid GitHub URL format")
    return match.group(1), match.group(2)


# ---------------------------------------------------------
# REPO INFO
# ---------------------------------------------------------

def get_repo_info(repo_url: str) -> Dict[str, Any]:
    owner, repo = extract_owner_repo(repo_url)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    resp = requests.get(url, headers=HEADERS)

    if not resp.ok:
        raise Exception(f"GitHub API Error {resp.status_code}: {resp.text}")

    return resp.json()


# ---------------------------------------------------------
# COMMITS (with caching)
# ---------------------------------------------------------

def get_commits(repo_url: str, per_page: int = 100):
    owner, repo = extract_owner_repo(repo_url)
    cache_key = f"{owner}_{repo}_commits"

    # 1️⃣ Try cache
    cached = load_cache(cache_key, "commits")
    if cached:
        return cached

    # 2️⃣ Fresh GitHub call
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"

    commits = []
    page = 1

    while True:
        params = {"page": page, "per_page": per_page}
        resp = requests.get(url, headers=HEADERS, params=params)

        if not resp.ok:
            raise Exception(f"GitHub API Error {resp.status_code}: {resp.text}")

        data = resp.json()
        if not data:
            break

        commits.extend(data)
        page += 1

    # 3️⃣ Save cache
    save_cache(cache_key, "commits", commits)
    return commits


def get_commit_details(repo_url: str, sha: str):
    owner, repo = extract_owner_repo(repo_url)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{sha}"

    resp = requests.get(url, headers=HEADERS)

    if not resp.ok:
        raise Exception(f"GitHub API Error {resp.status_code}: {resp.text}")

    return resp.json()


# ---------------------------------------------------------
# PULL REQUESTS (with caching)
# ---------------------------------------------------------

def get_pull_requests(repo_url: str, state: str = "all", per_page: int = 100):
    owner, repo = extract_owner_repo(repo_url)
    cache_key = f"{owner}_{repo}_prs"

    cached = load_cache(cache_key, "prs")
    if cached:
        return cached

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"

    prs = []
    page = 1

    while True:
        params = {"state": state, "page": page, "per_page": per_page}
        resp = requests.get(url, headers=HEADERS, params=params)

        if not resp.ok:
            raise Exception(f"GitHub API Error {resp.status_code}: {resp.text}")

        data = resp.json()
        if not data:
            break

        prs.extend(data)
        page += 1

    save_cache(cache_key, "prs", prs)
    return prs


# ---------------------------------------------------------
# CONTRIBUTORS (with caching)
# ---------------------------------------------------------

def get_contributors(repo_url: str):
    owner, repo = extract_owner_repo(repo_url)
    cache_key = f"{owner}_{repo}_contributors"

    cached = load_cache(cache_key, "contributors")
    if cached:
        return cached

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors"
    resp = requests.get(url, headers=HEADERS)

    if not resp.ok:
        raise Exception(f"GitHub API Error {resp.status_code}: {resp.text}")

    contributors = resp.json()

    save_cache(cache_key, "contributors", contributors)
    return contributors


# ---------------------------------------------------------
# BRANCHES
# ---------------------------------------------------------

def get_branches(repo_url: str):
    owner, repo = extract_owner_repo(repo_url)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches"

    resp = requests.get(url, headers=HEADERS)

    if not resp.ok:
        raise Exception(f"GitHub API Error {resp.status_code}: {resp.text}")

    return resp.json()
