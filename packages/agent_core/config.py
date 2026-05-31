from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "recursive-self-improving-agent"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4.1-mini"
    database_url: str = "postgresql://agent:agent@postgres:5432/agent"
    redis_url: str = "redis://redis:6379/0"
    store_backend: str = "postgres"
    queue_backend: str = "redis"
    artifact_dir: str = "artifacts"
    self_improve_sample_limit: int = 20
    github_token: str = ""
    github_repository: str = ""
    github_api_url: str = "https://api.github.com"
    github_base_branch: str = "main"
    self_improve_branch_prefix: str = "self-improve"
    self_improve_auto_push: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def artifact_path(self) -> Path:
        path = Path(self.artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
