import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from gitstats_cli.cli import main


def _run(cmd: list[str], cwd: str) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _make_repo(tmp: str) -> None:
    _run(["git", "init", "-q", "-b", "main"], tmp)
    _run(["git", "config", "user.email", "test@example.com"], tmp)
    _run(["git", "config", "user.name", "Test User"], tmp)
    (Path(tmp) / "a.txt").write_text("hello\n")
    _run(["git", "add", "a.txt"], tmp)
    _run(["git", "commit", "-q", "-m", "first commit"], tmp)
    (Path(tmp) / "a.txt").write_text("hello again\n")
    _run(["git", "add", "a.txt"], tmp)
    _run(["git", "commit", "-q", "-m", "second commit"], tmp)


class TestCli(unittest.TestCase):
    def test_summarizes_real_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            _make_repo(tmp)
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--repo", tmp])
            self.assertEqual(code, 0)
            self.assertIn("Total commits: 2", out.getvalue())
            self.assertIn("Test User", out.getvalue())

    def test_json_output(self) -> None:
        with TemporaryDirectory() as tmp:
            _make_repo(tmp)
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--repo", tmp, "--json"])
            self.assertEqual(code, 0)
            data = json.loads(out.getvalue())
            self.assertEqual(data["total_commits"], 2)

    def test_top_flag_limits_files(self) -> None:
        with TemporaryDirectory() as tmp:
            _make_repo(tmp)
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--repo", tmp, "--json", "--top", "1"])
            self.assertEqual(code, 0)
            data = json.loads(out.getvalue())
            self.assertLessEqual(len(data["top_files"]), 1)

    def test_non_repo_path_errors(self) -> None:
        with TemporaryDirectory() as tmp:
            code = main(["--repo", tmp])
            self.assertEqual(code, 2)

    def test_nonexistent_repo_path_errors(self) -> None:
        code = main(["--repo", "/nonexistent/path/xyz"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
