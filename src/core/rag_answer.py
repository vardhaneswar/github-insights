# src/core/rag_answer.py

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from src.services.github_service import (
    extract_owner_repo,
    get_commits,
)
from src.core.vectorstore import query_similar
from src.core.metrics import commits_per_day, commits_per_week, top_contributors
from src.core.llm_client import generate_answer_from_llm


# ---------------------------------------------------------
# 1) FILTER COMMITS BY DAYS
# ---------------------------------------------------------

def _filter_commits_by_days(commits: List[Dict[str, Any]], days: int | None) -> List[Dict[str, Any]]:
    """Return only commits from last N days. If days=None → no filtering."""
    if days is None:
        return commits

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    filtered = []
    for c in commits:
        date_str = (c.get("commit") or {}).get("author", {}).get("date")
        if not date_str:
            continue

        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt >= cutoff:
            filtered.append(c)

    return filtered


# ---------------------------------------------------------
# 2) METRICS BLOCK
# ---------------------------------------------------------

def _build_metrics_block(repo_url: str, time_window_days: int | None) -> Dict[str, Any]:
    """Compute commit statistics for the given time window."""
    commits = get_commits(repo_url)
    commits_recent = _filter_commits_by_days(commits, time_window_days)

    return {
        "total_commits_recent": len(commits_recent),
        "commits_per_day": commits_per_day(commits_recent),
        "commits_per_week": commits_per_week(commits_recent),
        "top_contributors": top_contributors(commits_recent, limit=5),
    }


# ---------------------------------------------------------
# 3) EMBEDDING RETRIEVAL CONTEXT
# ---------------------------------------------------------

def _build_context_snippets(repo_full_name: str, question: str, k: int = 15) -> List[str]:
    res = query_similar(repo_full_name, question, k)
    docs = res.get("documents") or [[]]
    return docs[0]


# ---------------------------------------------------------
# 4) AUTOMATIC TIME WINDOW DETECTION
# ---------------------------------------------------------

def infer_time_window(question: str) -> int | None:
    """Infer a proper time window from natural language."""
    q = question.lower()

    if "today" in q:
        return 1
    if "yesterday" in q:
        return 2

    if "this week" in q or "past week" in q or "last week" in q:
        return 7
    if "recent" in q or "recently" in q:
        return 7

    if "this month" in q or "last month" in q or "past month" in q:
        return 30

    if "this year" in q or "last year" in q or "past year" in q:
        return 365

    if any(k in q for k in ["why", "how", "architecture", "tokenizer", "design", "model"]):
        return None  # semantic question → full history

    return 30


# ---------------------------------------------------------
# 5) MAIN RAG ANSWERING PIPELINE
# ---------------------------------------------------------

def answer_question(
    repo_url: str,
    question: str,
    k: int = 15,
) -> Dict[str, Any]:

    owner, repo = extract_owner_repo(repo_url)
    repo_full_name = f"{owner}/{repo}"

    # (A) detect time window automatically
    time_window_days = infer_time_window(question)

    # (B) compute metrics
    metrics = _build_metrics_block(repo_url, time_window_days)

    # (C) return early if no commits exist
    if metrics["total_commits_recent"] == 0:
        return {
            "repo": repo_full_name,
            "question": question,
            "time_window_used": time_window_days,
            "answer": "No activity in this period.",
            "metrics": metrics,
            "used_context": [],
        }

    # (D) semantic retrieval
    context_snippets = _build_context_snippets(repo_full_name, question, k=k)
    context_text = "\n\n---\n\n".join(context_snippets[:k])

    metrics_block = (
        f"- Time Window: {time_window_days if time_window_days else 'full history'}\n"
        f"- Total commits: {metrics['total_commits_recent']}\n"
        f"- Commits per day: {metrics['commits_per_day']}\n"
        f"- Commits per week: {metrics['commits_per_week']}\n"
        f"- Top contributors: {metrics['top_contributors']}\n"
    )

    # strict hallucination-preventing system prompt
    system_msg = (
        "You are an AI assistant that analyzes GitHub activity.\n"
        "RULES:\n"
        "- The time window filter is already applied before you see data.\n"
        "- NEVER mention dates, timestamps, or missing date information.\n"
        "- NEVER say you need the current date.\n"
        "- ONLY describe what happened based on the commits provided.\n"
        "- NEVER talk about contributors not present in this filtered data.\n"
        "- NEVER use old data outside the time window.\n"
        "- If there are no commits → you will NEVER be called. Python handles that.\n"
        "- Be short, factual, confident.\n"
        "- ZERO hallucinations. Use ONLY context and metrics.\n"
    )

    user_prompt = f"""
Repository: {repo_full_name}

Question:
{question}

[METRICS]
{metrics_block}

[CONTEXT - COMMITS & PRs]
{context_text}

Provide a short factual answer ONLY using the above information.
Do NOT mention dates, time, or missing data.
"""

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_prompt},
    ]

    answer_text = generate_answer_from_llm(messages)

    return {
        "repo": repo_full_name,
        "question": question,
        "time_window_used": time_window_days,
        "answer": answer_text,
        "metrics": metrics,
        "used_context": context_snippets[:k],
    }


# ---------------------------------------------------------
# 6) SUMMARY ENDPOINT
# ---------------------------------------------------------

def summarize_repo(
    repo_url: str,
    time_window_days: int = 7,
    k: int = 20
) -> Dict[str, Any]:

    owner, repo = extract_owner_repo(repo_url)
    repo_full_name = f"{owner}/{repo}"

    metrics = _build_metrics_block(repo_url, time_window_days)
    context_snippets = _build_context_snippets(repo_full_name, "recent activity", k=k)
    context_text = "\n\n---\n\n".join(context_snippets)

    summary_prompt = f"""
You are an AI summarizing GitHub repository activity.

Repository: {repo_full_name}
Time Window: last {time_window_days} days

[METRICS]
- Total commits: {metrics["total_commits_recent"]}
- Commits per day: {metrics["commits_per_day"]}
- Commits per week: {metrics["commits_per_week"]}
- Top contributors: {metrics["top_contributors"]}

[CONTEXT]
{context_text}

Write a concise executive summary including:
1. Main changes
2. Improvements / refactors
3. Notable PRs
4. Risks / blockers
5. Momentum (low / medium / high)

Do NOT hallucinate. Use only given data.
"""

    messages = [
        {"role": "system", "content": "You are a senior engineering analyst."},
        {"role": "user", "content": summary_prompt},
    ]

    summary_text = generate_answer_from_llm(messages)

    return {
        "status": "success",
        "repo": repo_full_name,
        "summary": summary_text,
        "metrics": metrics,
        "used_context": context_snippets[:k],
    }
