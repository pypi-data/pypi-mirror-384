"""Tests for News Sentry agent."""

import pytest
from unittest.mock import AsyncMock, patch

from langchain_core.messages import HumanMessage, AIMessage
from navam_invest.agents.news_sentry import create_news_sentry_agent


@pytest.mark.asyncio
async def test_news_sentry_agent_initialization() -> None:
    """Test that News Sentry agent initializes correctly."""
    with patch("navam_invest.agents.news_sentry.get_settings") as mock_settings:
        mock_settings.return_value.anthropic_api_key = "test-key"
        mock_settings.return_value.anthropic_model = "claude-3-5-sonnet-20241022"
        mock_settings.return_value.temperature = 0.0
        mock_settings.return_value.newsapi_api_key = "test-newsapi-key"
        mock_settings.return_value.finnhub_api_key = "test-finnhub-key"

        agent = await create_news_sentry_agent()
        assert agent is not None


@pytest.mark.asyncio
async def test_news_sentry_graph_structure() -> None:
    """Test that News Sentry agent graph is properly structured."""
    with patch("navam_invest.agents.news_sentry.get_settings") as mock_settings:
        mock_settings.return_value.anthropic_api_key = "test-key"
        mock_settings.return_value.anthropic_model = "claude-3-5-sonnet-20241022"
        mock_settings.return_value.temperature = 0.0
        mock_settings.return_value.newsapi_api_key = "test-newsapi-key"
        mock_settings.return_value.finnhub_api_key = "test-finnhub-key"

        agent = await create_news_sentry_agent()

        # Test graph has correct nodes
        assert agent is not None
        # LangGraph compiled agents have nodes attribute
        assert hasattr(agent, "nodes") or hasattr(agent, "_nodes")


@pytest.mark.asyncio
async def test_news_sentry_tools_registered() -> None:
    """Test that News Sentry has correct tools registered."""
    from navam_invest.tools import get_tools_for_agent

    tools = get_tools_for_agent("news_sentry")

    # Check that key tools are available
    tool_names = [tool.name for tool in tools]

    assert "get_latest_8k" in tool_names
    assert "get_insider_transactions" in tool_names
    assert "search_market_news" in tool_names
    assert "get_company_news" in tool_names
    assert "get_analyst_recommendations" in tool_names
    assert "get_company_news_sentiment" in tool_names


@pytest.mark.asyncio
async def test_news_sentry_state_schema() -> None:
    """Test that News Sentry state schema is correct."""
    from navam_invest.agents.news_sentry import NewsSentryState

    # Test state initialization
    state: NewsSentryState = {"messages": []}

    assert "messages" in state
    assert isinstance(state["messages"], list)
