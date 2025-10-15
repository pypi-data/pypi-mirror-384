"""
Configuration management for vMCP.

This module handles all configuration settings using pydantic-settings.
Environment variables can be used to override default values.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="vMCP", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=7860, description="Server port")
    base_url: str = Field(default="http://localhost:7860", description="Base URL for the application")

    # Database (SQLite by default, like Langflow)
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{Path.home() / '.vmcp' / 'vmcp.db'}",
        description="Database URL (SQLite by default, PostgreSQL optional)"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # Dummy User (No Auth)
    dummy_user_id: str = Field(default="local-user", description="Dummy user ID for local mode")
    dummy_user_email: str = Field(default="user@local.vmcp", description="Dummy user email")
    dummy_user_token: str = Field(default="local-token", description="Dummy authentication token")

    # Storage
    storage_path: Path = Field(
        default=Path.home() / ".vmcp" / "storage",
        description="Path for storing MCP configurations and data"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )

    # Tracing (OpenTelemetry)
    enable_tracing: bool = Field(default=False, description="Enable OpenTelemetry tracing")
    otlp_endpoint: Optional[str] = Field(default=None, description="OTLP endpoint for traces")
    service_name: str = Field(default="vmcp", description="Service name for tracing")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:7860"],
        description="Allowed CORS origins"
    )

    # Frontend
    serve_frontend: bool = Field(default=True, description="Serve frontend static files")
    frontend_path: Optional[Path] = Field(default=None, description="Path to frontend build directory")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Set frontend path if not specified
        if self.frontend_path is None:
            # Look for frontend build in package
            package_dir = Path(__file__).parent.parent
            frontend_build = package_dir / "frontend" / "dist"
            if frontend_build.exists():
                self.frontend_path = frontend_build


# Global settings instance
settings = Settings()
