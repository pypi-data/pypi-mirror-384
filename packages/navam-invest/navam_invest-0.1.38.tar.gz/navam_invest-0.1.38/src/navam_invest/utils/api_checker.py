"""API connection checker for Navam Invest.

Provides utilities to test API connectivity and display status to users.
"""

from typing import Any, Dict, List, Optional

import httpx

from navam_invest.config.settings import get_settings


async def check_alpha_vantage(api_key: str) -> Dict[str, Any]:
    """Test Alpha Vantage API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.alphavantage.co/query",
                params={"function": "GLOBAL_QUOTE", "symbol": "AAPL", "apikey": api_key},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if "Global Quote" in data and data["Global Quote"]:
                    return {"status": "✅ Working", "details": "Successfully fetched quote data"}
                elif "Error Message" in data:
                    return {"status": "❌ Failed", "details": data["Error Message"]}
                elif "Note" in data:
                    return {"status": "⚠️ Rate Limited", "details": "API rate limit exceeded"}
                else:
                    return {"status": "❌ Failed", "details": "Invalid response format"}
            else:
                return {"status": "❌ Failed", "details": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "❌ Failed", "details": str(e)[:50]}


async def check_fred(api_key: str) -> Dict[str, Any]:
    """Test FRED API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.stlouisfed.org/fred/series",
                params={"series_id": "GDP", "api_key": api_key, "file_type": "json"},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if "seriess" in data:
                    return {"status": "✅ Working", "details": "Successfully fetched economic data"}
                else:
                    return {"status": "❌ Failed", "details": "Invalid response"}
            elif response.status_code == 400:
                return {"status": "❌ Failed", "details": "Invalid API key"}
            else:
                return {"status": "❌ Failed", "details": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "❌ Failed", "details": str(e)[:50]}


async def check_newsapi(api_key: str) -> Dict[str, Any]:
    """Test NewsAPI.org API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://newsapi.org/v2/top-headlines",
                params={"country": "us", "category": "business", "pageSize": 1},
                headers={"X-Api-Key": api_key},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    total = data.get("totalResults", 0)
                    return {"status": "✅ Working", "details": f"{total} articles available"}
                else:
                    return {"status": "❌ Failed", "details": data.get("message", "Unknown error")}
            elif response.status_code == 401:
                data = response.json()
                return {"status": "❌ Failed", "details": "Invalid API key"}
            elif response.status_code == 429:
                return {"status": "⚠️ Rate Limited", "details": "Daily limit exceeded"}
            else:
                return {"status": "❌ Failed", "details": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "❌ Failed", "details": str(e)[:50]}


async def check_finnhub(api_key: str) -> Dict[str, Any]:
    """Test Finnhub API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://finnhub.io/api/v1/quote",
                params={"symbol": "AAPL", "token": api_key},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if "c" in data:  # 'c' is current price
                    return {"status": "✅ Working", "details": "Successfully fetched quote"}
                else:
                    return {"status": "❌ Failed", "details": "Invalid response"}
            elif response.status_code == 401:
                return {"status": "❌ Failed", "details": "Invalid API key"}
            elif response.status_code == 429:
                return {"status": "⚠️ Rate Limited", "details": "API rate limit exceeded"}
            else:
                return {"status": "❌ Failed", "details": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "❌ Failed", "details": str(e)[:50]}


async def check_tiingo(api_key: str) -> Dict[str, Any]:
    """Test Tiingo API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.tiingo.com/tiingo/daily/aapl",
                headers={"Authorization": f"Token {api_key}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "ticker" in data:
                    return {"status": "✅ Working", "details": "Successfully fetched data"}
                else:
                    return {"status": "❌ Failed", "details": "Invalid response"}
            elif response.status_code == 401:
                return {"status": "❌ Failed", "details": "Invalid API key"}
            elif response.status_code == 429:
                return {"status": "⚠️ Rate Limited", "details": "Rate limit exceeded"}
            else:
                return {"status": "❌ Failed", "details": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "❌ Failed", "details": str(e)[:50]}


async def check_all_apis() -> List[Dict[str, str]]:
    """Check status of all configured APIs.

    Returns:
        List of dicts with API name, status, and details
    """
    settings = get_settings()
    results = []

    # Anthropic (always required)
    results.append({
        "api": "Anthropic",
        "status": "✅ Configured" if settings.anthropic_api_key else "❌ Missing",
        "details": "Required - AI model provider",
    })

    # Alpha Vantage (optional)
    if settings.alpha_vantage_api_key:
        result = await check_alpha_vantage(settings.alpha_vantage_api_key)
        results.append({"api": "Alpha Vantage", **result})
    else:
        results.append({
            "api": "Alpha Vantage",
            "status": "⚪ Not Configured",
            "details": "Optional - Stock quotes (25/day free)",
        })

    # FRED (optional)
    if settings.fred_api_key:
        result = await check_fred(settings.fred_api_key)
        results.append({"api": "FRED", **result})
    else:
        results.append({
            "api": "FRED",
            "status": "⚪ Not Configured",
            "details": "Optional - Economic data (unlimited free)",
        })

    # NewsAPI.org (optional)
    if settings.newsapi_api_key:
        result = await check_newsapi(settings.newsapi_api_key)
        results.append({"api": "NewsAPI.org", **result})
    else:
        results.append({
            "api": "NewsAPI.org",
            "status": "⚪ Not Configured",
            "details": "Optional - News (1,000/day free)",
        })

    # Finnhub (optional)
    if settings.finnhub_api_key:
        result = await check_finnhub(settings.finnhub_api_key)
        results.append({"api": "Finnhub", **result})
    else:
        results.append({
            "api": "Finnhub",
            "status": "⚪ Not Configured",
            "details": "Optional - Alt data (60/min free)",
        })

    # Tiingo (optional)
    if settings.tiingo_api_key:
        result = await check_tiingo(settings.tiingo_api_key)
        results.append({"api": "Tiingo", **result})
    else:
        results.append({
            "api": "Tiingo",
            "status": "⚪ Not Configured",
            "details": "Optional - Historical data (500/hr free)",
        })

    # Free APIs (no key needed)
    results.append({
        "api": "Yahoo Finance",
        "status": "✅ Built-in",
        "details": "Free - No API key required",
    })
    results.append({
        "api": "SEC EDGAR",
        "status": "✅ Built-in",
        "details": "Free - No API key required",
    })
    results.append({
        "api": "U.S. Treasury",
        "status": "✅ Built-in",
        "details": "Free - No API key required",
    })

    return results
