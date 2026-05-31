from __future__ import annotations

import httpx

from packages.agent_core.config import settings


class LLMClient:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(self) -> None:
        self.base_url = settings.openai_base_url.rstrip("/")
        self.api_key = settings.openai_api_key
        self.model_name = settings.model_name

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a pragmatic autonomous software agent. Provide concise, useful task outputs.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices", [])
        if not choices:
            raise ValueError("LLM response did not include choices")
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, list):
            return "\n".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()
        if not isinstance(content, str) or not content.strip():
            raise ValueError("LLM response content is empty")
        return content.strip()


def get_llm_client() -> LLMClient:
    return OpenAICompatibleLLMClient()
