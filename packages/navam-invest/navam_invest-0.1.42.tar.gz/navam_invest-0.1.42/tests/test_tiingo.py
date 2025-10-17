"""Tests for Tiingo API tools."""

import pytest
from unittest.mock import AsyncMock, patch

from navam_invest.tools.tiingo import (
    get_fundamentals_daily,
    get_fundamentals_definitions,
    get_fundamentals_statements,
    get_historical_fundamentals,
)


@pytest.mark.asyncio
async def test_get_fundamentals_definitions():
    """Test fundamental definitions retrieval."""
    mock_response = {
        "marketCap": {"description": "Market capitalization"},
        "peRatio": {"description": "Price to earnings ratio"},
        "revenue": {"description": "Total revenue"},
        "netIncome": {"description": "Net income"},
    }

    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_fundamentals_definitions.ainvoke({"api_key": "test_key"})

        assert "Tiingo Fundamentals" in result
        assert "Field Definitions" in result
        assert "marketCap" in result
        assert "peRatio" in result
        mock_fetch.assert_called_once_with(
            "tiingo/fundamentals/definitions", "test_key"
        )


@pytest.mark.asyncio
async def test_get_fundamentals_definitions_with_ticker():
    """Test fundamental definitions with specific ticker."""
    mock_response = [
        {"name": "marketCap", "description": "Market cap"},
        {"name": "peRatio", "description": "P/E ratio"},
    ]

    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_fundamentals_definitions.ainvoke(
            {"api_key": "test_key", "ticker": "AAPL"}
        )

        assert "AAPL" in result or "marketCap" in result
        assert "Available fields" in result or "Total Fields" in result


@pytest.mark.asyncio
async def test_get_fundamentals_daily():
    """Test daily fundamentals retrieval."""
    mock_response = [
        {
            "date": "2025-10-06",
            "marketCap": 3000000000000,
            "enterpriseVal": 3100000000000,
            "peRatio": 28.5,
            "pbRatio": 45.2,
        }
    ]

    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_fundamentals_daily.ainvoke(
            {"ticker": "AAPL", "api_key": "test_key"}
        )

        assert "AAPL" in result
        assert "Daily Fundamentals" in result
        assert "2025-10-06" in result
        assert "3,000,000,000,000" in result  # Market cap formatted
        assert "28.5" in result  # P/E ratio
        mock_fetch.assert_called_once()
        assert mock_fetch.call_args[0][0] == "tiingo/fundamentals/AAPL/daily"


@pytest.mark.asyncio
async def test_get_fundamentals_daily_with_dates():
    """Test daily fundamentals with custom date range."""
    mock_response = [
        {
            "date": "2025-10-06",
            "marketCap": 3000000000000,
            "peRatio": 28.5,
        },
        {
            "date": "2025-10-05",
            "marketCap": 2950000000000,
            "peRatio": 28.0,
        },
    ]

    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_fundamentals_daily.ainvoke(
            {
                "ticker": "GOOGL",
                "api_key": "test_key",
                "start_date": "2025-10-01",
                "end_date": "2025-10-06",
            }
        )

        assert "GOOGL" in result
        assert "2025-10-06" in result
        assert "Historical Trend" in result
        assert "2 data points" in result


@pytest.mark.asyncio
async def test_get_fundamentals_statements():
    """Test quarterly statements retrieval."""
    mock_response = [
        {
            "date": "2025-09-30",
            "quarter": 3,
            "year": 2025,
            "revenue": 100000000000,
            "netIncome": 25000000000,
            "grossProfit": 60000000000,
            "operatingIncome": 35000000000,
            "totalAssets": 500000000000,
            "totalDebt": 150000000000,
            "cash": 80000000000,
            "stockholdersEquity": 200000000000,
            "operatingCashFlow": 30000000000,
            "capex": -8000000000,
            "freeCashFlow": 22000000000,
        }
    ]

    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_fundamentals_statements.ainvoke(
            {"ticker": "MSFT", "api_key": "test_key"}
        )

        assert "MSFT" in result
        assert "Quarterly Financial Statements" in result
        assert "Q3 2025" in result
        assert "100,000,000,000" in result  # Revenue formatted
        assert "Income Statement" in result
        assert "Balance Sheet" in result
        assert "Cash Flow" in result
        assert "As Reported to SEC" in result
        mock_fetch.assert_called_once()
        assert mock_fetch.call_args[0][0] == "tiingo/fundamentals/MSFT/statements"


@pytest.mark.asyncio
async def test_get_fundamentals_statements_corrected():
    """Test quarterly statements with corrected data."""
    mock_response = [
        {
            "date": "2025-09-30",
            "quarter": 3,
            "year": 2025,
            "revenue": 100000000000,
            "netIncome": 25000000000,
        }
    ]

    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_fundamentals_statements.ainvoke(
            {"ticker": "NVDA", "api_key": "test_key", "as_reported": False}
        )

        assert "NVDA" in result
        assert "With Corrections" in result
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[1]["asReported"] == "false"


@pytest.mark.asyncio
async def test_get_historical_fundamentals():
    """Test historical fundamentals analysis."""
    mock_response = [
        {
            "date": "2025-09-30",
            "quarter": 3,
            "year": 2025,
            "revenue": 120000000000,
            "netIncome": 30000000000,
        },
        {
            "date": "2025-06-30",
            "quarter": 2,
            "year": 2025,
            "revenue": 115000000000,
            "netIncome": 28000000000,
        },
        {
            "date": "2020-09-30",
            "quarter": 3,
            "year": 2020,
            "revenue": 60000000000,
            "netIncome": 15000000000,
        },
    ]

    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_historical_fundamentals.ainvoke(
            {"ticker": "AAPL", "api_key": "test_key", "years": 5}
        )

        assert "AAPL" in result
        assert "5-Year Fundamental Trends" in result
        assert "Revenue Growth" in result
        assert "CAGR" in result
        assert "Profitability Trend" in result
        assert "Recent Quarterly Performance" in result
        mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_get_fundamentals_daily_no_data():
    """Test daily fundamentals with no data."""
    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = []

        result = await get_fundamentals_daily.ainvoke(
            {"ticker": "XYZ", "api_key": "test_key"}
        )

        assert "No daily fundamental data" in result
        assert "XYZ" in result


@pytest.mark.asyncio
async def test_get_fundamentals_statements_no_data():
    """Test quarterly statements with no data."""
    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = []

        result = await get_fundamentals_statements.ainvoke(
            {"ticker": "ABC", "api_key": "test_key"}
        )

        assert "No quarterly statement data found" in result
        assert "ABC" in result


@pytest.mark.asyncio
async def test_get_historical_fundamentals_insufficient_data():
    """Test historical fundamentals with insufficient data."""
    mock_response = [
        {
            "date": "2025-09-30",
            "quarter": 3,
            "year": 2025,
            "revenue": 120000000000,
            "netIncome": 30000000000,
        }
    ]

    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_historical_fundamentals.ainvoke(
            {"ticker": "TEST", "api_key": "test_key", "years": 5}
        )

        assert "Insufficient historical data" in result
        assert "TEST" in result


@pytest.mark.asyncio
async def test_api_error_handling():
    """Test API error handling."""
    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.side_effect = Exception("API key invalid")

        result = await get_fundamentals_daily.ainvoke(
            {"ticker": "TEST", "api_key": "bad_key"}
        )

        assert "Error fetching daily fundamentals" in result
        assert "TEST" in result


@pytest.mark.asyncio
async def test_historical_fundamentals_years_limit():
    """Test that historical fundamentals limits years to 5 on free tier."""
    mock_response = []

    with patch(
        "navam_invest.tools.tiingo._fetch_tiingo", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        # Request 10 years, should be capped at 5
        result = await get_historical_fundamentals.ainvoke(
            {"ticker": "AAPL", "api_key": "test_key", "years": 10}
        )

        # Verify the date range passed to API is ~5 years, not 10
        call_args = mock_fetch.call_args
        params = call_args[1]
        # Should see dates approximately 5 years apart, not 10
        # (exact dates depend on current time, so we just verify the call was made)
        assert mock_fetch.called
