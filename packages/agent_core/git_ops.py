from __future__ import annotations

import sys
import subprocess
from pathlib import Path


class GitRepositoryClient:
    def __init__(self, repo_path: str | Path | None = None) -> None:
        if repo_path:
            self.repo_path = Path(repo_path)
        else:
            if getattr(sys, "frozen", False):
                self.repo_path = Path(sys.executable).resolve().parent
            else:
                self.repo_path = Path(__file__).resolve().parent.parent.parent

    def create_branch(self, branch_name: str) -> None:
        self._run(["git", "checkout", "-b", branch_name])

    def add_files(self, *paths: str) -> None:
        self._run(["git", "add", *paths])

    def commit(self, message: str) -> str:
        self._run(["git", "commit", "-m", message])
        return self.current_commit_sha()

    def push_branch(self, branch_name: str) -> None:
        self._run(["git", "push", "-u", "origin", branch_name])

    def current_commit_sha(self) -> str:
        return self._run(["git", "rev-parse", "HEAD"])

    def _run(self, command: list[str]) -> str:
        completed = subprocess.run(
            command,
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()
