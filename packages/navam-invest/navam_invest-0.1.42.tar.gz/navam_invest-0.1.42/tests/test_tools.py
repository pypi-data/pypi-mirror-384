"""Tests for API tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from navam_invest.tools.alpha_vantage import get_stock_price, get_stock_overview
from navam_invest.tools.fred import get_economic_indicator, get_key_macro_indicators


@pytest.mark.asyncio
async def test_get_stock_price_success() -> None:
    """Test successful stock price retrieval."""
    mock_response = {
        "Global Quote": {
            "05. price": "150.00",
            "09. change": "2.50",
            "10. change percent": "1.69%",
            "06. volume": "50000000",
        }
    }

    with patch("navam_invest.tools.alpha_vantage._fetch_alpha_vantage") as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_stock_price.ainvoke({"symbol": "AAPL", "api_key": "test"})
        assert "AAPL" in result
        assert "150.00" in result


@pytest.mark.asyncio
async def test_get_stock_overview_success() -> None:
    """Test successful stock overview retrieval."""
    mock_response = {
        "Symbol": "AAPL",
        "Name": "Apple Inc.",
        "Sector": "Technology",
        "Industry": "Consumer Electronics",
        "MarketCapitalization": "3000000000000",
        "PERatio": "30.5",
        "EPS": "6.05",
        "DividendYield": "0.005",
        "Description": "Apple Inc. designs and manufactures consumer electronics.",
    }

    with patch("navam_invest.tools.alpha_vantage._fetch_alpha_vantage") as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_stock_overview.ainvoke({"symbol": "AAPL", "api_key": "test"})
        assert "Apple Inc." in result
        assert "Technology" in result


@pytest.mark.asyncio
async def test_get_economic_indicator_success() -> None:
    """Test successful economic indicator retrieval."""
    mock_series_response = {
        "seriess": [{"title": "Gross Domestic Product", "units": "Billions of Dollars"}]
    }
    mock_obs_response = {"observations": [{"date": "2024-01-01", "value": "28000.0"}]}

    with patch("navam_invest.tools.fred._fetch_fred") as mock_fetch:
        mock_fetch.side_effect = [mock_series_response, mock_obs_response]

        result = await get_economic_indicator.ainvoke(
            {"series_id": "GDP", "api_key": "test"}
        )
        assert "Gross Domestic Product" in result
        assert "28000.0" in result


@pytest.mark.asyncio
async def test_get_key_macro_indicators() -> None:
    """Test key macro indicators retrieval."""
    mock_response = {"observations": [{"date": "2024-01-01", "value": "3.5"}]}

    with patch("navam_invest.tools.fred._fetch_fred") as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_key_macro_indicators.ainvoke({"api_key": "test"})
        assert "Key Economic Indicators" in result
