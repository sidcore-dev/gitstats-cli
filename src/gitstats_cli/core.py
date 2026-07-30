"""Core parsing and summarization logic for gitstats-cli.

This module is pure: it takes the text output of `git log` (produced
elsewhere) and turns it into summary statistics. It performs no I/O and
never shells out itself.
"""
from __future__ import annotations

import datetime
from collections import Counter
from dataclasses import dataclass, field

COMMIT_MARKER = "COMMIT"
FIELD_SEP = "\x1f"

#: Format string to pass to `git log --pretty=format:...`
LOG_FORMAT = f"{COMMIT_MARKER}{FIELD_SEP}%an{FIELD_SEP}%ad"

#: Weekday order used for the day-of-week breakdown, Monday first.
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass
class Commit:
    author: str
    date: str  # ISO date, YYYY-MM-DD
    files: list[str] = field(default_factory=list)


@dataclass
class GitStats:
    total_commits: int
    commits_per_author: list[tuple[str, int]]
    commits_per_weekday: list[tuple[str, int]]
    top_files: list[tuple[str, int]]


def day_of_week(iso_date: str) -> str:
    """Return the full weekday name for an ISO (YYYY-MM-DD) date string."""
    return datetime.date.fromisoformat(iso_date).strftime("%A")


def parse_git_log(log_text: str) -> list[Commit]:
    """Parse `git log --numstat --pretty=format:LOG_FORMAT` output.

    Each commit is introduced by a line ``COMMIT<sep>author<sep>date``,
    optionally followed by numstat lines (``added\\tdeleted\\tpath``) for
    the files that commit touched. Binary files (numstat shows ``-``) are
    still counted by path, just without add/delete counts.
    """
    commits: list[Commit] = []
    current: Commit | None = None

    for raw_line in log_text.splitlines():
        line = raw_line.rstrip("\n")
        if not line:
            continue
        if line.startswith(COMMIT_MARKER + FIELD_SEP):
            parts = line.split(FIELD_SEP)
            if len(parts) >= 3:
                author = parts[1]
                date = parts[2]
                current = Commit(author=author, date=date)
                commits.append(current)
            continue
        if current is not None and "\t" in line:
            fields = line.split("\t")
            if len(fields) >= 3:
                filename = "\t".join(fields[2:])
                current.files.append(filename)

    return commits


def summarize(commits: list[Commit], top_n: int = 10) -> GitStats:
    """Compute author, weekday, and top-file breakdowns for a set of commits."""
    author_counts = Counter(c.author for c in commits)
    weekday_counts = Counter(day_of_week(c.date) for c in commits)
    file_counts: Counter[str] = Counter()
    for c in commits:
        file_counts.update(c.files)

    commits_per_author = sorted(author_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    commits_per_weekday = [(day, weekday_counts.get(day, 0)) for day in WEEKDAYS]
    top_files = sorted(file_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]

    return GitStats(
        total_commits=len(commits),
        commits_per_author=commits_per_author,
        commits_per_weekday=commits_per_weekday,
        top_files=top_files,
    )
