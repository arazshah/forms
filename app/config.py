from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Araz Forms"
    app_env: Literal["development", "testing", "production"] = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"

    app_base_url: str = "http://localhost:8000"
    app_allowed_hosts: str = "localhost,127.0.0.1,web,forms.araz.me"
    app_secure_cookies: bool = False

    secret_key: str = "development-only-change-this-secret"

    database_url: str = "sqlite:////data/forms.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_hosts(self) -> list[str]:
        """Return the configured hosts as a normalized list."""

        return [
            host.strip()
            for host in self.app_allowed_hosts.split(",")
            if host.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_production_security(self) -> None:
        """Prevent starting production with an unsafe secret."""

        unsafe_secrets = {
            "",
            "development-only-change-this-secret",
            "replace-this-with-a-long-random-secret",
        }

        if self.is_production and self.secret_key in unsafe_secrets:
            raise RuntimeError(
                "A secure SECRET_KEY is required in production."
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production_security()
    return settings