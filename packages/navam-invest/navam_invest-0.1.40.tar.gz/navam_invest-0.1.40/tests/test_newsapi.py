"""Tests for NewsAPI tools."""

import pytest

from navam_invest.tools.newsapi import (
    get_company_news,
    get_top_financial_headlines,
    search_market_news,
)


@pytest.mark.asyncio
async def test_search_market_news_invalid_key() -> None:
    """Test search_market_news with invalid API key."""
    result = await search_market_news.ainvoke(
        {"query": "Tesla", "api_key": "invalid_key"}
    )
    assert "Error" in result or "HTTP error" in result


@pytest.mark.asyncio
async def test_get_top_financial_headlines_invalid_key() -> None:
    """Test get_top_financial_headlines with invalid API key."""
    result = await get_top_financial_headlines.ainvoke({"api_key": "invalid_key"})
    assert "Error" in result or "HTTP error" in result


@pytest.mark.asyncio
async def test_get_company_news_invalid_key() -> None:
    """Test get_company_news with invalid API key."""
    result = await get_company_news.ainvoke(
        {"company_name": "Apple", "api_key": "invalid_key"}
    )
    assert "Error" in result or "HTTP error" in result


@pytest.mark.asyncio
async def test_search_market_news_structure() -> None:
    """Test that search_market_news has correct structure."""
    # Verify tool is callable
    assert hasattr(search_market_news, "ainvoke")
    assert search_market_news.name == "search_market_news"
    assert "search" in search_market_news.description.lower()


@pytest.mark.asyncio
async def test_get_top_financial_headlines_structure() -> None:
    """Test that get_top_financial_headlines has correct structure."""
    assert hasattr(get_top_financial_headlines, "ainvoke")
    assert get_top_financial_headlines.name == "get_top_financial_headlines"
    assert "headline" in get_top_financial_headlines.description.lower()


@pytest.mark.asyncio
async def test_get_company_news_structure() -> None:
    """Test that get_company_news has correct structure."""
    assert hasattr(get_company_news, "ainvoke")
    assert get_company_news.name == "get_company_news"
    assert "company" in get_company_news.description.lower()


def test_newsapi_tools_exported() -> None:
    """Test that NewsAPI tools are properly exported."""
    from navam_invest.tools import (
        get_company_news as exported_company_news,
        get_top_financial_headlines as exported_headlines,
        search_market_news as exported_search,
    )

    assert exported_search is not None
    assert exported_headlines is not None
    assert exported_company_news is not None


def test_newsapi_tools_in_registry() -> None:
    """Test that NewsAPI tools are registered in TOOLS dict."""
    from navam_invest.tools import TOOLS

    assert "search_market_news" in TOOLS
    assert "get_top_financial_headlines" in TOOLS
    assert "get_company_news" in TOOLS


def test_newsapi_tools_in_category() -> None:
    """Test that NewsAPI tools are in news category."""
    from navam_invest.tools import get_tools_by_category

    news_tools = get_tools_by_category("news")
    assert len(news_tools) == 3

    tool_names = [tool.name for tool in news_tools]
    assert "search_market_news" in tool_names
    assert "get_top_financial_headlines" in tool_names
    assert "get_company_news" in tool_names
