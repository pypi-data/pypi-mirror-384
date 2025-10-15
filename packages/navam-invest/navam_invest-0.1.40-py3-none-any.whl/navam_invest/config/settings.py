"""Configuration management for Navam Invest."""

from typing import Optional

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""

    pass


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Anthropic API
    anthropic_api_key: str

    # Market Data APIs
    alpha_vantage_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None  # Finnhub alternative data
    tiingo_api_key: Optional[str] = None  # Tiingo historical fundamentals

    # Macro Data APIs
    fred_api_key: Optional[str] = None

    # News APIs
    newsapi_api_key: Optional[str] = None

    # Model configuration
    anthropic_model: str = "claude-3-7-sonnet-20250219"
    temperature: float = 0.0

    # Application settings
    debug: bool = False


def get_settings() -> Settings:
    """Get application settings instance.

    Raises:
        ConfigurationError: If required API keys are missing
    """
    try:
        return Settings()
    except ValidationError as e:
        # Extract missing field names
        missing_fields = []
        for error in e.errors():
            if error["type"] == "missing":
                field_name = error["loc"][0]
                missing_fields.append(field_name.upper())

        if missing_fields:
            fields_str = ", ".join(missing_fields)
            raise ConfigurationError(
                f"Missing required configuration: {fields_str}\n\n"
                f"Please set the following environment variable(s):\n"
                f"  {', '.join(missing_fields)}\n\n"
                f"You can:\n"
                f"1. Create a .env file with: {fields_str}=your_key_here\n"
                f"2. Set environment variable: export {missing_fields[0]}=your_key_here\n\n"
                f"Get your Anthropic API key at: https://console.anthropic.com/"
            ) from e
        raise
