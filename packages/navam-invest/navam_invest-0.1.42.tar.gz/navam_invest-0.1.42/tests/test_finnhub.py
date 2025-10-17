"""Tests for Finnhub API tools."""

import pytest
from unittest.mock import AsyncMock, patch

from navam_invest.tools.finnhub import (
    get_company_news_sentiment,
    get_social_sentiment,
    get_insider_sentiment,
    get_recommendation_trends,
    get_finnhub_company_news,
)


@pytest.mark.asyncio
async def test_get_company_news_sentiment():
    """Test company news sentiment retrieval."""
    mock_response = {
        "buzz": {
            "articlesInLastWeek": 10,
            "weeklyAverage": 5.5,
            "buzz": 0.8,
        },
        "sentiment": {"bearishPercent": 0.25, "bullishPercent": 0.75},
        "companyNewsScore": 0.85,
        "sectorAverageNewsScore": 0.65,
    }

    with patch(
        "navam_invest.tools.finnhub._fetch_finnhub", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_company_news_sentiment.ainvoke(
            {"symbol": "AAPL", "api_key": "test_key"}
        )

        assert "AAPL" in result
        assert "News Sentiment Analysis" in result
        assert "0.85" in result
        assert "0.75" in result
        mock_fetch.assert_called_once_with("news-sentiment", "test_key", symbol="AAPL")


@pytest.mark.asyncio
async def test_get_social_sentiment():
    """Test social media sentiment retrieval."""
    mock_response = {
        "reddit": [
            {
                "atTime": "2025-10-06",
                "mention": 1500,
                "positiveScore": 0.75,
                "negativeScore": 0.25,
                "score": 0.50,
            }
        ],
        "twitter": [
            {
                "atTime": "2025-10-06",
                "mention": 2500,
                "positiveScore": 0.80,
                "negativeScore": 0.20,
                "score": 0.60,
            }
        ],
    }

    with patch(
        "navam_invest.tools.finnhub._fetch_finnhub", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_social_sentiment.ainvoke(
            {"symbol": "TSLA", "api_key": "test_key"}
        )

        assert "TSLA" in result
        assert "Social Media Sentiment" in result
        assert "Reddit" in result
        assert "Twitter" in result
        assert "1,500" in result
        mock_fetch.assert_called_once_with(
            "stock/social-sentiment", "test_key", symbol="TSLA"
        )


@pytest.mark.asyncio
async def test_get_insider_sentiment():
    """Test insider sentiment retrieval."""
    mock_response = {
        "data": [
            {"symbol": "2025-09", "mspr": 0.15, "change": 50000},
            {"symbol": "2025-08", "mspr": -0.05, "change": -20000},
        ]
    }

    with patch(
        "navam_invest.tools.finnhub._fetch_finnhub", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_insider_sentiment.ainvoke(
            {"symbol": "NVDA", "api_key": "test_key"}
        )

        assert "NVDA" in result
        assert "Insider Sentiment Analysis" in result
        assert "2025-09" in result
        assert "0.15" in result
        assert "Bullish" in result


@pytest.mark.asyncio
async def test_get_recommendation_trends():
    """Test analyst recommendation trends retrieval."""
    mock_response = [
        {
            "period": "2025-10",
            "strongBuy": 10,
            "buy": 5,
            "hold": 3,
            "sell": 1,
            "strongSell": 0,
        },
        {
            "period": "2025-09",
            "strongBuy": 8,
            "buy": 7,
            "hold": 4,
            "sell": 0,
            "strongSell": 0,
        },
    ]

    with patch(
        "navam_invest.tools.finnhub._fetch_finnhub", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_recommendation_trends.ainvoke(
            {"symbol": "MSFT", "api_key": "test_key"}
        )

        assert "MSFT" in result
        assert "Analyst Recommendation Trends" in result
        assert "2025-10" in result
        assert "Strong Buy: 10" in result
        assert "Bullish" in result


@pytest.mark.asyncio
async def test_get_company_news():
    """Test company news retrieval."""
    mock_response = [
        {
            "headline": "Company announces record earnings",
            "summary": "The company reported strong quarterly results",
            "source": "Reuters",
            "datetime": 1696665600,
            "url": "https://example.com/news",
        }
    ]

    with patch(
        "navam_invest.tools.finnhub._fetch_finnhub", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_response

        result = await get_finnhub_company_news.ainvoke(
            {"symbol": "GOOGL", "api_key": "test_key"}
        )

        assert "GOOGL" in result
        assert "Recent Company News" in result
        assert "record earnings" in result
        assert "Reuters" in result


@pytest.mark.asyncio
async def test_get_company_news_sentiment_no_data():
    """Test company news sentiment with no data."""
    with patch(
        "navam_invest.tools.finnhub._fetch_finnhub", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = {}

        result = await get_company_news_sentiment.ainvoke(
            {"symbol": "XYZ", "api_key": "test_key"}
        )

        assert "No news sentiment data found" in result
        assert "XYZ" in result


@pytest.mark.asyncio
async def test_get_social_sentiment_no_data():
    """Test social sentiment with no data."""
    with patch(
        "navam_invest.tools.finnhub._fetch_finnhub", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = {"reddit": [], "twitter": []}

        result = await get_social_sentiment.ainvoke(
            {"symbol": "ABC", "api_key": "test_key"}
        )

        assert "No social sentiment data available" in result
        assert "ABC" in result


@pytest.mark.asyncio
async def test_api_error_handling():
    """Test API error handling."""
    with patch(
        "navam_invest.tools.finnhub._fetch_finnhub", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.side_effect = Exception("API key invalid")

        result = await get_company_news_sentiment.ainvoke(
            {"symbol": "TEST", "api_key": "bad_key"}
        )

        assert "Error fetching news sentiment" in result
        assert "TEST" in result
