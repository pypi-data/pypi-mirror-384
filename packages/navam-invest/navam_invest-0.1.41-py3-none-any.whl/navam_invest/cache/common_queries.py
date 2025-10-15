"""Common queries for cache warming.

This module defines frequently accessed queries to pre-populate the cache,
improving initial user experience by reducing API calls.
"""

from typing import Any

# Import all cached tool functions
from navam_invest.tools.yahoo_finance import (
    _get_quote_cached,
    _get_market_indices_cached,
    _get_company_info_cached,
)
from navam_invest.tools.treasury import _get_treasury_yield_curve_cached
from navam_invest.tools.fred import _get_economic_indicator_cached
from navam_invest.config.settings import get_settings


def get_common_queries() -> list[dict[str, Any]]:
    """
    Get list of common queries for cache warming.

    Returns:
        List of query dictionaries for cache warming
    """
    queries = []

    # Get settings for API keys
    try:
        settings = get_settings()
        fred_api_key = settings.fred_api_key
    except Exception:
        # If settings fail, skip FRED queries
        fred_api_key = None

    # 1. Major Market Indices - Most frequently accessed
    queries.append(
        {
            "source": "yahoo_finance",
            "tool_name": "get_market_indices",
            "args": (),
            "kwargs": {},
            "func": _get_market_indices_cached,
        }
    )

    # 2. Popular Large-Cap Tech Stocks
    popular_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
    for symbol in popular_stocks:
        # Quote data
        queries.append(
            {
                "source": "yahoo_finance",
                "tool_name": "get_quote",
                "args": (symbol,),
                "kwargs": {},
                "func": _get_quote_cached,
            }
        )
        # Company info
        queries.append(
            {
                "source": "yahoo_finance",
                "tool_name": "get_company_info",
                "args": (symbol,),
                "kwargs": {},
                "func": _get_company_info_cached,
            }
        )

    # 3. Treasury Yield Curve - Key economic indicator
    queries.append(
        {
            "source": "treasury",
            "tool_name": "get_treasury_yield_curve",
            "args": (),
            "kwargs": {},
            "func": _get_treasury_yield_curve_cached,
        }
    )

    # 4. Key Economic Indicators from FRED (only if API key is configured)
    if fred_api_key:
        fred_series = [
            ("DGS10", "10-Year Treasury Rate"),  # 10-year treasury yield
            ("UNRATE", "Unemployment Rate"),  # Unemployment rate
            ("CPIAUCSL", "CPI"),  # Consumer Price Index
            ("GDP", "GDP"),  # Gross Domestic Product
        ]
        for series_id, _ in fred_series:
            queries.append(
                {
                    "source": "fred",
                    "tool_name": "get_economic_indicator",
                    "args": (series_id, fred_api_key),
                    "kwargs": {},
                    "func": _get_economic_indicator_cached,
                }
            )

    return queries


def get_query_summary() -> str:
    """
    Get human-readable summary of common queries.

    Returns:
        Formatted string describing the queries
    """
    return (
        "**Common Queries for Cache Warming:**\n\n"
        "1. **Market Indices** - S&P 500, Dow Jones, Nasdaq, Russell 2000, VIX\n"
        "2. **Popular Stocks** - AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA (quotes + info)\n"
        "3. **Treasury Data** - Current yield curve (3mo to 30yr)\n"
        "4. **Economic Indicators** - 10Y Treasury, Unemployment, CPI, GDP\n\n"
        f"**Total Queries:** {len(get_common_queries())}\n"
    )
