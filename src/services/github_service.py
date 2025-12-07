import re
import requests

GITHUB_API_BASE = "https://api.github.com"


def extract_owner_repo(repo_url: str):
    """
    Extracts the owner and repo name from a GitHub URL.
    Example: https://github.com/karpathy/nanoGPT → ('karpathy', 'nanoGPT')
    """
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, repo_url)

    if not match:
        raise ValueError("Invalid GitHub URL format")

    owner, repo = match.group(1), match.group(2)
    return owner, repo


def get_repo_info(repo_url: str, token: str = None):
    """
    Fetch basic repository info from GitHub API.
    """
    owner, repo = extract_owner_repo(repo_url)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHub-Insights-AI"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

    return response.json()




def get_commits(repo_url: str, token: str = None, per_page: int = 100):
    """
    Fetch commits for a repository.
    GitHub returns results paginated (100 commits per page max).
    """
    owner, repo = extract_owner_repo(repo_url)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHub-Insights-AI"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    commits = []
    page = 1

    while True:
        params = {"page": page, "per_page": per_page}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

        data = response.json()

        if not data:
            break  # No more pages

        commits.extend(data)
        page += 1

    return commits



def get_pull_requests(repo_url: str, state: str = "all", token: str = None, per_page: int = 100):
    """
    Fetch pull requests (open, closed, or all).
    state options: "open", "closed", "all"
    """
    owner, repo = extract_owner_repo(repo_url)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHub-Insights-AI"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "state": state,
        "per_page": per_page
    }

    pull_requests = []
    page = 1

    while True:
        params["page"] = page
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

        data = response.json()

        if not data:
            break

        pull_requests.extend(data)
        page += 1

    return pull_requests




def get_contributors(repo_url: str, token: str = None):
    """
    Fetch contributors for a repository.
    Includes commit count, additions, deletions for each contributor.
    """
    owner, repo = extract_owner_repo(repo_url)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHub-Insights-AI"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

    return response.json()



def get_branches(repo_url: str, token: str = None):
    """
    Fetches all branches of a repository.
    Provides branch names + last commit info.
    """
    owner, repo = extract_owner_repo(repo_url)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHub-Insights-AI"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub API Error {response.status_code}: {response.text}")

    return response.json()
