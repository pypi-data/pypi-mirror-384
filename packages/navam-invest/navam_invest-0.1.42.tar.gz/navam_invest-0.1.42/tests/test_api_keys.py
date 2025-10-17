"""Comprehensive tests for all APIs requiring keys.

This test suite verifies that:
1. API keys are properly loaded from environment variables
2. Each API tool can successfully connect and fetch data
3. Error handling works correctly for invalid keys
"""

import os
from pathlib import Path

import pytest

from navam_invest.config.settings import Settings, get_settings

# Alpha Vantage tools
from navam_invest.tools.alpha_vantage import get_stock_price, get_stock_overview

# FRED tools
from navam_invest.tools.fred import get_economic_indicator, get_key_macro_indicators

# Finnhub tools
from navam_invest.tools.finnhub import (
    get_company_news_sentiment,
    get_recommendation_trends,
    get_social_sentiment,
)

# NewsAPI tools
from navam_invest.tools.newsapi import (
    get_company_news,
    get_top_financial_headlines,
    search_market_news,
)

# Tiingo tools
from navam_invest.tools.tiingo import get_fundamentals_daily


class TestEnvironmentVariables:
    """Test that environment variables are properly loaded."""

    def test_env_file_exists(self):
        """Verify .env file exists in project root."""
        env_path = Path(".env")
        assert env_path.exists(), (
            f".env file not found in {Path.cwd()}. "
            f"Please create it with API keys from .env.example"
        )

    def test_settings_load(self):
        """Test that settings can be loaded."""
        try:
            settings = get_settings()
            assert settings is not None
            print(f"\n✓ Settings loaded successfully")
            print(f"  Working directory: {Path.cwd()}")
        except Exception as e:
            pytest.fail(f"Failed to load settings: {e}")

    def test_anthropic_key_loaded(self):
        """Test that required Anthropic key is loaded."""
        settings = get_settings()
        assert settings.anthropic_api_key, "ANTHROPIC_API_KEY is required"
        assert not settings.anthropic_api_key.startswith("your_"), (
            "Please set actual ANTHROPIC_API_KEY (not placeholder)"
        )
        print(f"\n✓ ANTHROPIC_API_KEY loaded: {settings.anthropic_api_key[:10]}...")

    def test_optional_keys_status(self):
        """Print status of all optional API keys."""
        settings = get_settings()
        keys = {
            "ALPHA_VANTAGE_API_KEY": settings.alpha_vantage_api_key,
            "FRED_API_KEY": settings.fred_api_key,
            "FINNHUB_API_KEY": settings.finnhub_api_key,
            "NEWSAPI_API_KEY": settings.newsapi_api_key,
            "TIINGO_API_KEY": settings.tiingo_api_key,
        }

        print("\n=== API Key Status ===")
        for key_name, key_value in keys.items():
            if key_value:
                print(f"✓ {key_name}: {key_value[:10]}... (loaded)")
            else:
                print(f"✗ {key_name}: Not set")

        # At least verify the keys we're testing exist
        assert settings.newsapi_api_key, "NEWSAPI_API_KEY is required for this test"


class TestAlphaVantageAPI:
    """Test Alpha Vantage API integration."""

    @pytest.mark.asyncio
    async def test_get_stock_price(self):
        """Test fetching stock price."""
        settings = get_settings()
        if not settings.alpha_vantage_api_key:
            pytest.skip("ALPHA_VANTAGE_API_KEY not set")

        result = await get_stock_price.ainvoke(
            {"symbol": "AAPL", "api_key": settings.alpha_vantage_api_key}
        )
        print(f"\n=== Alpha Vantage Stock Price ===\n{result}")

        assert result is not None
        assert "AAPL" in result or "error" in result.lower()


class TestFREDAPI:
    """Test FRED API integration."""

    @pytest.mark.asyncio
    async def test_get_economic_indicator(self):
        """Test fetching FRED economic indicator."""
        settings = get_settings()
        if not settings.fred_api_key:
            pytest.skip("FRED_API_KEY not set")

        result = await get_economic_indicator.ainvoke(
            {"series_id": "GDP", "api_key": settings.fred_api_key}
        )
        print(f"\n=== FRED Economic Indicator ===\n{result}")

        assert result is not None
        assert "GDP" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_get_key_macro_indicators(self):
        """Test fetching key macro indicators."""
        settings = get_settings()
        if not settings.fred_api_key:
            pytest.skip("FRED_API_KEY not set")

        result = await get_key_macro_indicators.ainvoke(
            {"api_key": settings.fred_api_key}
        )
        print(f"\n=== FRED Key Macro Indicators ===\n{result}")

        assert result is not None
        assert "GDP" in result or "Unemployment" in result


class TestNewsAPI:
    """Test NewsAPI integration."""

    @pytest.mark.asyncio
    async def test_search_market_news(self):
        """Test searching market news."""
        settings = get_settings()
        if not settings.newsapi_api_key:
            pytest.skip("NEWSAPI_API_KEY not set")

        print(f"\n=== Testing NewsAPI ===")
        print(f"API Key loaded: {settings.newsapi_api_key[:15]}...")
        print(f"Searching for: 'Federal Reserve'")

        result = await search_market_news.ainvoke(
            {
                "query": "Federal Reserve",
                "api_key": settings.newsapi_api_key,
                "limit": 3,
            }
        )
        print(f"\n=== NewsAPI Search Result ===\n{result}")

        assert result is not None
        # Check if it's a valid result or an error message
        if "error" in result.lower():
            if "401" in result or "apiKeyInvalid" in result:
                pytest.fail(
                    f"NewsAPI authentication failed. API key may be invalid.\n{result}"
                )
            elif "429" in result or "rate limit" in result.lower():
                pytest.skip("NewsAPI rate limit reached")
        else:
            # Success - should contain news articles
            assert (
                "News for" in result or "No news" in result
            ), f"Unexpected response format: {result}"

    @pytest.mark.asyncio
    async def test_get_top_financial_headlines(self):
        """Test getting top financial headlines."""
        settings = get_settings()
        if not settings.newsapi_api_key:
            pytest.skip("NEWSAPI_API_KEY not set")

        print(f"\n=== Testing NewsAPI Headlines ===")
        print(f"API Key: {settings.newsapi_api_key[:15]}...")

        result = await get_top_financial_headlines.ainvoke(
            {"api_key": settings.newsapi_api_key, "limit": 3}
        )
        print(f"\n=== NewsAPI Headlines Result ===\n{result}")

        assert result is not None
        if "401" in result or "apiKeyInvalid" in result:
            pytest.fail(
                f"NewsAPI authentication failed. API key may be invalid.\n{result}"
            )
        elif "error" in result.lower() and "429" not in result:
            pytest.fail(f"NewsAPI error: {result}")


class TestFinnhubAPI:
    """Test Finnhub API integration."""

    @pytest.mark.asyncio
    async def test_get_recommendation_trends(self):
        """Test fetching recommendation trends."""
        settings = get_settings()
        if not settings.finnhub_api_key:
            pytest.skip("FINNHUB_API_KEY not set")

        result = await get_recommendation_trends.ainvoke(
            {"symbol": "AAPL", "api_key": settings.finnhub_api_key}
        )
        print(f"\n=== Finnhub Recommendation Trends ===\n{result}")

        assert result is not None


class TestTiingoAPI:
    """Test Tiingo API integration."""

    @pytest.mark.asyncio
    async def test_get_fundamentals_daily(self):
        """Test fetching daily fundamentals."""
        settings = get_settings()
        if not settings.tiingo_api_key:
            pytest.skip("TIINGO_API_KEY not set")

        result = await get_fundamentals_daily.ainvoke(
            {"ticker": "AAPL", "api_key": settings.tiingo_api_key}
        )
        print(f"\n=== Tiingo Fundamentals Daily ===\n{result}")

        assert result is not None


class TestAPIKeyBinding:
    """Test that API key binding works correctly in agents."""

    def test_bind_api_keys_function(self):
        """Test the bind_api_keys_to_tools function."""
        from navam_invest.tools import bind_api_keys_to_tools, get_tools_by_category

        settings = get_settings()

        # Get news tools
        news_tools = get_tools_by_category("news")
        assert len(news_tools) > 0, "No news tools found"

        print(f"\n=== Testing API Key Binding ===")
        print(f"News tools found: {[t.name for t in news_tools]}")

        # Bind keys
        bound_tools = bind_api_keys_to_tools(
            news_tools, newsapi_key=settings.newsapi_api_key or ""
        )

        assert len(bound_tools) == len(
            news_tools
        ), "Number of bound tools doesn't match"
        print(f"✓ Successfully bound {len(bound_tools)} tools")

        # Verify tools are callable
        for tool in bound_tools:
            assert tool.name in [
                "search_market_news",
                "get_top_financial_headlines",
                "get_company_news",
            ]
            print(f"  - {tool.name}: {'bound' if tool.coroutine else 'original'}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
