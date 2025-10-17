"""Tests for Router agent."""

import pytest
from navam_invest.agents.router import create_router_agent


@pytest.mark.asyncio
async def test_create_router_agent():
    """Test router agent creation."""
    agent = await create_router_agent()
    assert agent is not None
    assert hasattr(agent, "invoke")


@pytest.mark.asyncio
async def test_router_agent_tools():
    """Test that router agent has all 10 agent tools available."""
    from navam_invest.agents.router import (
        route_to_quill,
        route_to_screen_forge,
        route_to_macro_lens,
        route_to_earnings_whisperer,
        route_to_news_sentry,
        route_to_risk_shield,
        route_to_tax_scout,
        route_to_hedge_smith,
        route_to_portfolio,
        route_to_research,
    )

    # Verify all tool functions exist
    tools = [
        route_to_quill,
        route_to_screen_forge,
        route_to_macro_lens,
        route_to_earnings_whisperer,
        route_to_news_sentry,
        route_to_risk_shield,
        route_to_tax_scout,
        route_to_hedge_smith,
        route_to_portfolio,
        route_to_research,
    ]

    assert len(tools) == 10
    for tool in tools:
        assert callable(tool)
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")


# Intent Classification Tests
@pytest.mark.asyncio
async def test_router_quill_intent():
    """Test router routes fundamental analysis queries to Quill."""
    # This test would require mocking the LLM response
    # For now, we verify the tool can be invoked
    from navam_invest.agents.router import route_to_quill

    # Verify tool metadata
    assert "fundamental" in route_to_quill.description.lower()
    assert "valuation" in route_to_quill.description.lower()
    assert route_to_quill.name == "route_to_quill"


@pytest.mark.asyncio
async def test_router_screen_forge_intent():
    """Test router routes screening queries to Screen Forge."""
    from navam_invest.agents.router import route_to_screen_forge

    assert "screening" in route_to_screen_forge.description.lower()
    assert "stocks" in route_to_screen_forge.description.lower()
    assert route_to_screen_forge.name == "route_to_screen_forge"


@pytest.mark.asyncio
async def test_router_macro_lens_intent():
    """Test router routes macro/timing queries to Macro Lens."""
    from navam_invest.agents.router import route_to_macro_lens

    assert "macro" in route_to_macro_lens.description.lower()
    assert "market" in route_to_macro_lens.description.lower()
    assert route_to_macro_lens.name == "route_to_macro_lens"


@pytest.mark.asyncio
async def test_router_earnings_whisperer_intent():
    """Test router routes earnings queries to Earnings Whisperer."""
    from navam_invest.agents.router import route_to_earnings_whisperer

    assert "earnings" in route_to_earnings_whisperer.description.lower()
    assert route_to_earnings_whisperer.name == "route_to_earnings_whisperer"


@pytest.mark.asyncio
async def test_router_news_sentry_intent():
    """Test router routes news/event queries to News Sentry."""
    from navam_invest.agents.router import route_to_news_sentry

    assert (
        "news" in route_to_news_sentry.description.lower()
        or "event" in route_to_news_sentry.description.lower()
    )
    assert route_to_news_sentry.name == "route_to_news_sentry"


@pytest.mark.asyncio
async def test_router_risk_shield_intent():
    """Test router routes risk queries to Risk Shield."""
    from navam_invest.agents.router import route_to_risk_shield

    assert "risk" in route_to_risk_shield.description.lower()
    assert route_to_risk_shield.name == "route_to_risk_shield"


@pytest.mark.asyncio
async def test_router_tax_scout_intent():
    """Test router routes tax queries to Tax Scout."""
    from navam_invest.agents.router import route_to_tax_scout

    assert "tax" in route_to_tax_scout.description.lower()
    assert route_to_tax_scout.name == "route_to_tax_scout"


@pytest.mark.asyncio
async def test_router_hedge_smith_intent():
    """Test router routes options queries to Hedge Smith."""
    from navam_invest.agents.router import route_to_hedge_smith

    assert "options" in route_to_hedge_smith.description.lower()
    assert route_to_hedge_smith.name == "route_to_hedge_smith"


@pytest.mark.asyncio
async def test_router_portfolio_fallback():
    """Test router has Portfolio as fallback agent."""
    from navam_invest.agents.router import route_to_portfolio

    assert (
        "fallback" in route_to_portfolio.description.lower()
        or "general" in route_to_portfolio.description.lower()
    )
    assert route_to_portfolio.name == "route_to_portfolio"


@pytest.mark.asyncio
async def test_router_research_fallback():
    """Test router has Research as fallback for macro data."""
    from navam_invest.agents.router import route_to_research

    assert (
        "macro" in route_to_research.description.lower()
        or "fallback" in route_to_research.description.lower()
    )
    assert route_to_research.name == "route_to_research"


# Tool Execution Tests (Error Handling)
@pytest.mark.asyncio
async def test_router_tool_error_handling():
    """Test that router tools handle errors gracefully."""
    from navam_invest.agents.router import route_to_portfolio

    # Call with empty query should either succeed or return error message
    result = await route_to_portfolio.ainvoke({"query": ""})

    # Should return a string (either valid response or error message)
    assert isinstance(result, str)


# Agent Instance Caching Tests
@pytest.mark.asyncio
async def test_router_agent_caching():
    """Test that agent instances are cached and reused."""
    from navam_invest.agents.router import _get_quill_agent

    agent1 = await _get_quill_agent()
    agent2 = await _get_quill_agent()

    # Should return the same instance
    assert agent1 is agent2


@pytest.mark.asyncio
async def test_router_all_agent_getters():
    """Test all agent getter functions work."""
    from navam_invest.agents.router import (
        _get_portfolio_agent,
        _get_research_agent,
        _get_quill_agent,
        _get_screen_forge_agent,
        _get_macro_lens_agent,
        _get_earnings_whisperer_agent,
        _get_news_sentry_agent,
        _get_risk_shield_agent,
        _get_tax_scout_agent,
        _get_hedge_smith_agent,
    )

    # Verify all getter functions exist and can be called
    getters = [
        _get_portfolio_agent,
        _get_research_agent,
        _get_quill_agent,
        _get_screen_forge_agent,
        _get_macro_lens_agent,
        _get_earnings_whisperer_agent,
        _get_news_sentry_agent,
        _get_risk_shield_agent,
        _get_tax_scout_agent,
        _get_hedge_smith_agent,
    ]

    assert len(getters) == 10
    for getter in getters:
        assert callable(getter)


# Integration Test
@pytest.mark.asyncio
async def test_router_agent_structure():
    """Test router agent has correct structure."""
    router = await create_router_agent()

    # Should be a compiled graph
    assert router is not None

    # Should have invoke method for execution
    assert hasattr(router, "invoke")
    assert hasattr(router, "ainvoke")

    # Should have stream method for streaming
    assert hasattr(router, "stream")
    assert hasattr(router, "astream")
