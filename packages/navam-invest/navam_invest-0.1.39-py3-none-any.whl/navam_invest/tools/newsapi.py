"""NewsAPI.org tools for market news and sentiment analysis.

IMPORTANT: This uses NewsAPI.org (https://newsapi.org), NOT NewsAPI.ai
Get your free API key at: https://newsapi.org/register
Free tier: 1,000 requests/day
"""

from typing import Any, Dict, Optional

import httpx
from langchain_core.tools import tool


async def _fetch_newsapi(endpoint: str, api_key: str, **params: Any) -> Dict[str, Any]:
    """Fetch data from NewsAPI.org.

    Args:
        endpoint: API endpoint ('everything' or 'top-headlines')
        api_key: NewsAPI.org API key
        **params: Additional query parameters

    Returns:
        JSON response from NewsAPI

    Raises:
        httpx.HTTPStatusError: If the request fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://newsapi.org/v2/{endpoint}",
            params=params,
            headers={"X-Api-Key": api_key},
            timeout=30.0,
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        return data


@tool
async def search_market_news(
    query: str, api_key: str, from_date: Optional[str] = None, limit: int = 5
) -> str:
    """Search for market news articles related to stocks, companies, or financial topics.

    This tool searches through millions of articles from financial news sources.
    Uses NewsAPI.org (NOT NewsAPI.ai). Get your key at: https://newsapi.org/register
    Note: Free tier has 1,000 requests/day limit and 24-hour article delay.

    Args:
        query: Search query (e.g., 'Tesla earnings', 'Federal Reserve', 'AAPL stock')
        api_key: NewsAPI.org API key
        from_date: Filter articles from this date onwards (format: YYYY-MM-DD)
        limit: Maximum number of articles to return (default: 5, max: 20)

    Returns:
        Formatted string with news articles including title, source, and description

    Examples:
        search_market_news("Apple stock analysis")
        search_market_news("Federal Reserve interest rates", from_date="2025-01-01")
    """
    try:
        # Limit to reasonable values for free tier
        limit = min(limit, 20)

        params: Dict[str, Any] = {
            "q": query,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": limit,
        }

        if from_date:
            params["from"] = from_date

        data = await _fetch_newsapi("everything", api_key, **params)

        if data.get("status") != "ok":
            error_msg = data.get("message", "Unknown error")
            return f"Error: {error_msg}"

        articles = data.get("articles", [])
        if not articles:
            return f"No news articles found for query: {query}"

        # Format results
        result_lines = [f"**News for '{query}'** ({len(articles)} articles)\n"]

        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            source = article.get("source", {}).get("name", "Unknown")
            published = article.get("publishedAt", "")[:10]  # YYYY-MM-DD
            description = article.get("description", "No description")
            url = article.get("url", "")

            result_lines.append(
                f"{i}. **{title}**\n"
                f"   Source: {source} | Date: {published}\n"
                f"   {description[:200]}...\n"
                f"   URL: {url}\n"
            )

        return "\n".join(result_lines)

    except httpx.HTTPStatusError as e:
        return f"HTTP error fetching news: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error fetching news for '{query}': {str(e)}"


@tool
async def get_top_financial_headlines(
    api_key: str, category: str = "business", country: str = "us", limit: int = 5
) -> str:
    """Get top financial and business headlines from major news sources.

    This tool retrieves current top headlines for financial news.
    Uses NewsAPI.org (NOT NewsAPI.ai). Get your key at: https://newsapi.org/register
    Note: Free tier has 1,000 requests/day limit and 24-hour article delay.

    Args:
        api_key: NewsAPI.org API key
        category: News category (default: 'business')
                 Options: business, general, technology
        country: Country code (default: 'us')
                Options: us, gb, ca, au, de, fr
        limit: Maximum number of headlines (default: 5, max: 20)

    Returns:
        Formatted string with top headlines including title, source, and description

    Examples:
        get_top_financial_headlines()
        get_top_financial_headlines(category="technology", country="us")
    """
    try:
        # Limit to reasonable values for free tier
        limit = min(limit, 20)

        params = {"category": category, "country": country, "pageSize": limit}

        data = await _fetch_newsapi("top-headlines", api_key, **params)

        if data.get("status") != "ok":
            error_msg = data.get("message", "Unknown error")
            return f"Error: {error_msg}"

        articles = data.get("articles", [])
        if not articles:
            return f"No top headlines found for {category} in {country.upper()}"

        # Format results
        result_lines = [
            f"**Top {category.title()} Headlines - {country.upper()}** ({len(articles)} articles)\n"
        ]

        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            source = article.get("source", {}).get("name", "Unknown")
            published = article.get("publishedAt", "")[:10]  # YYYY-MM-DD
            description = article.get("description", "No description")

            result_lines.append(
                f"{i}. **{title}**\n"
                f"   Source: {source} | Date: {published}\n"
                f"   {description[:200] if description else 'No description'}...\n"
            )

        return "\n".join(result_lines)

    except httpx.HTTPStatusError as e:
        return f"HTTP error fetching headlines: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error fetching top headlines: {str(e)}"


@tool
async def get_company_news(company_name: str, api_key: str, limit: int = 5) -> str:
    """Get recent news articles specifically about a company.

    This tool searches for news mentioning a specific company name.
    Useful for tracking company-specific events, announcements, and market sentiment.
    Uses NewsAPI.org (NOT NewsAPI.ai). Get your key at: https://newsapi.org/register
    Note: Free tier has 1,000 requests/day limit and 24-hour article delay.

    Args:
        company_name: Company name to search for (e.g., 'Apple', 'Tesla', 'Microsoft')
        api_key: NewsAPI.org API key
        limit: Maximum number of articles (default: 5, max: 20)

    Returns:
        Formatted string with company news including title, source, and summary

    Examples:
        get_company_news("Apple")
        get_company_news("Tesla", limit=10)
    """
    try:
        # Limit to reasonable values for free tier
        limit = min(limit, 20)

        params = {
            "q": company_name,
            "language": "en",
            "sortBy": "publishedAt",  # Most recent first
            "pageSize": limit,
        }

        data = await _fetch_newsapi("everything", api_key, **params)

        if data.get("status") != "ok":
            error_msg = data.get("message", "Unknown error")
            return f"Error: {error_msg}"

        articles = data.get("articles", [])
        if not articles:
            return f"No recent news found for company: {company_name}"

        # Format results
        result_lines = [
            f"**Recent News for {company_name}** ({len(articles)} articles)\n"
        ]

        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            source = article.get("source", {}).get("name", "Unknown")
            published = article.get("publishedAt", "")[:10]  # YYYY-MM-DD
            description = article.get("description", "No description")
            url = article.get("url", "")

            result_lines.append(
                f"{i}. **{title}**\n"
                f"   Source: {source} | Date: {published}\n"
                f"   {description[:200] if description else 'No description'}...\n"
                f"   URL: {url}\n"
            )

        return "\n".join(result_lines)

    except httpx.HTTPStatusError as e:
        return f"HTTP error fetching company news: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error fetching news for {company_name}: {str(e)}"
