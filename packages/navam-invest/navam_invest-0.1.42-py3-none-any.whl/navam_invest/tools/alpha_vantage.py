"""Alpha Vantage API tools for stock market data."""

from typing import Any, Dict, Optional

import httpx
from langchain_core.tools import tool

from navam_invest.cache import cached


async def _fetch_alpha_vantage(
    function: str, symbol: str, api_key: str, **kwargs: Any
) -> Dict[str, Any]:
    """Fetch data from Alpha Vantage API."""
    async with httpx.AsyncClient() as client:
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": api_key,
            **kwargs,
        }
        response = await client.get(
            "https://www.alphavantage.co/query", params=params, timeout=30.0
        )
        response.raise_for_status()
        return response.json()


@cached(source="alpha_vantage")
async def _get_stock_price_cached(symbol: str, api_key: str) -> str:
    """Cached implementation of get_stock_price."""
    data = await _fetch_alpha_vantage("GLOBAL_QUOTE", symbol, api_key)

    if "Global Quote" not in data or not data["Global Quote"]:
        return f"No data found for symbol {symbol}"

    quote = data["Global Quote"]
    price = quote.get("05. price", "N/A")
    change = quote.get("09. change", "N/A")
    change_pct = quote.get("10. change percent", "N/A")
    volume = quote.get("06. volume", "N/A")

    return (
        f"**{symbol}**\n"
        f"Price: ${price}\n"
        f"Change: {change} ({change_pct})\n"
        f"Volume: {volume}"
    )


@tool
async def get_stock_price(symbol: str, api_key: str) -> str:
    """Get current stock price and key metrics for a given symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        api_key: Alpha Vantage API key

    Returns:
        Formatted string with current price and key metrics
    """
    try:
        return await _get_stock_price_cached(symbol, api_key)
    except Exception as e:
        return f"Error fetching data for {symbol}: {str(e)}"


@cached(source="alpha_vantage")
async def _get_stock_overview_cached(symbol: str, api_key: str) -> str:
    """Cached implementation of get_stock_overview."""
    data = await _fetch_alpha_vantage("OVERVIEW", symbol, api_key)

    if not data or "Symbol" not in data:
        return f"No overview data found for {symbol}"

    name = data.get("Name", "N/A")
    sector = data.get("Sector", "N/A")
    industry = data.get("Industry", "N/A")
    market_cap = data.get("MarketCapitalization", "N/A")
    pe_ratio = data.get("PERatio", "N/A")
    div_yield = data.get("DividendYield", "N/A")
    eps = data.get("EPS", "N/A")
    description = data.get("Description", "")

    # Truncate description
    if description and len(description) > 200:
        description = description[:200] + "..."

    return (
        f"**{name} ({symbol})**\n\n"
        f"**Sector:** {sector}\n"
        f"**Industry:** {industry}\n"
        f"**Market Cap:** ${market_cap}\n"
        f"**P/E Ratio:** {pe_ratio}\n"
        f"**EPS:** {eps}\n"
        f"**Dividend Yield:** {div_yield}\n\n"
        f"**Description:** {description}"
    )


@tool
async def get_stock_overview(symbol: str, api_key: str) -> str:
    """Get company overview and fundamental data.

    Args:
        symbol: Stock ticker symbol
        api_key: Alpha Vantage API key

    Returns:
        Formatted company overview with key fundamentals
    """
    try:
        return await _get_stock_overview_cached(symbol, api_key)
    except Exception as e:
        return f"Error fetching overview for {symbol}: {str(e)}"

