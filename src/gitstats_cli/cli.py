"""Command-line entry point for gitstats-cli."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

from .core import LOG_FORMAT, GitStats, parse_git_log, summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitstats-cli",
        description="Summarize a git repository's commit history: commits per author, "
        "commits per day-of-week, and the most-frequently-changed files.",
    )
    parser.add_argument("--repo", default=".", help="Path to the git repository (default: current directory)")
    parser.add_argument("--top", type=int, default=10, help="Number of top changed files to show (default: 10)")
    parser.add_argument("--since", default=None, help="Only include commits after this date (passed to git log)")
    parser.add_argument("--until", default=None, help="Only include commits before this date (passed to git log)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    return parser


def _check_git_available() -> str | None:
    return shutil.which("git")


def _check_is_repo(repo: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def _run_git_log(repo: str, since: str | None, until: str | None) -> str:
    cmd = ["git", "-C", repo, "log", "--numstat", f"--pretty=format:{LOG_FORMAT}", "--date=format:%Y-%m-%d"]
    if since:
        cmd.append(f"--since={since}")
    if until:
        cmd.append(f"--until={until}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def _print_human(stats: GitStats, top_n: int) -> None:
    print(f"Total commits: {stats.total_commits}")
    print()
    print("Commits per author:")
    for author, count in stats.commits_per_author:
        print(f"  {count:>5}  {author}")
    print()
    print("Commits per day of week:")
    for day, count in stats.commits_per_weekday:
        print(f"  {count:>5}  {day}")
    print()
    print(f"Top {top_n} most-changed files:")
    if not stats.top_files:
        print("  (no file changes found)")
    for path, count in stats.top_files:
        print(f"  {count:>5}  {path}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if _check_git_available() is None:
        print("gitstats-cli: error: git executable not found on PATH", file=sys.stderr)
        return 2

    if not _check_is_repo(args.repo):
        print(f"gitstats-cli: error: '{args.repo}' is not a git repository", file=sys.stderr)
        return 2

    try:
        log_text = _run_git_log(args.repo, args.since, args.until)
    except subprocess.CalledProcessError as exc:
        print(f"gitstats-cli: error: git log failed: {exc.stderr.strip()}", file=sys.stderr)
        return 2

    commits = parse_git_log(log_text)
    stats = summarize(commits, top_n=args.top)

    if args.json:
        print(
            json.dumps(
                {
                    "total_commits": stats.total_commits,
                    "commits_per_author": stats.commits_per_author,
                    "commits_per_weekday": stats.commits_per_weekday,
                    "top_files": stats.top_files,
                },
                indent=2,
            )
        )
    else:
        _print_human(stats, args.top)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
