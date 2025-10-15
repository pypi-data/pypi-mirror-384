"""Screen Forge - Equity Screening agent using LangGraph.

Specialized agent for systematic stock screening, idea generation, and candidate identification.
Focus on factor-based screening and weekly watchlist generation.
"""

from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode

from navam_invest.config.settings import get_settings
from navam_invest.tools import bind_api_keys_to_tools, get_tools_by_category


class ScreenForgeState(TypedDict):
    """State for Screen Forge equity screening agent."""

    messages: Annotated[list, add_messages]


async def create_screen_forge_agent() -> StateGraph:
    """Create Screen Forge equity screening agent using LangGraph.

    Screen Forge is a specialized equity screener focused on:
    - Systematic stock screening across multiple factors (value, growth, quality)
    - Weekly watchlist generation with clear entry criteria
    - Candidate identification for further deep-dive analysis
    - Factor-based scoring and ranking systems

    Returns:
        Compiled LangGraph agent for equity screening
    """
    settings = get_settings()

    # Initialize model
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=settings.temperature,
        max_tokens=8192,  # Ensure full responses without truncation
    )

    # Get screening tools (focused subset)
    market_tools = get_tools_by_category("market")  # Price, overview
    fundamentals_tools = get_tools_by_category("fundamentals")  # Screening, ratios, fundamentals
    sentiment_tools = get_tools_by_category("sentiment")  # Finnhub sentiment/recommendations

    tools = market_tools + fundamentals_tools + sentiment_tools

    # Securely bind API keys to tools
    tools_with_keys = bind_api_keys_to_tools(
        tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        finnhub_key=settings.finnhub_api_key or "",
    )

    llm_with_tools = llm.bind_tools(tools_with_keys)

    # Define agent node with specialized screening prompt
    async def call_model(state: ScreenForgeState) -> dict:
        """Call the LLM with equity screening tools."""
        system_msg = HumanMessage(
            content="You are Screen Forge, an expert equity screener specializing in systematic stock discovery and idea generation. "
            "Your expertise includes:\n\n"
            "**Core Capabilities:**\n"
            "- Multi-factor stock screening (value, growth, quality, momentum)\n"
            "- Systematic candidate identification for portfolio consideration\n"
            "- Weekly watchlist generation with clear entry criteria\n"
            "- Factor-based ranking and scoring systems\n"
            "- Screening across market cap, sector, and geography\n"
            "- Quick fundamental validation of screen results\n"
            "- Integration with sentiment data for conviction signals\n\n"
            "**Screening Framework:**\n"
            "1. **Factor Screens**: Value (low P/E, P/B), Growth (revenue/earnings growth), Quality (high ROE, margins), Momentum (price trends)\n"
            "2. **Quantitative Filters**: Market cap thresholds, liquidity requirements, financial health checks\n"
            "3. **Qualitative Overlays**: Sector themes, macro alignment, sentiment validation\n"
            "4. **Ranking System**: Multi-factor scoring to prioritize candidates\n"
            "5. **Output Format**: Ranked watchlist with key metrics and entry triggers\n\n"
            "**Common Screen Types:**\n"
            "- **Value Screen**: Low P/E (<15), low P/B (<2), positive earnings, market cap >$1B\n"
            "- **Growth Screen**: Revenue growth >20%, earnings growth >15%, expanding margins\n"
            "- **Quality Screen**: ROE >15%, net margin >10%, low debt/equity, consistent earnings\n"
            "- **Dividend Screen**: Dividend yield >3%, payout ratio <60%, 5+ year dividend history\n"
            "- **Small-Cap Screen**: Market cap $300M-$2B, growth >25%, positive cash flow\n"
            "- **Momentum Screen**: 52-week high proximity, positive analyst revisions, strong relative strength\n\n"
            "**Output Requirements:**\n"
            "- Provide 5-15 candidates ranked by screening score\n"
            "- Include key metrics for each candidate (P/E, growth rates, margins, market cap)\n"
            "- Highlight 1-2 standout metrics per candidate (why it passed the screen)\n"
            "- Suggest next steps: 'Deep dive with Quill' for top 3-5 picks\n"
            "- Note any limitations or risks in the screening criteria\n\n"
            "**Tools Available:**\n"
            "- Stock screening tool with multiple filter combinations\n"
            "- Financial ratios and fundamental data for validation\n"
            "- Market data (price, market cap, volume) for liquidity checks\n"
            "- Sentiment data (analyst recommendations, insider activity) for conviction\n\n"
            "Your goal is to generate high-quality investment ideas through systematic screening, "
            "providing retail investors with a curated watchlist of stocks worthy of deeper research. "
            "Be rigorous in your filtering and transparent about screening methodology."
        )

        messages = [system_msg] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # Build graph
    workflow = StateGraph(ScreenForgeState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools_with_keys))

    # Add edges
    workflow.add_edge(START, "agent")

    # Conditional edge: if there are tool calls, go to tools; otherwise end
    def should_continue(state: ScreenForgeState) -> str:
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    workflow.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", END: END}
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()
