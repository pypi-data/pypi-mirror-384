"""FRED API tools for macroeconomic data."""

from typing import Any, Dict, Optional

import httpx
from langchain_core.tools import tool


async def _fetch_fred(
    endpoint: str, api_key: str, **params: Any
) -> Dict[str, Any]:
    """Fetch data from FRED API."""
    async with httpx.AsyncClient() as client:
        url = f"https://api.stlouisfed.org/fred/{endpoint}"
        params_with_key = {"api_key": api_key, "file_type": "json", **params}
        response = await client.get(url, params=params_with_key, timeout=30.0)
        response.raise_for_status()
        return response.json()


@tool
async def get_economic_indicator(series_id: str, api_key: str) -> str:
    """Get the latest value of an economic indicator from FRED.

    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'CPIAUCSL')
        api_key: FRED API key

    Returns:
        Formatted string with indicator name and latest value
    """
    try:
        # Get series info
        series_info = await _fetch_fred("series", api_key, series_id=series_id)

        if "seriess" not in series_info or not series_info["seriess"]:
            return f"No series found for ID {series_id}"

        series = series_info["seriess"][0]
        title = series.get("title", "Unknown")
        units = series.get("units", "")

        # Get latest observation
        observations = await _fetch_fred(
            "series/observations",
            api_key,
            series_id=series_id,
            sort_order="desc",
            limit=1,
        )

        if "observations" not in observations or not observations["observations"]:
            return f"No data available for {title}"

        latest = observations["observations"][0]
        date = latest.get("date", "N/A")
        value = latest.get("value", "N/A")

        return (
            f"**{title}**\n"
            f"Series ID: {series_id}\n"
            f"Latest Value: {value} {units}\n"
            f"Date: {date}"
        )
    except Exception as e:
        return f"Error fetching FRED data for {series_id}: {str(e)}"


@tool
async def get_key_macro_indicators(api_key: str) -> str:
    """Get key macroeconomic indicators summary.

    Args:
        api_key: FRED API key

    Returns:
        Summary of key economic indicators
    """
    indicators = {
        "GDP": "GDP",
        "UNRATE": "Unemployment Rate",
        "CPIAUCSL": "CPI (Inflation)",
        "DFF": "Federal Funds Rate",
    }

    results = []
    for series_id, name in indicators.items():
        try:
            data = await _fetch_fred(
                "series/observations",
                api_key,
                series_id=series_id,
                sort_order="desc",
                limit=1,
            )

            if "observations" in data and data["observations"]:
                latest = data["observations"][0]
                value = latest.get("value", "N/A")
                date = latest.get("date", "N/A")
                results.append(f"**{name}:** {value} (as of {date})")
        except Exception:
            results.append(f"**{name}:** Data unavailable")

    return "**Key Economic Indicators**\n\n" + "\n".join(results)
