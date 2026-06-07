from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DocuSync"
    database_url: str | None = None
    direct_url: str | None = None
    database_path: str = "docusync.db"
    github_webhook_secret: str = "dev-secret"
    github_token: str | None = None
    llm_provider: str = "mock"
    llm_temperature: float = 0.2
    openai_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    anthropic_api_key: str | None = None
    notion_api_key: str | None = None
    notion_version: str = "2022-06-28"
    notion_database_or_page_id: str | None = None
    module_mapping_path: str = "config/module_mapping.json"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8-sig", extra="ignore")

    @property
    def module_mapping_file(self) -> Path:
        configured_path = Path(self.module_mapping_path)
        candidates = [
            configured_path,
            Path.cwd() / configured_path,
            Path(__file__).resolve().parents[1] / "config" / "module_mapping.json",
            Path(__file__).resolve().parents[2] / "config" / "module_mapping.json",
        ]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.exists():
                return resolved
        return configured_path.resolve()

    @property
    def requested_module_mapping_file(self) -> Path:
        return Path(self.module_mapping_path).resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
