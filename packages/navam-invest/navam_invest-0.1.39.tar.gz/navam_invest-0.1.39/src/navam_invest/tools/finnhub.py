"""Finnhub API tools for alternative data and sentiment analysis."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from langchain_core.tools import tool


async def _fetch_finnhub(
    endpoint: str, api_key: str, **params: Any
) -> Dict[str, Any] | List[Dict[str, Any]]:
    """Fetch data from Finnhub API."""
    async with httpx.AsyncClient() as client:
        url = f"https://finnhub.io/api/v1/{endpoint}"
        params_with_key = {"token": api_key, **params}
        try:
            response = await client.get(url, params=params_with_key, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 403:
                raise Exception(
                    "Finnhub API access denied. Please check your API key is valid and has sufficient permissions."
                )
            elif status_code == 401:
                raise Exception(
                    "Finnhub API authentication failed. Please verify your API key."
                )
            elif status_code == 429:
                raise Exception(
                    "Finnhub API rate limit exceeded. Free tier: 60 calls/minute."
                )
            else:
                raise Exception(f"Finnhub API error: HTTP {status_code}")


@tool
async def get_company_news_sentiment(symbol: str, api_key: str) -> str:
    """Get news sentiment analysis for a company.

    Provides sentiment scores, sector averages, and bullish/bearish percentages
    based on recent news coverage.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        api_key: Finnhub API key

    Returns:
        Formatted string with news sentiment metrics
    """
    try:
        data = await _fetch_finnhub("news-sentiment", api_key, symbol=symbol)

        if not data or "buzz" not in data:
            return f"No news sentiment data found for {symbol}"

        # Extract sentiment metrics
        buzz = data.get("buzz", {})
        sentiment = data.get("sentiment", {})
        company_news_score = data.get("companyNewsScore", "N/A")
        sector_avg_news_score = data.get("sectorAverageNewsScore", "N/A")

        articles_in_last_week = buzz.get("articlesInLastWeek", 0)
        weekly_avg = buzz.get("weeklyAverage", 0)
        buzz_score = buzz.get("buzz", "N/A")

        bearish_percent = sentiment.get("bearishPercent", "N/A")
        bullish_percent = sentiment.get("bullishPercent", "N/A")

        return (
            f"**{symbol} - News Sentiment Analysis**\n\n"
            f"**Sentiment Scores:**\n"
            f"Company News Score: {company_news_score}\n"
            f"Sector Average: {sector_avg_news_score}\n"
            f"Bullish: {bullish_percent}% | Bearish: {bearish_percent}%\n\n"
            f"**News Buzz:**\n"
            f"Articles Last Week: {articles_in_last_week}\n"
            f"Weekly Average: {weekly_avg}\n"
            f"Buzz Score: {buzz_score}\n\n"
            f"*Higher company news score vs sector average indicates positive news momentum*"
        )
    except Exception as e:
        return f"Error fetching news sentiment for {symbol}: {str(e)}"


@tool
async def get_social_sentiment(symbol: str, api_key: str) -> str:
    """Get social media sentiment data for a stock.

    Analyzes social media mentions, positive/negative sentiment scores,
    and trending indicators from Reddit and Twitter.

    Args:
        symbol: Stock ticker symbol
        api_key: Finnhub API key

    Returns:
        Formatted string with social sentiment metrics
    """
    try:
        data = await _fetch_finnhub("stock/social-sentiment", api_key, symbol=symbol)

        if not data or "reddit" not in data:
            return f"No social sentiment data found for {symbol}"

        reddit = data.get("reddit", [])
        twitter = data.get("twitter", [])

        result = [f"**{symbol} - Social Media Sentiment**\n"]

        # Reddit sentiment (most recent)
        if reddit:
            recent_reddit = reddit[0]
            result.append(
                f"\n**Reddit Sentiment:**\n"
                f"Date: {recent_reddit.get('atTime', 'N/A')}\n"
                f"Mentions: {recent_reddit.get('mention', 0):,}\n"
                f"Positive Score: {recent_reddit.get('positiveScore', 0):.2f}\n"
                f"Negative Score: {recent_reddit.get('negativeScore', 0):.2f}\n"
                f"Score: {recent_reddit.get('score', 0):.2f}"
            )

        # Twitter sentiment (most recent)
        if twitter:
            recent_twitter = twitter[0]
            result.append(
                f"\n**Twitter Sentiment:**\n"
                f"Date: {recent_twitter.get('atTime', 'N/A')}\n"
                f"Mentions: {recent_twitter.get('mention', 0):,}\n"
                f"Positive Score: {recent_twitter.get('positiveScore', 0):.2f}\n"
                f"Negative Score: {recent_twitter.get('negativeScore', 0):.2f}\n"
                f"Score: {recent_twitter.get('score', 0):.2f}"
            )

        if not reddit and not twitter:
            return f"No social sentiment data available for {symbol}"

        result.append(
            "\n*Positive score > negative score indicates bullish sentiment*"
        )

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching social sentiment for {symbol}: {str(e)}"


@tool
async def get_insider_sentiment(
    symbol: str, api_key: str, from_date: Optional[str] = None
) -> str:
    """Get insider trading sentiment analysis.

    Aggregates insider trading activity (MSPR - monthly share purchase ratio)
    to gauge insider confidence in the company.

    Args:
        symbol: Stock ticker symbol
        api_key: Finnhub API key
        from_date: Start date in YYYY-MM-DD format (default: 1 year ago)

    Returns:
        Formatted string with insider sentiment metrics
    """
    try:
        # Default to 1 year ago if not specified
        if not from_date:
            one_year_ago = datetime.now() - timedelta(days=365)
            from_date = one_year_ago.strftime("%Y-%m-%d")

        data = await _fetch_finnhub(
            "stock/insider-sentiment", api_key, symbol=symbol, from_=from_date
        )

        if not data or "data" not in data:
            return f"No insider sentiment data found for {symbol}"

        insider_data = data.get("data", [])

        if not insider_data:
            return f"No insider trading activity found for {symbol} since {from_date}"

        result = [f"**{symbol} - Insider Sentiment Analysis**\n"]

        # Get recent months (latest 6)
        recent_months = insider_data[:6]

        for month_data in recent_months:
            year_month = month_data.get("symbol", "N/A")
            mspr = month_data.get("mspr", 0)  # Monthly Share Purchase Ratio
            change = month_data.get("change", 0)
            sentiment = "🟢 Bullish" if mspr > 0 else "🔴 Bearish" if mspr < 0 else "⚪ Neutral"

            result.append(
                f"\n**{year_month}**\n"
                f"MSPR: {mspr:.2f} | Change: {change:,}\n"
                f"Sentiment: {sentiment}"
            )

        result.append(
            "\n*MSPR > 0 indicates net insider buying (bullish), < 0 indicates net selling (bearish)*"
        )

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching insider sentiment for {symbol}: {str(e)}"


@tool
async def get_recommendation_trends(symbol: str, api_key: str) -> str:
    """Get analyst recommendation trends.

    Shows the distribution of analyst ratings (strong buy, buy, hold, sell, strong sell)
    and how recommendations have changed over time.

    Args:
        symbol: Stock ticker symbol
        api_key: Finnhub API key

    Returns:
        Formatted string with recommendation trends
    """
    try:
        data = await _fetch_finnhub("stock/recommendation", api_key, symbol=symbol)

        if not data:
            return f"No recommendation data found for {symbol}"

        # Get most recent recommendations (latest 4 periods)
        recent_recs = data[:4] if isinstance(data, list) else [data]

        result = [f"**{symbol} - Analyst Recommendation Trends**\n"]

        for rec in recent_recs:
            period = rec.get("period", "N/A")
            strong_buy = rec.get("strongBuy", 0)
            buy = rec.get("buy", 0)
            hold = rec.get("hold", 0)
            sell = rec.get("sell", 0)
            strong_sell = rec.get("strongSell", 0)

            total = strong_buy + buy + hold + sell + strong_sell
            bullish = strong_buy + buy
            bearish = sell + strong_sell

            # Calculate sentiment
            if bullish > hold + bearish:
                sentiment = "🟢 Bullish"
            elif bearish > hold + bullish:
                sentiment = "🔴 Bearish"
            else:
                sentiment = "⚪ Neutral"

            result.append(
                f"\n**{period}** ({total} analysts)\n"
                f"Strong Buy: {strong_buy} | Buy: {buy} | Hold: {hold}\n"
                f"Sell: {sell} | Strong Sell: {strong_sell}\n"
                f"Consensus: {sentiment}"
            )

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching recommendations for {symbol}: {str(e)}"


@tool
async def get_finnhub_company_news(
    symbol: str, api_key: str, from_date: Optional[str] = None, to_date: Optional[str] = None
) -> str:
    """Get recent company news articles from Finnhub.

    Retrieves news headlines, summaries, and sources for company-specific news.

    Args:
        symbol: Stock ticker symbol
        api_key: Finnhub API key
        from_date: Start date in YYYY-MM-DD format (default: 7 days ago)
        to_date: End date in YYYY-MM-DD format (default: today)

    Returns:
        Formatted string with recent news articles
    """
    try:
        # Default to last 7 days if not specified
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            week_ago = datetime.now() - timedelta(days=7)
            from_date = week_ago.strftime("%Y-%m-%d")

        data = await _fetch_finnhub(
            "company-news",
            api_key,
            symbol=symbol,
            from_=from_date,
            to=to_date,
        )

        if not data:
            return f"No news found for {symbol} between {from_date} and {to_date}"

        news_items = data if isinstance(data, list) else [data]

        result = [f"**{symbol} - Recent Company News** ({from_date} to {to_date})\n"]

        for i, news in enumerate(news_items[:10], 1):  # Limit to 10 most recent
            headline = news.get("headline", "No headline")
            summary = news.get("summary", "No summary available")
            source = news.get("source", "Unknown")
            timestamp = news.get("datetime", 0)
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "N/A"
            url = news.get("url", "")

            result.append(
                f"\n**{i}. {headline}**\n"
                f"Source: {source} | Date: {date_str}\n"
                f"Summary: {summary[:200]}{'...' if len(summary) > 200 else ''}\n"
                f"URL: {url}"
            )

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching company news for {symbol}: {str(e)}"
