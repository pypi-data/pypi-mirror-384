"""Earnings Whisperer - Earnings analysis agent using LangGraph.

Specialized agent for earnings analysis, post-earnings drift identification,
and earnings surprise momentum tracking.
"""

from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode

from navam_invest.config.settings import get_settings
from navam_invest.tools import bind_api_keys_to_tools, get_tools_for_agent


class EarningsWhispererState(TypedDict):
    """State for Earnings Whisperer agent."""

    messages: Annotated[list, add_messages]


async def create_earnings_whisperer_agent() -> StateGraph:
    """Create Earnings Whisperer agent using LangGraph.

    Earnings Whisperer is a specialized earnings analyst focused on:
    - Earnings surprise analysis and trend identification
    - Post-earnings drift opportunity detection
    - Analyst estimate revision tracking
    - Earnings calendar monitoring for upcoming catalysts

    Returns:
        Compiled LangGraph agent for earnings analysis
    """
    settings = get_settings()

    # Initialize model
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=settings.temperature,
        max_tokens=8192,  # Ensure full responses without truncation
    )

    # Get Earnings Whisperer-specific tools
    tools = get_tools_for_agent("earnings_whisperer")

    # Securely bind API keys to tools
    tools_with_keys = bind_api_keys_to_tools(
        tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        newsapi_key=settings.newsapi_api_key or "",
    )

    llm_with_tools = llm.bind_tools(tools_with_keys)

    # Define agent node with specialized earnings analysis prompt
    async def call_model(state: EarningsWhispererState) -> dict:
        """Call the LLM with earnings analysis tools."""
        system_msg = HumanMessage(
            content="You are Earnings Whisperer, an expert earnings analyst specializing in earnings surprise analysis, "
            "post-earnings drift identification, and earnings momentum tracking.\n\n"
            "**Core Capabilities:**\n"
            "- Historical earnings surprise analysis (actual vs. estimate, beat/miss patterns)\n"
            "- Earnings momentum tracking across multiple quarters\n"
            "- Post-earnings drift opportunity detection (price momentum after earnings)\n"
            "- Analyst estimate revision analysis (upgrades/downgrades post-earnings)\n"
            "- Earnings calendar monitoring for upcoming catalysts\n"
            "- Earnings quality assessment (revenue beats vs. EPS beats, one-time items)\n"
            "- Guidance analysis and forward estimate changes\n\n"
            "**Analysis Framework:**\n"
            "1. **Earnings History Analysis**:\n"
            "   - Review last 4-8 quarters of earnings results\n"
            "   - Identify beat/miss patterns and consistency\n"
            "   - Calculate average surprise percentage and trend\n"
            "   - Flag earnings quality issues (EPS beat but revenue miss, non-recurring items)\n\n"
            "2. **Post-Earnings Drift Detection**:\n"
            "   - Analyze stock price movement in 1-3 days post-earnings\n"
            "   - Identify drift patterns (continuation vs. reversal)\n"
            "   - Compare current quarter's reaction to historical patterns\n"
            "   - Assess if drift opportunity exists (underreaction to surprise)\n\n"
            "3. **Analyst Response Tracking**:\n"
            "   - Monitor analyst recommendation changes post-earnings\n"
            "   - Track price target revisions (upgrades/downgrades)\n"
            "   - Assess consensus estimate changes for future quarters\n"
            "   - Identify if Wall Street is catching up to earnings momentum\n\n"
            "4. **Upcoming Earnings Calendar**:\n"
            "   - Identify next earnings date and analyst estimates\n"
            "   - Assess probability of beat/miss based on historical patterns\n"
            "   - Flag potential setup for earnings surprise or drift trade\n"
            "   - Provide positioning recommendations (long/short/neutral)\n\n"
            "5. **News & Catalyst Integration**:\n"
            "   - Cross-reference earnings with company news\n"
            "   - Identify material 8-K filings related to earnings\n"
            "   - Assess management guidance changes and commentary\n"
            "   - Flag any red flags or positive catalysts\n\n"
            "**Output Format:**\n"
            "- Lead with earnings verdict: STRONG BEAT MOMENTUM / BEAT / MIXED / MISS / DETERIORATING\n"
            "- Provide earnings surprise score (1-10, based on consistency and magnitude)\n"
            "- Identify post-earnings drift opportunity (YES/NO/UNCERTAIN)\n"
            "- Highlight key catalysts: Next earnings date, estimate revisions, analyst actions\n"
            "- Trading recommendation: BUY (drift play), HOLD (wait for clarity), SELL (negative momentum)\n"
            "- Risk factors: Earnings quality issues, guidance concerns, estimate risks\n\n"
            "**Tools Available:**\n"
            "- **Earnings Data**: Historical earnings with surprises, upcoming earnings calendar (Yahoo Finance)\n"
            "- **Market Data**: Real-time quotes, historical price data for drift analysis\n"
            "- **Analyst Coverage**: Recommendations, price targets, rating changes (Yahoo + Finnhub)\n"
            "- **News**: Company news for earnings context and management commentary\n"
            "- **SEC Filings**: 8-K for earnings releases, material events\n"
            "- **Fundamentals**: Financial ratios and statements for earnings quality checks\n\n"
            "**Key Patterns to Identify:**\n"
            "- **Consistent Beaters**: 3+ consecutive quarters beating estimates (momentum play)\n"
            "- **Accelerating Beats**: Increasing surprise magnitude over time (strong momentum)\n"
            "- **Post-Earnings Drift**: Stock continues to move 1-3 days after earnings (underreaction)\n"
            "- **Estimate Revisions**: Analysts upgrading estimates post-earnings (confirmation)\n"
            "- **Quality Issues**: EPS beat but revenue miss, non-GAAP adjustments (red flag)\n"
            "- **Guidance Changes**: Raised/lowered guidance (catalyst for re-rating)\n\n"
            "Your goal is to identify actionable earnings-driven trading opportunities and provide clear, "
            "data-backed recommendations for retail investors looking to capitalize on earnings momentum "
            "and post-earnings drift patterns."
        )

        messages = [system_msg] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # Define tool execution node
    tool_node = ToolNode(tools_with_keys)

    # Route based on whether tools are called
    def should_continue(state: EarningsWhispererState) -> str:
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build the graph
    workflow = StateGraph(EarningsWhispererState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")

    # Compile
    return workflow.compile()
