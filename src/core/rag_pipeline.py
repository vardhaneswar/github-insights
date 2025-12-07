from typing import List, Dict, Any, Tuple

from src.services.github_service import (
    extract_owner_repo,
    get_commits,
    get_pull_requests,
)
from src.core.vectorstore import upsert_documents


# --------- Helpers to build RAG documents --------- #

def _build_commit_docs(commits: List[Dict[str, Any]], repo_full_name: str
                       ) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """
    Turn GitHub commits into ids, texts, metadatas for the vector store.
    """
    ids: List[str] = []
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for c in commits:
        sha = c.get("sha")
        commit_info = c.get("commit", {}) or {}
        author_info = commit_info.get("author", {}) or {}

        message = commit_info.get("message", "") or ""
        author_name = author_info.get("name") or "Unknown"
        date = author_info.get("date")
        html_url = c.get("html_url")

        # Text that will be embedded
        text = f"[COMMIT] {author_name} on {date}:\n{message}"

        metadata = {
            "repo": repo_full_name,
            "type": "commit",
            "sha": sha,
            "author": author_name,
            "date": date,
            "url": html_url,
        }

        doc_id = f"commit:{repo_full_name}:{sha}"

        ids.append(doc_id)
        texts.append(text)
        metadatas.append(metadata)

    return ids, texts, metadatas


def _build_pr_docs(prs: List[Dict[str, Any]], repo_full_name: str
                   ) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """
    Turn GitHub pull requests into ids, texts, metadatas for the vector store.
    """
    ids: List[str] = []
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for pr in prs:
        number = pr.get("number")
        title = pr.get("title") or ""
        body = pr.get("body") or ""
        user = (pr.get("user") or {}).get("login") or "Unknown"
        state = pr.get("state")
        created_at = pr.get("created_at")
        merged_at = pr.get("merged_at")
        closed_at = pr.get("closed_at")
        html_url = pr.get("html_url")

        # Truncate huge bodies a bit to keep things reasonable
        if len(body) > 2000:
            body = body[:2000] + "\n...[truncated]"

        text = f"[PR #{number}] {title}\n\nAuthor: {user}\nState: {state}\n\n{body}"

        metadata = {
            "repo": repo_full_name,
            "type": "pr",
            "number": number,
            "author": user,
            "state": state,
            "created_at": created_at,
            "merged_at": merged_at,
            "closed_at": closed_at,
            "url": html_url,
        }

        doc_id = f"pr:{repo_full_name}:{number}"

        ids.append(doc_id)
        texts.append(text)
        metadatas.append(metadata)

    return ids, texts, metadatas


# --------- Public pipeline: index repo activity --------- #

def index_repo_activity(repo_url: str,
                        max_commits: int = 200,
                        max_prs: int = 100) -> Dict[str, int]:
    """
    Fetch commits + PRs from GitHub for a repo and index them into Chroma.

    repo_url: e.g. "https://github.com/karpathy/nanoGPT"

    Returns a small summary: how many commits and PR docs were indexed.
    """
    owner, repo = extract_owner_repo(repo_url)
    repo_full_name = f"{owner}/{repo}"

    # 1) Fetch data from GitHub
    commits = get_commits(repo_url)
    prs = get_pull_requests(repo_url, state="all")

    # Optionally limit to a max number so we don't index thousands at once
    if max_commits is not None:
        commits = commits[:max_commits]
    if max_prs is not None:
        prs = prs[:max_prs]

    # 2) Build commit docs
    commit_ids, commit_texts, commit_metadatas = _build_commit_docs(
        commits, repo_full_name
    )

    # 3) Build PR docs
    pr_ids, pr_texts, pr_metadatas = _build_pr_docs(
        prs, repo_full_name
    )

    # 4) Upsert into vector store
    if commit_ids:
        upsert_documents(commit_ids, commit_texts, commit_metadatas)

    if pr_ids:
        upsert_documents(pr_ids, pr_texts, pr_metadatas)

    return {
        "commits_indexed": len(commit_ids),
        "prs_indexed": len(pr_ids),
    }
