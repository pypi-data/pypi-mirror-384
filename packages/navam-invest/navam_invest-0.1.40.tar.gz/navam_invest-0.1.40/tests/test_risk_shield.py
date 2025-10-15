"""Tests for Risk Shield Manager agent."""

import pytest

from navam_invest.agents.risk_shield import create_risk_shield_agent
from navam_invest.tools import get_tools_for_agent


@pytest.mark.asyncio
async def test_create_risk_shield_agent():
    """Test Risk Shield agent creation."""
    agent = await create_risk_shield_agent()
    assert agent is not None
    assert hasattr(agent, "invoke")


def test_risk_shield_tools():
    """Test that Risk Shield agent has correct tools."""
    tools = get_tools_for_agent("risk_shield")

    # Should have at least 15 risk analysis tools
    assert len(tools) >= 15

    # Key tools for portfolio risk analysis
    tool_names = [tool.name for tool in tools]

    # Portfolio data access
    assert "read_local_file" in tool_names
    assert "list_local_files" in tool_names

    # Market data for risk calculations
    assert "get_quote" in tool_names
    assert "get_historical_data" in tool_names
    assert "get_market_indices" in tool_names

    # Volatility and correlation
    assert "get_company_info" in tool_names  # Contains beta
    assert "get_financials" in tool_names

    # Macro indicators for scenario testing
    assert "get_economic_indicator" in tool_names
    assert "get_key_macro_indicators" in tool_names

    # Treasury data for interest rate risk
    assert "get_treasury_yield_curve" in tool_names
    assert "get_treasury_rate" in tool_names


def test_risk_shield_agent_capabilities():
    """Test that Risk Shield agent has appropriate tools for each capability."""
    tools = get_tools_for_agent("risk_shield")
    tool_names = [tool.name for tool in tools]

    # Concentration risk analysis capabilities
    concentration_tools = ["get_quote", "get_historical_data", "get_company_info"]
    assert all(tool in tool_names for tool in concentration_tools)

    # Drawdown analysis capabilities
    drawdown_tools = ["get_historical_data", "get_market_indices"]
    assert all(tool in tool_names for tool in drawdown_tools)

    # VAR calculation capabilities
    var_tools = ["get_historical_data", "get_quote", "get_company_info"]
    assert all(tool in tool_names for tool in var_tools)

    # Scenario testing capabilities
    scenario_tools = ["get_economic_indicator", "get_key_macro_indicators", "get_treasury_yield_curve"]
    assert all(tool in tool_names for tool in scenario_tools)

    # Correlation analysis capabilities
    correlation_tools = ["get_historical_data", "get_stock_price", "get_historical_fundamentals"]
    assert all(tool in tool_names for tool in correlation_tools)
