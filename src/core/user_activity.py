# src/core/user_activity.py

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from src.services.github_service import (
    extract_owner_repo,
    get_commits,
    get_pull_requests,
    get_commit_details,   # <-- we'll add this in github_service.py
)
from src.core.llm_client import generate_answer_from_llm


def _parse_iso(dt_str: str) -> datetime | None:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def _filter_commits_for_user(
    commits: List[Dict[str, Any]],
    username: str,
    since: datetime,
) -> List[Dict[str, Any]]:
    username_l = username.lower()
    filtered: List[Dict[str, Any]] = []

    for c in commits:
        commit_obj = c.get("commit") or {}
        author_info = c.get("author") or {}
        commit_author = commit_obj.get("author") or {}

        login = (author_info.get("login") or "").lower()
        name = (commit_author.get("name") or "").lower()

        date_str = commit_author.get("date")
        dt = _parse_iso(date_str)
        if not dt or dt < since:
            continue

        if username_l and username_l not in {login, name}:
            continue

        filtered.append(c)

    return filtered


def _filter_prs_for_user(
    prs: List[Dict[str, Any]],
    username: str,
    since: datetime,
) -> List[Dict[str, Any]]:
    username_l = username.lower()
    result: List[Dict[str, Any]] = []

    for pr in prs:
        user = (pr.get("user") or {}).get("login") or ""
        if user.lower() != username_l:
            continue

        created_dt = _parse_iso(pr.get("created_at"))
        if not created_dt or created_dt < since:
            continue

        result.append(pr)

    return result


def _build_folder_stats(all_files: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    all_files = list of {"filename": ..., "additions": int, "deletions": int}
    We aggregate by top-level folder.
    """
    folders: Dict[str, int] = {}

    for f in all_files:
        path = f.get("filename") or ""
        if "/" in path:
            folder = path.split("/")[0]
        else:
            folder = "(root)"

        changes = int(f.get("additions", 0)) + int(f.get("deletions", 0))
        folders[folder] = folders.get(folder, 0) + changes

    return folders


def get_user_activity(
    repo_url: str,
    username: str,
    time_window_days: int = 1,
) -> Dict[str, Any]:
    """
    High-level pipeline:

    1) Pull commits & PRs from GitHub
    2) Filter by author + time window
    3) For commits, pull per-commit file + diff stats
    4) Aggregate folder stats
    5) Ask LLM to summarize what this person did
    """
    owner, repo = extract_owner_repo(repo_url)
    repo_full_name = f"{owner}/{repo}"

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=time_window_days)

    # 1) All commits for repo (we filter in Python)
    all_commits = get_commits(repo_url)
    commits_user = _filter_commits_for_user(all_commits, username, since)

    detailed_commits: List[Dict[str, Any]] = []
    all_files_flat: List[Dict[str, Any]] = []
    total_additions = 0
    total_deletions = 0

    for c in commits_user:
        sha = c.get("sha")
        commit_obj = c.get("commit") or {}
        commit_author = commit_obj.get("author") or {}
        date_str = commit_author.get("date")
        message = commit_obj.get("message") or ""

        # Pull full commit details (files + stats)
        if not sha:
            continue

        commit_details = get_commit_details(repo_url, sha)
        stats = commit_details.get("stats") or {}
        additions = int(stats.get("additions", 0))
        deletions = int(stats.get("deletions", 0))

        files = []
        for f in commit_details.get("files", []):
            file_info = {
                "filename": f.get("filename"),
                "status": f.get("status"),
                "additions": int(f.get("additions", 0)),
                "deletions": int(f.get("deletions", 0)),
            }
            files.append(file_info)
            all_files_flat.append(file_info)

        total_additions += additions
        total_deletions += deletions

        detailed_commits.append(
            {
                "sha": sha,
                "message": message,
                "date": date_str,
                "additions": additions,
                "deletions": deletions,
                "files": files,
            }
        )

    # 2) PRs created by this user
    all_prs = get_pull_requests(repo_url, state="all")
    prs_user = _filter_prs_for_user(all_prs, username, since)
    prs_clean = [
        {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "state": pr.get("state"),
            "created_at": pr.get("created_at"),
            "merged_at": pr.get("merged_at"),
        }
        for pr in prs_user
    ]

    # 3) Folder aggregation
    folders_touched = _build_folder_stats(all_files_flat)

    # 4) Build LLM summary
    # context: short bullets of commits & PRs
    commit_lines = []
    for dc in detailed_commits[:20]:  # cap for prompt size
        short_sha = (dc["sha"] or "")[:7]
        commit_lines.append(
            f"- [{short_sha}] {dc['message']} (files: {len(dc['files'])}, +{dc['additions']}/-{dc['deletions']})"
        )

    pr_lines = []
    for pr in prs_clean[:20]:
        pr_lines.append(
            f"- PR #{pr['number']} [{pr['state']}]: {pr['title']}"
        )

    context_text = (
        "Commits:\n" + "\n".join(commit_lines or ["(no commits)"]) + "\n\n"
        "Pull Requests:\n" + "\n".join(pr_lines or ["(no PRs)"])
    )

    system_msg = (
        "You are an assistant that summarizes the activity of a single developer "
        "in a GitHub repository.\n"
        "ONLY use the provided commits, PRs and stats.\n"
        "Be concise and focus on what this person actually did: features, fixes, refactors, "
        "folders they touched, and overall impact.\n"
    )

    user_prompt = f"""
Repository: {repo_full_name}
Developer: {username}
Time Window: last {time_window_days} days

[STATS]
- Commits: {len(detailed_commits)}
- PRs opened: {len(prs_clean)}
- Total additions: {total_additions}
- Total deletions: {total_deletions}
- Folders touched: {folders_touched}

[RAW ACTIVITY]
{context_text}

Write a short summary (3–6 bullet points) of what this developer worked on in this period.
"""

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_prompt},
    ]

    summary_text = generate_answer_from_llm(messages)

    return {
        "status": "success",
        "repo": repo_full_name,
        "user": username,
        "time_window_days": time_window_days,
        "summary": summary_text,
        "stats": {
            "commit_count": len(detailed_commits),
            "prs_opened": len(prs_clean),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "folders_touched": folders_touched,
        },
        "commits": detailed_commits,
        "pull_requests": prs_clean,
    }
