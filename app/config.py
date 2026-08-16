from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Application
    app_name: str = "Araz Forms"
    app_env: Literal["development", "testing", "production"] = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"

    # Public URL
    app_base_url: str = "http://localhost:8000"

    # Security
    app_allowed_hosts: str = "localhost,127.0.0.1,web,forms.araz.me"
    app_secure_cookies: bool = False
    secret_key: str = "development-only-change-this-secret"

    # Admin login
    admin_username: str = "admin"
    admin_password: str = "change-this-admin-password"

    # Database
    database_url: str = "sqlite:////data/forms.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_hosts(self) -> list[str]:
        """Return configured allowed hosts as a normalized list."""

        return [
            host.strip()
            for host in self.app_allowed_hosts.split(",")
            if host.strip()
        ]

    @property
    def is_production(self) -> bool:
        """Return whether the application runs in production."""

        return self.app_env == "production"

    def validate_production_security(self) -> None:
        """Prevent starting production with unsafe default credentials."""

        unsafe_secret_keys = {
            "",
            "development-only-change-this-secret",
            "replace-this-with-a-long-random-secret",
        }

        unsafe_admin_passwords = {
            "",
            "change-this-admin-password",
            "replace-this-with-a-strong-admin-password",
        }

        if self.is_production and self.secret_key in unsafe_secret_keys:
            raise RuntimeError(
                "A secure SECRET_KEY is required in production."
            )

        if self.is_production and self.admin_password in unsafe_admin_passwords:
            raise RuntimeError(
                "A secure ADMIN_PASSWORD is required in production."
            )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    settings = Settings()
    settings.validate_production_security()
    return settings