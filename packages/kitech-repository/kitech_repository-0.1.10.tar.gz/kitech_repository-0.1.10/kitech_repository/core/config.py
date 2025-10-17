"""Configuration management for KITECH Repository."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Configuration settings for KITECH Repository.

    Environment variables can be used with KITECH_ prefix:
    - KITECH_API_BASE_URL: API base URL (default: http://localhost:6300)
    - KITECH_CHUNK_SIZE: Download chunk size in bytes (default: 8192)
    """

    model_config = ConfigDict(env_prefix="KITECH_")

    api_base_url: str = Field(
        default=os.getenv("KITECH_API_BASE_URL", "http://localhost:6300"),
        description="Base URL for KITECH API (without version)",
    )

    @model_validator(mode="after")
    def normalize_api_url(self) -> "Config":
        """Normalize API URL by removing trailing slashes."""
        self.api_base_url = self.api_base_url.rstrip("/")
        return self

    chunk_size: int = Field(
        default=int(os.getenv("KITECH_CHUNK_SIZE", "8192")),
        description="Chunk size for file downloads in bytes",
    )

    # Runtime-only properties (not saved to config.json)
    @property
    def config_dir(self) -> Path:
        """Directory for storing configuration files."""
        return Path.home() / ".kitech"

    @property
    def download_dir(self) -> Path:
        """Default directory for downloads."""
        return Path.cwd() / "downloads"

    @property
    def api_token(self) -> str | None:
        """API token - managed by AuthManager, not stored in config."""
        return None

    def save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / "config.json"
        config_file.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file or environment."""
        config_dir = Path.home() / ".kitech"
        config_file = config_dir / "config.json"

        if config_file.exists():
            import json

            data = json.loads(config_file.read_text())
            return cls(**data)

        return cls()


def get_config() -> Config:
    """Get the current configuration."""
    return Config.load()
