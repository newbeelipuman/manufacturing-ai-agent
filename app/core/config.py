from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "manufacturing-ai-agent"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = "sqlite:///./local_dev.db"
    test_database_url: str | None = None
    postgres_db: str = "manufacturing_ai_agent"
    postgres_user: str = "agent_user"
    postgres_password: str = "agent_password"
    redis_url: str = "redis://redis:6379/0"
    log_level: str = "INFO"
    enable_sql_echo: bool = False
    llm_gateway_mode: str = "mock"
    llm_provider: str = "mock"
    llm_model: str = "mock-enterprise-agent"
    llm_fallback_model: str = "mock-safe-fallback"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_timeout_seconds: int = 20
    auth_secret_key: str = "dev-only-change-me"
    access_token_expire_minutes: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_database_url(self) -> str:
        if self.environment == "test" and self.test_database_url:
            return self.test_database_url
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
