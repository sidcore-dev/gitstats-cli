import unittest

from gitstats_cli.core import day_of_week, parse_git_log, summarize

SEP = "\x1f"


def _commit_line(author: str, date: str) -> str:
    return f"COMMIT{SEP}{author}{SEP}{date}"


class TestDayOfWeek(unittest.TestCase):
    def test_known_monday(self) -> None:
        self.assertEqual(day_of_week("2026-07-27"), "Monday")

    def test_known_sunday(self) -> None:
        self.assertEqual(day_of_week("2026-08-02"), "Sunday")


class TestParseGitLog(unittest.TestCase):
    def test_parses_single_commit_with_files(self) -> None:
        log = "\n".join(
            [
                _commit_line("Ann", "2026-07-27"),
                "3\t1\tfile_a.py",
                "0\t0\tfile_b.py",
                "",
            ]
        )
        commits = parse_git_log(log)
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].author, "Ann")
        self.assertEqual(commits[0].date, "2026-07-27")
        self.assertEqual(commits[0].files, ["file_a.py", "file_b.py"])

    def test_parses_multiple_commits(self) -> None:
        log = "\n".join(
            [
                _commit_line("Ann", "2026-07-27"),
                "1\t0\tfile_a.py",
                "",
                _commit_line("Bo", "2026-07-28"),
                "2\t0\tfile_a.py",
                "",
            ]
        )
        commits = parse_git_log(log)
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[1].author, "Bo")

    def test_handles_binary_file_marker(self) -> None:
        log = "\n".join([_commit_line("Ann", "2026-07-27"), "-\t-\timage.png", ""])
        commits = parse_git_log(log)
        self.assertEqual(commits[0].files, ["image.png"])

    def test_empty_log_returns_no_commits(self) -> None:
        self.assertEqual(parse_git_log(""), [])


class TestSummarize(unittest.TestCase):
    def test_commits_per_author_sorted_desc(self) -> None:
        log = "\n".join(
            [
                _commit_line("Ann", "2026-07-27"),
                "",
                _commit_line("Ann", "2026-07-28"),
                "",
                _commit_line("Bo", "2026-07-29"),
                "",
            ]
        )
        commits = parse_git_log(log)
        stats = summarize(commits)
        self.assertEqual(stats.total_commits, 3)
        self.assertEqual(stats.commits_per_author[0], ("Ann", 2))
        self.assertEqual(stats.commits_per_author[1], ("Bo", 1))

    def test_commits_per_weekday_includes_all_days(self) -> None:
        commits = parse_git_log(_commit_line("Ann", "2026-07-27") + "\n")
        stats = summarize(commits)
        days = [d for d, _ in stats.commits_per_weekday]
        self.assertEqual(
            days,
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        )
        counts = dict(stats.commits_per_weekday)
        self.assertEqual(counts["Monday"], 1)

    def test_top_files_respects_top_n(self) -> None:
        log = "\n".join(
            [
                _commit_line("Ann", "2026-07-27"),
                "1\t0\ta.py",
                "1\t0\tb.py",
                "1\t0\tc.py",
                "",
            ]
        )
        commits = parse_git_log(log)
        stats = summarize(commits, top_n=2)
        self.assertEqual(len(stats.top_files), 2)

    def test_top_files_counts_frequency(self) -> None:
        log = "\n".join(
            [
                _commit_line("Ann", "2026-07-27"),
                "1\t0\ta.py",
                "",
                _commit_line("Bo", "2026-07-28"),
                "1\t0\ta.py",
                "1\t0\tb.py",
                "",
            ]
        )
        commits = parse_git_log(log)
        stats = summarize(commits)
        self.assertEqual(stats.top_files[0], ("a.py", 2))


if __name__ == "__main__":
    unittest.main()
