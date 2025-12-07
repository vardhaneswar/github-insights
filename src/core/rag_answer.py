# src/core/rag_answer.py

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from src.services.github_service import (
    extract_owner_repo,
    get_commits,
    get_pull_requests,
)
from src.core.vectorstore import query_similar
from src.core.metrics import commits_per_day, commits_per_week, top_contributors
from src.core.llm_client import generate_answer_from_llm


# ---------------------------------------------------------
# 1) TIME-WINDOW FILTER
# ---------------------------------------------------------

def _filter_commits_by_days(commits: List[Dict[str, Any]], days: int) -> List[Dict[str, Any]]:
    """Return only commits from the last N days."""
    if days is None:
        return commits

    now = datetime.now(timezone.utc)            # FIX: timezone-aware
    cutoff = now - timedelta(days=days)

    filtered = []
    for c in commits:
        date_str = (c.get("commit") or {}).get("author", {}).get("date")
        if not date_str:
            continue

        # Make commit timestamp timezone aware
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        if dt >= cutoff:
            filtered.append(c)

    return filtered


# ---------------------------------------------------------
# 2) METRICS BLOCK
# ---------------------------------------------------------

def _build_metrics_block(repo_url: str, time_window_days: int) -> Dict[str, Any]:
    """Compute commit statistics for the last N days."""
    commits = get_commits(repo_url)
    commits_recent = _filter_commits_by_days(commits, time_window_days)

    metrics = {
        "total_commits_recent": len(commits_recent),
        "commits_per_day": commits_per_day(commits_recent),
        "commits_per_week": commits_per_week(commits_recent),
        "top_contributors": top_contributors(commits_recent, limit=5),
    }
    return metrics


# ---------------------------------------------------------
# 3) RETRIEVAL CONTEXT
# ---------------------------------------------------------

def _build_context_snippets(repo_full_name: str, question: str, k: int = 15) -> List[str]:
    """Return retrieved commit/PR texts for the repo."""
    res = query_similar(repo_full_name, question, k)
    docs = res.get("documents") or [[]]
    return docs[0]       # Take only the first query


# ---------------------------------------------------------
# 4) MAIN RAG ANSWERING PIPELINE
# ---------------------------------------------------------

def answer_question(
    repo_url: str,
    question: str,
    time_window_days: int = 7,
    k: int = 15,
) -> Dict[str, Any]:
    """
    Steps:
    1. Resolve repo
    2. Compute metrics
    3. Retrieve context from vector DB
    4. Build a prompt
    5. Ask the LLM
    6. Return structured result
    """
    owner, repo = extract_owner_repo(repo_url)
    repo_full_name = f"{owner}/{repo}"

    # (1) Metrics
    metrics = _build_metrics_block(repo_url, time_window_days)

    # (2) Vector DB retrieval
    context_snippets = _build_context_snippets(repo_full_name, question, k=k)

    # Prepare context
    context_text = "\n\n---\n\n".join(context_snippets[:k])

    # Build metrics block text
    metrics_block = (
        f"- Total commits (last {time_window_days} days): {metrics['total_commits_recent']}\n"
        f"- Commits per day: {metrics['commits_per_day']}\n"
        f"- Commits per week: {metrics['commits_per_week']}\n"
        f"- Top contributors: {metrics['top_contributors']}\n"
    )

    # System prompt
    system_msg = (
        "You are an AI assistant analyzing GitHub repository activity.\n"
        "You are given commit texts, PR texts, and repo metrics.\n"
        "Base your answer ONLY on the information provided.\n"
        "If something is unclear or missing, say so.\n"
    )

    # User prompt
    user_prompt = f"""
Repository: {repo_full_name}

Question:
{question}

Time window: last {time_window_days} days

[METRICS]
{metrics_block}

[CONTEXT - COMMITS & PRs]
{context_text}

Using ONLY the context and metrics above, answer the question clearly.
If the question implies 'recent changes', focus on last {time_window_days} days.
"""

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_prompt},
    ]

    # (4) Ask the LLM
    answer_text = generate_answer_from_llm(messages)

    # (5) Final structured return
    return {
        "repo": repo_full_name,
        "question": question,
        "answer": answer_text,
        "metrics": metrics,
        "used_context": context_snippets[:k],
    }




def summarize_repo(
    repo_url: str,
    time_window_days: int = 7,
    k: int = 20
) -> Dict[str, Any]:

    owner, repo = extract_owner_repo(repo_url)
    repo_full_name = f"{owner}/{repo}"

    # 1) Metrics
    metrics = _build_metrics_block(repo_url, time_window_days)

    # 2) Semantic context (top commit/PR snippets)
    context_snippets = _build_context_snippets(repo_full_name, "recent activity", k=k)
    context_text = "\n\n---\n\n".join(context_snippets)

    # 3) Build summary prompt
    summary_prompt = f"""
You are an AI that summarizes GitHub repository activity for engineering managers.

Repository: {repo_full_name}
Time Window: last {time_window_days} days

[METRICS]
- Total commits: {metrics["total_commits_recent"]}
- Commits per day: {metrics["commits_per_day"]}
- Commits per week: {metrics["commits_per_week"]}
- Top contributors: {metrics["top_contributors"]}

[CONTEXT - COMMITS & PULL REQUESTS]
{context_text}

Write a short, clear **executive summary** including:
1. Main changes
2. Improvements or refactors
3. Notable discussions or PRs
4. Risks or important blockers
5. Momentum level (low / medium / high)

Keep it concise and factual. Do NOT invent data.
"""

    messages = [
        {"role": "system", "content": "You are a senior engineering analyst."},
        {"role": "user", "content": summary_prompt},
    ]

    # 4) LLM call
    summary_text = generate_answer_from_llm(messages)

    return {
        "status": "success",
        "repo": repo_full_name,
        "summary": summary_text,
        "metrics": metrics,
        "used_context": context_snippets[:k],
    }
