"""Tests for Tax Scout agent."""

import pytest

from navam_invest.agents.tax_scout import create_tax_scout_agent
from navam_invest.tools import get_tools_for_agent


@pytest.mark.asyncio
async def test_create_tax_scout_agent():
    """Test Tax Scout agent creation."""
    agent = await create_tax_scout_agent()
    assert agent is not None
    assert hasattr(agent, "invoke")


def test_tax_scout_tools():
    """Test that Tax Scout agent has correct tools."""
    tools = get_tools_for_agent("tax_scout")

    # Should have at least 10 tax optimization tools
    assert len(tools) >= 10

    # Key tools for tax optimization
    tool_names = [tool.name for tool in tools]

    # Portfolio data access with cost basis
    assert "read_local_file" in tool_names
    assert "list_local_files" in tool_names

    # Market data for unrealized gain/loss calculations
    assert "get_quote" in tool_names
    assert "get_historical_data" in tool_names
    assert "get_stock_price" in tool_names

    # Company info for substitute security identification
    assert "get_company_info" in tool_names
    assert "get_financials" in tool_names
    assert "get_stock_overview" in tool_names


def test_tax_scout_agent_capabilities():
    """Test that Tax Scout agent has appropriate tools for each capability."""
    tools = get_tools_for_agent("tax_scout")
    tool_names = [tool.name for tool in tools]

    # Tax-loss harvesting capabilities
    tlh_tools = ["get_quote", "get_historical_data", "get_stock_price", "read_local_file"]
    assert all(tool in tool_names for tool in tlh_tools)

    # Wash-sale rule compliance capabilities
    wash_sale_tools = ["get_historical_data", "read_local_file", "list_local_files"]
    assert all(tool in tool_names for tool in wash_sale_tools)

    # Substitute security identification capabilities
    substitute_tools = ["get_company_info", "get_financials", "get_stock_overview"]
    assert all(tool in tool_names for tool in substitute_tools)

    # Capital gains/loss analysis capabilities
    gains_analysis_tools = ["get_quote", "get_historical_data", "read_local_file"]
    assert all(tool in tool_names for tool in gains_analysis_tools)


def test_tax_scout_has_portfolio_access():
    """Test that Tax Scout can access portfolio data."""
    tools = get_tools_for_agent("tax_scout")
    tool_names = [tool.name for tool in tools]

    # Must have file reading tools for portfolio data
    assert "read_local_file" in tool_names
    assert "list_local_files" in tool_names


def test_tax_scout_has_pricing_data():
    """Test that Tax Scout can access current and historical pricing."""
    tools = get_tools_for_agent("tax_scout")
    tool_names = [tool.name for tool in tools]

    # Must have pricing tools for gain/loss calculations
    pricing_tools = ["get_quote", "get_historical_data", "get_stock_price"]
    assert all(tool in tool_names for tool in pricing_tools)


def test_tax_scout_has_company_research():
    """Test that Tax Scout can research substitute securities."""
    tools = get_tools_for_agent("tax_scout")
    tool_names = [tool.name for tool in tools]

    # Must have company research tools for finding alternatives
    research_tools = ["get_company_info", "get_financials", "get_stock_overview"]
    assert all(tool in tool_names for tool in research_tools)
