from __future__ import annotations

import httpx

from packages.agent_core.config import settings


class GitHubPRClient:
    def __init__(self) -> None:
        self.repository = settings.github_repository
        self.token = settings.github_token
        self.base_url = settings.github_api_url.rstrip("/")

    def is_enabled(self) -> bool:
        return bool(self.repository and self.token)

    def create_pr_draft(self, title: str, body: str, head_branch: str) -> dict[str, str] | None:
        if not self.is_enabled():
            return None

        response = httpx.post(
            f"{self.base_url}/repos/{self.repository}/pulls",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "title": title,
                "body": body,
                "head": head_branch,
                "base": settings.github_base_branch,
                "draft": True,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "url": payload.get("html_url", ""),
            "number": str(payload.get("number", "")),
        }

    def repository_branch_ref(self, branch_name: str) -> str:
        return f"{self.repository.split('/', 1)[0]}:{branch_name}"
