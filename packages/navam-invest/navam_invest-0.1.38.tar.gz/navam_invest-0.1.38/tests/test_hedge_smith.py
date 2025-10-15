"""Tests for Hedge Smith agent."""

import pytest

from navam_invest.agents.hedge_smith import create_hedge_smith_agent
from navam_invest.tools import get_tools_for_agent


@pytest.mark.asyncio
async def test_create_hedge_smith_agent():
    """Test Hedge Smith agent creation."""
    agent = await create_hedge_smith_agent()
    assert agent is not None
    assert hasattr(agent, "invoke")


def test_hedge_smith_tools():
    """Test that Hedge Smith agent has correct tools."""
    tools = get_tools_for_agent("hedge_smith")

    # Should have at least 12 options strategy tools
    assert len(tools) >= 12

    # Key tools for options strategies
    tool_names = [tool.name for tool in tools]

    # Options data (critical for strategy design)
    assert "get_options_chain" in tool_names

    # Portfolio data access
    assert "read_local_file" in tool_names
    assert "list_local_files" in tool_names

    # Market data for underlying stocks
    assert "get_quote" in tool_names
    assert "get_historical_data" in tool_names
    assert "get_stock_price" in tool_names

    # Company fundamentals for analysis
    assert "get_company_info" in tool_names
    assert "get_financials" in tool_names
    assert "get_stock_overview" in tool_names

    # Volatility and market indices
    assert "get_market_indices" in tool_names

    # Dividend information (affects options strategies)
    assert "get_dividends" in tool_names

    # Sentiment for strategy timing
    assert "get_analyst_recommendations" in tool_names


def test_hedge_smith_agent_capabilities():
    """Test that Hedge Smith agent has appropriate tools for each capability."""
    tools = get_tools_for_agent("hedge_smith")
    tool_names = [tool.name for tool in tools]

    # Protective collar capabilities
    collar_tools = ["get_options_chain", "get_quote", "get_historical_data", "read_local_file"]
    assert all(tool in tool_names for tool in collar_tools)

    # Covered call capabilities
    covered_call_tools = ["get_options_chain", "get_quote", "get_dividends", "read_local_file"]
    assert all(tool in tool_names for tool in covered_call_tools)

    # Put protection capabilities
    put_protection_tools = ["get_options_chain", "get_quote", "get_historical_data", "get_company_info"]
    assert all(tool in tool_names for tool in put_protection_tools)

    # Strike selection and Greeks analysis capabilities
    greeks_tools = ["get_options_chain", "get_historical_data", "get_market_indices"]
    assert all(tool in tool_names for tool in greeks_tools)


def test_hedge_smith_has_options_chain():
    """Test that Hedge Smith has the critical options chain tool."""
    tools = get_tools_for_agent("hedge_smith")
    tool_names = [tool.name for tool in tools]

    # Must have options chain tool - this is the core capability
    assert "get_options_chain" in tool_names


def test_hedge_smith_has_portfolio_access():
    """Test that Hedge Smith can access portfolio data."""
    tools = get_tools_for_agent("hedge_smith")
    tool_names = [tool.name for tool in tools]

    # Must have file reading tools for portfolio holdings
    assert "read_local_file" in tool_names
    assert "list_local_files" in tool_names


def test_hedge_smith_has_market_data():
    """Test that Hedge Smith can access current and historical market data."""
    tools = get_tools_for_agent("hedge_smith")
    tool_names = [tool.name for tool in tools]

    # Must have market data tools for underlying stock analysis
    market_tools = ["get_quote", "get_historical_data", "get_stock_price"]
    assert all(tool in tool_names for tool in market_tools)


def test_hedge_smith_has_volatility_data():
    """Test that Hedge Smith can access volatility and risk metrics."""
    tools = get_tools_for_agent("hedge_smith")
    tool_names = [tool.name for tool in tools]

    # Must have tools for volatility and beta analysis
    volatility_tools = ["get_historical_data", "get_company_info", "get_market_indices"]
    assert all(tool in tool_names for tool in volatility_tools)


def test_hedge_smith_has_fundamental_data():
    """Test that Hedge Smith can access company fundamentals."""
    tools = get_tools_for_agent("hedge_smith")
    tool_names = [tool.name for tool in tools]

    # Must have fundamental data tools for underlying stock assessment
    fundamental_tools = ["get_company_info", "get_financials", "get_stock_overview"]
    assert all(tool in tool_names for tool in fundamental_tools)
