"""Quill - Equity Research agent using LangGraph.

Specialized agent for deep fundamental analysis, thesis building, and valuation.
Focus on bottom-up stock analysis with comprehensive fundamental tools.
"""

from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode

from navam_invest.config.settings import get_settings
from navam_invest.tools import bind_api_keys_to_tools, get_tools_for_agent


class QuillState(TypedDict):
    """State for Quill equity research agent."""

    messages: Annotated[list, add_messages]


async def create_quill_agent() -> StateGraph:
    """Create Quill equity research agent using LangGraph.

    Quill is a specialized equity research analyst focused on:
    - Deep fundamental analysis and DCF valuation
    - Investment thesis building with catalysts and risks
    - Bottom-up stock research with historical trends
    - SEC filings analysis and insider activity tracking

    Returns:
        Compiled LangGraph agent for equity research
    """
    settings = get_settings()

    # Initialize model
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=settings.temperature,
        max_tokens=8192,  # Ensure full responses without truncation
    )

    # Get Quill-specific tools (comprehensive equity research toolkit)
    # Includes: Yahoo Finance (quotes, financials, earnings, analyst recs),
    # Enhanced EDGAR (8-K, company facts, insider transactions),
    # FMP fundamentals, Tiingo historical data, and company news
    tools = get_tools_for_agent("quill")

    # Securely bind API keys to tools
    tools_with_keys = bind_api_keys_to_tools(
        tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        tiingo_key=settings.tiingo_api_key or "",
        newsapi_key=settings.newsapi_api_key or "",
    )

    llm_with_tools = llm.bind_tools(tools_with_keys)

    # Define agent node with specialized research prompt
    async def call_model(state: QuillState) -> dict:
        """Call the LLM with equity research tools."""
        system_msg = HumanMessage(
            content="You are Quill, an expert equity research analyst specializing in bottom-up fundamental analysis and investment thesis building. "
            "Your expertise includes:\n\n"
            "**Core Capabilities:**\n"
            "- Deep fundamental analysis using current and historical financial data (5 years via Tiingo)\n"
            "- Investment thesis development with clear catalysts, risks, and valuation targets\n"
            "- DCF and comparable company valuation modeling\n"
            "- Quarterly earnings tracking and trend analysis\n"
            "- SEC filings analysis (10-K, 10-Q) for business model understanding\n"
            "- Insider trading pattern analysis for conviction signals\n"
            "- Company-specific news analysis for thesis validation\n\n"
            "**Analysis Framework:**\n"
            "1. **Business Quality**: Analyze competitive moats, market position, and unit economics\n"
            "2. **Financial Health**: Review profitability trends, balance sheet strength, and cash flow generation\n"
            "3. **Growth Trajectory**: Assess revenue growth, margin expansion, and market opportunity\n"
            "4. **Valuation**: Compare P/E, P/S, EV/EBITDA vs peers and historical averages\n"
            "5. **Catalysts**: Identify near-term and long-term value drivers\n"
            "6. **Risks**: Flag key downside scenarios and red flags\n\n"
            "**Output Format:**\n"
            "- Lead with clear investment recommendation (Strong Buy/Buy/Hold/Sell/Strong Sell)\n"
            "- Provide fair value range with supporting DCF or comp-based valuation\n"
            "- Highlight 2-3 key catalysts and 2-3 key risks\n"
            "- Include relevant financial metrics and trends\n"
            "- Reference specific data points from filings and fundamentals\n\n"
            "**Tools Available:**\n"
            "- **Market Data**: Real-time quotes (Yahoo Finance), historical prices, market indices\n"
            "- **Fundamentals**: Financial statements (Yahoo + FMP), ratios, historical fundamentals (5yr via Tiingo)\n"
            "- **SEC Filings**: 10-K, 10-Q, 8-K (material events), company facts (XBRL), insider transactions (Form 4)\n"
            "- **Earnings**: Historical earnings with surprises, earnings calendar, upcoming estimates (Yahoo Finance)\n"
            "- **Analyst Coverage**: Analyst recommendations, price targets, rating changes (Yahoo Finance + Finnhub)\n"
            "- **Ownership**: Institutional holders, 13F filings, insider trading patterns\n"
            "- **Corporate Actions**: Dividend history, dividend yield, payment schedule\n"
            "- **News**: Company-specific news for thesis validation and event tracking\n\n"
            "Your goal is to produce institutional-quality equity research that helps retail investors make informed decisions. "
            "Be rigorous, data-driven, and intellectually honest about both upside and downside scenarios."
        )

        messages = [system_msg] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # Build graph
    workflow = StateGraph(QuillState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools_with_keys))

    # Add edges
    workflow.add_edge(START, "agent")

    # Conditional edge: if there are tool calls, go to tools; otherwise end
    def should_continue(state: QuillState) -> str:
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
