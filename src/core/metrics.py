from collections import defaultdict
from datetime import datetime


def commits_per_day(commits):
    """
    Computes number of commits per day.
    Input: list of commit objects from GitHub API
    Output: dict {"2024-01-01": 5, "2024-01-02": 12, ...}
    """

    daily_counts = defaultdict(int)

    for c in commits:
        date_str = c["commit"]["author"]["date"]  # example: "2025-01-28T19:52:34Z"
        date_only = date_str.split("T")[0]
        daily_counts[date_only] += 1

    return dict(sorted(daily_counts.items()))



def commits_per_week(commits):
    """
    Computes number of commits per ISO week.
    Output example:
    { "2024-W45": 12, "2024-W46": 30, ... }
    """
    weekly_counts = defaultdict(int)

    for c in commits:
        date_str = c["commit"]["author"]["date"]   # "2025-01-20T17:30:45Z"
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        year, week, _ = dt.isocalendar()  # returns (year, week_number, weekday)

        key = f"{year}-W{week}"
        weekly_counts[key] += 1

    # Sort by week
    return dict(sorted(weekly_counts.items()))



def top_contributors(commits, limit=10):
    """
    Returns top contributors based on number of commits.
    Example output:
    [
        {"author": "karpathy", "commits": 120},
        {"author": "alice", "commits": 45},
        ...
    ]
    """
    counts = defaultdict(int)

    for c in commits:
        author = c["commit"]["author"]["name"] or "Unknown"
        counts[author] += 1

    # Convert and sort by commit count (descending)
    sorted_contributors = sorted(
        [{"author": a, "commits": cnt} for a, cnt in counts.items()],
        key=lambda x: x["commits"],
        reverse=True
    )

    return sorted_contributors[:limit]
