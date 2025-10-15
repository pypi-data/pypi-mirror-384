"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from navam_invest.config.settings import Settings, get_settings


def test_settings_with_env_vars() -> None:
    """Test settings load from environment variables."""
    with patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "test-key-123",
            "ALPHA_VANTAGE_API_KEY": "av-key-456",
            "FRED_API_KEY": "fred-key-789",
        },
    ):
        settings = Settings()
        assert settings.anthropic_api_key == "test-key-123"
        assert settings.alpha_vantage_api_key == "av-key-456"
        assert settings.fred_api_key == "fred-key-789"


def test_settings_defaults() -> None:
    """Test default settings values."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        settings = Settings()
        # Check that a default model is set (specific version may vary)
        assert settings.anthropic_model is not None
        assert "claude" in settings.anthropic_model.lower()
        assert settings.temperature == 0.0
        assert settings.debug is False


def test_get_settings() -> None:
    """Test get_settings function."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        settings = get_settings()
        assert isinstance(settings, Settings)
        assert settings.anthropic_api_key == "test-key"
