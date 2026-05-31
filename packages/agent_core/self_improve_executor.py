from __future__ import annotations

import sys
import json
from pathlib import Path

from packages.agent_core.config import settings
from packages.agent_core.git_ops import GitRepositoryClient
from packages.agent_core.models import ImprovementSuggestion, PullRequestDraft, SelfImproveExecution


class SelfImproveExecutor:
    def __init__(self, repo_path: str | Path | None = None, git_client: GitRepositoryClient | None = None) -> None:
        if repo_path:
            self.repo_path = Path(repo_path)
        else:
            if getattr(sys, "frozen", False):
                self.repo_path = Path(sys.executable).resolve().parent
            else:
                self.repo_path = Path(__file__).resolve().parent.parent.parent
        self.git_client = git_client or GitRepositoryClient(repo_path=self.repo_path)

    def execute(self, suggestions: list[ImprovementSuggestion], pull_request: PullRequestDraft) -> SelfImproveExecution:
        docs_path = self.repo_path / "docs" / "self_improve"
        docs_path.mkdir(parents=True, exist_ok=True)

        markdown_path = docs_path / "auto_improvements.md"
        history_path = docs_path / "latest_run.json"

        markdown_path.write_text(self._build_markdown(suggestions, pull_request))
        history_path.write_text(
            json.dumps(
                {
                    "branch_name": pull_request.branch_name,
                    "title": pull_request.title,
                    "suggestions": [item.model_dump(mode="json") for item in suggestions],
                },
                indent=2,
            )
        )

        changed_files = [
            str(markdown_path.relative_to(self.repo_path)),
            str(history_path.relative_to(self.repo_path)),
        ]
        commit_message = pull_request.title

        self.git_client.create_branch(pull_request.branch_name)
        self.git_client.add_files(*changed_files)
        commit_sha = self.git_client.commit(commit_message)
        if settings.self_improve_auto_push:
            self.git_client.push_branch(pull_request.branch_name)

        return SelfImproveExecution(
            branch_name=pull_request.branch_name,
            commit_message=commit_message,
            commit_sha=commit_sha,
            changed_files=changed_files,
        )

    def _build_markdown(self, suggestions: list[ImprovementSuggestion], pull_request: PullRequestDraft) -> str:
        lines = [
            "# Auto Improvements",
            "",
            f"Branch: `{pull_request.branch_name}`",
            f"Title: `{pull_request.title}`",
            "",
            "## Suggestions",
            "",
        ]
        for index, suggestion in enumerate(suggestions, start=1):
            lines.extend(
                [
                    f"### {index}. {suggestion.title}",
                    f"- Rationale: {suggestion.rationale}",
                    f"- Proposed change: {suggestion.proposed_change}",
                    "",
                ]
            )
        lines.extend(["## Pull Request Body", "", pull_request.body, ""])
        return "\n".join(lines)
