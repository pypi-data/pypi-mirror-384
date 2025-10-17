"""Configuration settings for Google Search Console MCP Server."""

from functools import cache
from typing import Literal

from pydantic import AliasChoices, EmailStr, Field, FilePath
from pydantic_settings import BaseSettings

type LogLevel = Literal[
    "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"
]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    google_credentials: FilePath = Field(
        description="Path to the Google Cloud credentials file. "
        "If not provided, the GOOGLE_APPLICATION_CREDENTIALS environment variable will be used.",
        validation_alias=AliasChoices(
            "google_credentials_path", "google_application_credentials"
        ),
    )

    subject: EmailStr | None = Field(
        default=None,
        description="Email address to impersonate using domain-wide delegation. "
        "If not provided, the GOOGLE_APPLICATION_SUBJECT environment variable will be used.",
        validation_alias=AliasChoices("google_application_subject"),
    )

    log_level: LogLevel = Field(
        default="INFO",
        description="Logging level",
    )


@cache
def load_settings(**kwargs) -> Settings:
    """Load settings from environment variables."""
    return Settings(**kwargs)
