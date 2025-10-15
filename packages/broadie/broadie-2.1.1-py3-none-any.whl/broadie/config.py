"""Broadie AI Framework — Configuration"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Unified configuration management for Broadie (dev → prod)."""

    def __init__(self):
        # Environment
        self.ENV: str = os.getenv("ENV", "development")
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

        # API / Server
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8080"))

        # Logging / Monitoring
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")
        self.ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
        self.METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))
        self.SENTRY_DSN: str | None = os.getenv("SENTRY_DSN")

        # Security
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
        self.ALLOWED_HOSTS: list[str] = os.getenv(
            "ALLOWED_HOSTS",
            "localhost,0.0.0.0",
        ).split(",")
        cors_origins = os.getenv("CORS_ORIGINS", "")
        self.CORS_ORIGINS: list[str] = cors_origins.split(",") if cors_origins else []

        # Database
        # Individual database components (for Cloud Run deployment)
        self.DB_HOST: str | None = os.getenv("DB_HOST")
        self.DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
        self.DB_NAME: str | None = os.getenv("DB_NAME")
        self.DB_USER: str | None = os.getenv("DB_USER")
        self.DB_PASSWORD: str | None = os.getenv("DB_PASSWORD")

        # Construct DATABASE_URL if individual components are provided
        if self.DB_HOST and self.DB_NAME and self.DB_USER and self.DB_PASSWORD:
            self.DATABASE_URL: str = (
                f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        else:
            # Fall back to explicit DATABASE_URL or SQLite default
            self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///broadie-agent.sqlite3")

        self.DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
        self.DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
        self.DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"

        # Limits & Performance
        self.RECURSION_LIMIT: int = int(os.getenv("RECURSION_LIMIT", "20"))
        self.MEMORY_DECAY_MINUTES: int = int(os.getenv("MEMORY_DECAY_MINUTES", "60"))
        self.WORKER_COUNT: int = int(os.getenv("WORKER_COUNT", "4"))
        self.MAX_CONCURRENT_REQUESTS: int = int(
            os.getenv("MAX_CONCURRENT_REQUESTS", "1000"),
        )
        self.REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "300"))

        # Swarm Configuration (Agent Transfer & Execution Limits)
        self.SWARM_MAX_TRANSFERS: int = int(os.getenv("SWARM_MAX_TRANSFERS", "20"))
        self.SWARM_RECURSION_LIMIT: int = int(os.getenv("SWARM_RECURSION_LIMIT", "50"))
        self.SWARM_STREAM_MODE: str = os.getenv("SWARM_STREAM_MODE", "values")

        # HTTP Client Settings
        self.HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", "10"))
        self.HTTP_RETRIES: int = int(os.getenv("HTTP_RETRIES", "3"))

        # Task Management
        self.TASK_TTL_SECONDS: int = int(
            os.getenv("TASK_TTL_SECONDS", "600"),
        )  # 10 minutes
        self.TASK_LIMIT_PER_THREAD: int = int(os.getenv("TASK_LIMIT_PER_THREAD", "4"))
        self.TASK_TEMP_DIR: str | None = os.getenv(
            "TASK_TEMP_DIR",
        )  # Will use system temp if None

        # Models
        self.EMBEDDING_MODEL: str = os.getenv(
            "EMBEDDING_MODEL",
            "google_vertexai:text-embedding-004",
        )
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "google_vertexai:gemini-2.0-flash")

        # LangSmith / LangChain Observability
        self.LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        self.LANGCHAIN_ENDPOINT: str = os.getenv(
            "LANGCHAIN_ENDPOINT",
            "https://api.smith.langchain.com",
        )
        self.LANGCHAIN_API_KEY: str | None = os.getenv("LANGCHAIN_API_KEY")
        self.LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "broadie")

        # A2A (Agent-to-Agent) Configuration
        self.A2A_ENABLED: bool = os.getenv("A2A_ENABLED", "false").lower() == "true"
        self.A2A_REGISTRY_URL: str = os.getenv(
            "A2A_REGISTRY_URL",
            "http://localhost:5000/api/v1/a2a",
        )
        self.A2A_API_KEY: str | None = os.getenv("A2A_API_KEY")
        self.A2A_TIMEOUT: int = int(os.getenv("A2A_TIMEOUT", "30"))
        self.A2A_REGISTRY_SECRET: str = os.getenv(
            "A2A_REGISTRY_SECRET",
            "change-me-in-production",
        )

        # JWT Configuration
        self.JWT_SECRET: str = os.getenv(
            "JWT_SECRET",
            "change-me-in-production",
        )

        # Authentication - Support both single API_KEY (legacy) and multiple API_KEYS
        legacy_key = os.getenv("API_KEY")
        api_keys_str = os.getenv("API_KEYS", "")

        # Parse API_KEYS from comma-separated string
        self.API_KEYS: set[str] = set()
        if api_keys_str:
            self.API_KEYS = {k.strip() for k in api_keys_str.split(",") if k.strip()}

        # Add legacy API_KEY if present (backward compatibility)
        if legacy_key:
            self.API_KEYS.add(legacy_key)

        # Keep API_KEY for backward compatibility
        self.API_KEY: str | None = legacy_key

        # Validate key length (minimum 32 characters for security)
        for key in self.API_KEYS:
            if len(key) < 32:
                import warnings

                warnings.warn(f"API key too short (min 32 chars recommended): {key[:8]}...", UserWarning, stacklevel=2)

        # Channels - Slack
        self.SLACK_BOT_TOKEN: str | None = os.getenv("SLACK_BOT_TOKEN")
        self.SLACK_SIGNING_SECRET: str | None = os.getenv("SLACK_SIGNING_SECRET")

        # Channels - Email/SMTP
        self.SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.example.com")
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.SMTP_USERNAME: str | None = os.getenv("SMTP_USERNAME")
        self.SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
        self.EMAIL_FROM: str = os.getenv("EMAIL_FROM", "alerts@example.com")

    def to_dict(self, safe: bool = True) -> dict[str, Any]:
        """Return settings as dict. Mask sensitive values if safe=True."""
        data = {key: value for key, value in self.__dict__.items() if not key.startswith("_")}

        if safe:
            sensitive_keys = [
                "SECRET_KEY",
                "API_KEY",
                "API_KEYS",
                "LANGCHAIN_API_KEY",
                "SENTRY_DSN",
                "A2A_API_KEY",
                "A2A_REGISTRY_SECRET",
                "SLACK_BOT_TOKEN",
                "SLACK_SIGNING_SECRET",
                "SMTP_USERNAME",
                "SMTP_PASSWORD",
                "DB_PASSWORD",
            ]
            for key in sensitive_keys:
                if data.get(key):
                    data[key] = "***MASKED***"
        return data


settings = Settings()
