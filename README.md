# gitstats-cli

A small, dependency-free command-line tool that summarizes a git
repository's commit history: commits per author, commits per day of the
week, and the most-frequently-changed files.

## Why

`git log` has all this information buried in it, but reading it as a
scrollable wall of text doesn't answer questions like "who's committing
the most this quarter" or "which files keep changing" at a glance.
`gitstats-cli` shells out to `git log` and turns it into a short summary.

## Install

```bash
pip install .
```

This installs a `gitstats-cli` command on your PATH.

## Usage

Run it inside a git repository, or point it at one with `--repo`:

```bash
gitstats-cli --top 5
```

Example output:

```
Total commits: 42

Commits per author:
     30  Ann
     12  Bo

Commits per day of week:
      8  Monday
      6  Tuesday
      9  Wednesday
      5  Thursday
      7  Friday
      4  Saturday
      3  Sunday

Top 5 most-changed files:
     11  src/app.py
      7  README.md
      5  tests/test_app.py
      4  src/utils.py
      3  src/config.py
```

Bound the range with `--since` / `--until` (passed straight through to
`git log`, so anything `git log --since` accepts works):

```bash
gitstats-cli --since "2 weeks ago"
gitstats-cli --since 2026-01-01 --until 2026-06-30
```

### Options

| Flag        | Description                                              |
|-------------|-------------------------------------------------------------|
| `--repo`    | Path to the git repository (default: current directory)     |
| `--top`     | Number of top changed files to show (default: 10)           |
| `--since`   | Only include commits after this date (passed to `git log`)  |
| `--until`   | Only include commits before this date (passed to `git log`) |
| `--json`    | Emit machine-readable JSON instead of text                  |

### Exit codes

- `0` — summary printed successfully
- `2` — `git` isn't available on PATH, or `--repo` isn't a git repository

## Development

```bash
pip install -e .
python -m unittest discover -s tests -v
```

## License

All rights reserved. This code is public for viewing and reference only —
no license is granted to use, copy, modify, or redistribute it. See
[LICENSE](LICENSE) for details.
