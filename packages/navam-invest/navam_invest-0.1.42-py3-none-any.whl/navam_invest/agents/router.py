"""Router - Intent-based routing supervisor agent using LangGraph.

Automatically classifies user intent and routes to appropriate specialist agents.
Coordinates multi-agent responses for complex queries.
"""

import asyncio
from typing import Annotated, TypedDict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from navam_invest.config.settings import get_settings
from navam_invest.agents.portfolio import create_portfolio_agent
from navam_invest.agents.research import create_research_agent
from navam_invest.agents.quill import create_quill_agent
from navam_invest.agents.screen_forge import create_screen_forge_agent
from navam_invest.agents.macro_lens import create_macro_lens_agent
from navam_invest.agents.earnings_whisperer import create_earnings_whisperer_agent
from navam_invest.agents.news_sentry import create_news_sentry_agent
from navam_invest.agents.risk_shield import create_risk_shield_agent
from navam_invest.agents.tax_scout import create_tax_scout_agent
from navam_invest.agents.hedge_smith import create_hedge_smith_agent


# Global agent instances (initialized once)
_portfolio_agent = None
_research_agent = None
_quill_agent = None
_screen_forge_agent = None
_macro_lens_agent = None
_earnings_whisperer_agent = None
_news_sentry_agent = None
_risk_shield_agent = None
_tax_scout_agent = None
_hedge_smith_agent = None

# Global streaming event queue for progressive disclosure
# Format: {"type": "tool_call"|"tool_complete"|"error", "agent": str, "tool_name": str, "args": dict, ...}
_streaming_queue: Optional[asyncio.Queue] = None


def set_streaming_queue(queue: asyncio.Queue) -> None:
    """Set the global streaming queue for progressive disclosure.

    Args:
        queue: AsyncIO queue for streaming sub-agent tool call events
    """
    global _streaming_queue
    _streaming_queue = queue


def get_streaming_queue() -> Optional[asyncio.Queue]:
    """Get the global streaming queue.

    Returns:
        The streaming queue if set, None otherwise
    """
    return _streaming_queue


async def _get_portfolio_agent():
    """Get or create Portfolio agent instance."""
    global _portfolio_agent
    if _portfolio_agent is None:
        _portfolio_agent = await create_portfolio_agent()
    return _portfolio_agent


async def _get_research_agent():
    """Get or create Research agent instance."""
    global _research_agent
    if _research_agent is None:
        _research_agent = await create_research_agent()
    return _research_agent


async def _get_quill_agent():
    """Get or create Quill agent instance."""
    global _quill_agent
    if _quill_agent is None:
        _quill_agent = await create_quill_agent()
    return _quill_agent


async def _get_screen_forge_agent():
    """Get or create Screen Forge agent instance."""
    global _screen_forge_agent
    if _screen_forge_agent is None:
        _screen_forge_agent = await create_screen_forge_agent()
    return _screen_forge_agent


async def _get_macro_lens_agent():
    """Get or create Macro Lens agent instance."""
    global _macro_lens_agent
    if _macro_lens_agent is None:
        _macro_lens_agent = await create_macro_lens_agent()
    return _macro_lens_agent


async def _get_earnings_whisperer_agent():
    """Get or create Earnings Whisperer agent instance."""
    global _earnings_whisperer_agent
    if _earnings_whisperer_agent is None:
        _earnings_whisperer_agent = await create_earnings_whisperer_agent()
    return _earnings_whisperer_agent


async def _get_news_sentry_agent():
    """Get or create News Sentry agent instance."""
    global _news_sentry_agent
    if _news_sentry_agent is None:
        _news_sentry_agent = await create_news_sentry_agent()
    return _news_sentry_agent


async def _get_risk_shield_agent():
    """Get or create Risk Shield agent instance."""
    global _risk_shield_agent
    if _risk_shield_agent is None:
        _risk_shield_agent = await create_risk_shield_agent()
    return _risk_shield_agent


async def _get_tax_scout_agent():
    """Get or create Tax Scout agent instance."""
    global _tax_scout_agent
    if _tax_scout_agent is None:
        _tax_scout_agent = await create_tax_scout_agent()
    return _tax_scout_agent


async def _get_hedge_smith_agent():
    """Get or create Hedge Smith agent instance."""
    global _hedge_smith_agent
    if _hedge_smith_agent is None:
        _hedge_smith_agent = await create_hedge_smith_agent()
    return _hedge_smith_agent


# Helper function to stream agent execution and push events to queue
async def _stream_agent_with_tool_log(agent, query: str, agent_name: str = "Unknown") -> str:
    """Stream agent execution and push tool call events to global queue for progressive disclosure.

    Args:
        agent: The LangGraph agent to stream
        query: The query to send to the agent
        agent_name: Display name of the agent (e.g., "Quill", "Macro Lens")

    Returns:
        Formatted string with [TOOL CALLS] section and analysis
    """
    tool_calls_log = []
    final_response = ""
    queue = get_streaming_queue()

    async for event in agent.astream(
        {"messages": [HumanMessage(content=query)]},
        stream_mode=["values", "updates"]
    ):
        if isinstance(event, tuple) and len(event) == 2:
            event_type, event_data = event

            # Collect tool call information and push to queue immediately
            if event_type == "updates":
                for node_name, node_output in event_data.items():
                    if node_name == "agent" and "messages" in node_output:
                        for msg in node_output["messages"]:
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    tool_name = tool_call.get("name", "unknown")
                                    tool_args = tool_call.get("args", {})
                                    tool_call_str = f"→ {tool_name}({tool_args})"
                                    tool_calls_log.append(tool_call_str)

                                    # Push event to queue for immediate TUI display
                                    if queue:
                                        try:
                                            await queue.put({
                                                "type": "tool_call",
                                                "agent": agent_name,
                                                "tool_name": tool_name,
                                                "args": tool_args,
                                            })
                                        except Exception:
                                            pass  # Don't break execution if queue fails

            # Capture final response
            elif event_type == "values":
                if "messages" in event_data and event_data["messages"]:
                    last_msg = event_data["messages"][-1]
                    if hasattr(last_msg, "content") and last_msg.content:
                        final_response = last_msg.content

    # Return response with tool call log prefix (for fallback/debugging)
    if tool_calls_log:
        log_str = "\n".join(tool_calls_log)
        return f"[TOOL CALLS]\n{log_str}\n\n[ANALYSIS]\n{final_response}"
    return final_response


# Agent tool wrappers
@tool
async def route_to_quill(query: str) -> str:
    """Route to Quill for fundamental equity analysis and investment thesis.

    Use when user asks about:
    - Company valuation, DCF analysis, fair value estimates
    - Investment recommendations (buy/sell/hold decisions)
    - Financial statement analysis, profitability trends
    - Investment thesis with catalysts and risks
    - SEC filings analysis (10-K, 10-Q)
    - Fundamental company research and deep dives

    Args:
        query: User's investment analysis question about a specific stock

    Returns:
        Quill's fundamental analysis and investment thesis (with tool call log)
    """
    try:
        agent = await _get_quill_agent()
        return await _stream_agent_with_tool_log(agent, query, "Quill")
    except Exception as e:
        return f"Error: Quill agent failed - {str(e)}"


@tool
async def route_to_screen_forge(query: str) -> str:
    """Route to Screen Forge for equity screening and stock discovery.

    Use when user asks about:
    - Finding stocks with specific criteria (P/E, growth, yield, etc.)
    - Screening for value, growth, dividend, or quality stocks
    - Factor-based stock discovery (momentum, size, value)
    - Generating investment idea shortlists
    - Identifying candidates for further research

    Args:
        query: User's stock screening or discovery question

    Returns:
        Screen Forge's screening results and candidate list
    """
    try:
        agent = await _get_screen_forge_agent()
        return await _stream_agent_with_tool_log(agent, query, "Screen Forge")
    except Exception as e:
        return f"Error: Screen Forge agent failed - {str(e)}"


@tool
async def route_to_macro_lens(query: str) -> str:
    """Route to Macro Lens for top-down market analysis and timing.

    Use when user asks about:
    - Market timing, economic regime assessment
    - Sector allocation recommendations
    - Macro risk scenarios and recession risk
    - Yield curve analysis, inflation trends
    - Factor exposure recommendations (value/growth, size)
    - Economic cycle positioning

    Args:
        query: User's macro or market timing question

    Returns:
        Macro Lens's top-down analysis and timing assessment
    """
    try:
        agent = await _get_macro_lens_agent()
        return await _stream_agent_with_tool_log(agent, query, "Macro Lens")
    except Exception as e:
        return f"Error: Macro Lens agent failed - {str(e)}"


@tool
async def route_to_earnings_whisperer(query: str) -> str:
    """Route to Earnings Whisperer for earnings analysis.

    Use when user asks about:
    - Earnings surprises, beats/misses
    - Post-earnings drift opportunities
    - Earnings calendar, upcoming reports
    - Analyst estimate revisions
    - Earnings quality and consistency
    - Earnings momentum patterns

    Args:
        query: User's earnings-related question

    Returns:
        Earnings Whisperer's earnings analysis
    """
    try:
        agent = await _get_earnings_whisperer_agent()
        return await _stream_agent_with_tool_log(agent, query, "Earnings Whisperer")
    except Exception as e:
        return f"Error: Earnings Whisperer agent failed - {str(e)}"


@tool
async def route_to_news_sentry(query: str) -> str:
    """Route to News Sentry for material event monitoring.

    Use when user asks about:
    - Breaking news, material events (8-K filings)
    - Insider trading activity (Form 4 filings)
    - Analyst rating changes
    - Corporate events (M&A, management changes, bankruptcy)
    - News sentiment analysis
    - Event-driven trading opportunities

    Args:
        query: User's news or event monitoring question

    Returns:
        News Sentry's event analysis and alerts
    """
    try:
        agent = await _get_news_sentry_agent()
        return await _stream_agent_with_tool_log(agent, query, "News Sentry")
    except Exception as e:
        return f"Error: News Sentry agent failed - {str(e)}"


@tool
async def route_to_risk_shield(query: str) -> str:
    """Route to Risk Shield for portfolio risk analysis.

    Use when user asks about:
    - Portfolio risk assessment, concentration analysis
    - VAR (Value at Risk) calculations
    - Drawdown analysis, maximum loss scenarios
    - Position sizing, limit breach detection
    - Risk mitigation strategies
    - Stress testing, scenario analysis

    Args:
        query: User's risk management question

    Returns:
        Risk Shield's risk analysis and mitigation recommendations
    """
    try:
        agent = await _get_risk_shield_agent()
        return await _stream_agent_with_tool_log(agent, query, "Risk Shield")
    except Exception as e:
        return f"Error: Risk Shield agent failed - {str(e)}"


@tool
async def route_to_tax_scout(query: str) -> str:
    """Route to Tax Scout for tax optimization and planning.

    Use when user asks about:
    - Tax-loss harvesting opportunities
    - Wash-sale rule compliance
    - Year-end tax planning
    - Capital gains/losses analysis
    - Tax-efficient rebalancing
    - Substitute securities for harvested losses

    Args:
        query: User's tax optimization question

    Returns:
        Tax Scout's tax optimization recommendations
    """
    try:
        agent = await _get_tax_scout_agent()
        return await _stream_agent_with_tool_log(agent, query, "Tax Scout")
    except Exception as e:
        return f"Error: Tax Scout agent failed - {str(e)}"


@tool
async def route_to_hedge_smith(query: str) -> str:
    """Route to Hedge Smith for options strategies.

    Use when user asks about:
    - Portfolio protection with options
    - Protective collar strategies
    - Covered call yield enhancement
    - Put protection analysis
    - Options Greeks (delta, gamma, theta, vega)
    - Strike selection and expiration optimization
    - Cash-secured puts

    Args:
        query: User's options strategy question

    Returns:
        Hedge Smith's options strategy recommendations
    """
    try:
        agent = await _get_hedge_smith_agent()
        return await _stream_agent_with_tool_log(agent, query, "Hedge Smith")
    except Exception as e:
        return f"Error: Hedge Smith agent failed - {str(e)}"


@tool
async def route_to_portfolio(query: str) -> str:
    """Route to Portfolio agent for general portfolio questions (fallback).

    Use when:
    - Query doesn't clearly match any specialist agent
    - General portfolio inquiries
    - Stock price lookups, basic company info
    - SEC filings access
    - Ambiguous or exploratory questions

    Args:
        query: User's general investment question

    Returns:
        Portfolio agent's general analysis
    """
    try:
        agent = await _get_portfolio_agent()
        return await _stream_agent_with_tool_log(agent, query, "Portfolio")
    except Exception as e:
        return f"Error: Portfolio agent failed - {str(e)}"


@tool
async def route_to_research(query: str) -> str:
    """Route to Research agent for macroeconomic indicators (fallback).

    Use when user asks about:
    - GDP, CPI, unemployment data
    - Treasury yields, yield curve
    - Federal Reserve policy
    - Economic indicators from FRED
    - General macro questions not requiring strategic recommendations

    Args:
        query: User's macroeconomic data question

    Returns:
        Research agent's macroeconomic data analysis
    """
    try:
        agent = await _get_research_agent()
        return await _stream_agent_with_tool_log(agent, query, "Research")
    except Exception as e:
        return f"Error: Research agent failed - {str(e)}"


async def create_router_agent():
    """Create router supervisor agent for intent-based routing.

    The router analyzes user queries and automatically routes to appropriate
    specialist agents. Supports:
    - Single-agent routing for focused queries
    - Multi-agent coordination for complex questions
    - Fallback handling for ambiguous queries
    - Transparent routing (explains which agents are used)

    Returns:
        Compiled router agent with all specialist agent tools
    """
    settings = get_settings()

    # Use a powerful model for routing decisions with low temperature for consistency
    supervisor_llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0.1,  # Low temperature for consistent intent classification
        max_tokens=8192,
    )

    # Bind system prompt directly to the model
    system_prompt = """You are an Investment Advisory Supervisor coordinating a team of 10 specialized AI agents.

Your role:
1. Understand the user's investment question and intent
2. Classify the query type (fundamental analysis, risk assessment, tax planning, etc.)
3. Select the appropriate specialist agent(s) to handle the query
4. For complex questions spanning multiple domains, you can call multiple agents
5. Synthesize results from multiple agents into coherent recommendations
6. Always explain which agent(s) you're using and why (transparency)

Available Specialist Agents:
- **Quill**: Fundamental equity analysis, investment thesis, valuation (DCF, comps), buy/sell/hold recommendations
- **Screen Forge**: Equity screening, factor-based stock discovery, shortlist generation
- **Macro Lens**: Top-down market analysis, sector allocation, regime assessment, timing
- **Earnings Whisperer**: Earnings analysis, surprises, post-earnings drift opportunities
- **News Sentry**: Material event monitoring, insider trading alerts, news filtering
- **Risk Shield**: Portfolio risk analysis, VAR, drawdown, concentration monitoring
- **Tax Scout**: Tax-loss harvesting, wash-sale compliance, year-end tax planning
- **Hedge Smith**: Options strategies, protective collars, covered calls, put protection
- **Portfolio**: General portfolio questions (fallback for ambiguous queries)
- **Research**: Macroeconomic indicators, FRED data (fallback for macro data queries)

Intent Classification Examples:
- "Should I buy AAPL?" → Use Quill (fundamentals), optionally Macro Lens (timing) and Risk Shield (exposure check)
- "Find undervalued growth stocks" → Use Screen Forge
- "Tax-loss harvest opportunities" → Use Tax Scout
- "Protect my NVDA position" → Use Hedge Smith
- "Is recession risk high?" → Use Macro Lens
- "TSLA earnings analysis" → Use Earnings Whisperer
- "Material events for META" → Use News Sentry
- "Portfolio risk assessment" → Use Risk Shield
- "What's AAPL's stock price?" → Use Portfolio (simple lookup)
- "What's the current GDP?" → Use Research (macro data)

Coordination Strategies:
- **Single-agent queries**: Route directly to the most appropriate specialist
- **Multi-faceted queries**: You can call 2-3 relevant agents and synthesize their responses
- **Ambiguous queries**: Route to Portfolio (general) or ask clarifying questions
- **Complex workflows**: Sequence agents if needed (e.g., Screen Forge results → Quill analysis)

Important Guidelines:
- Always explain which agent(s) you're routing to and why (e.g., "I'll route to Quill for fundamental analysis...")
- For investment decisions ("Should I buy X?"), consider using multiple agents: Quill for fundamentals + Macro Lens for timing
- Be transparent about your reasoning process
- If a query is ambiguous, either ask for clarification OR route to Portfolio as fallback
- Synthesize multi-agent responses into a coherent recommendation
- Keep responses focused and actionable

Remember: Your goal is to provide the best possible investment advice by intelligently coordinating specialist agents."""

    # Create supervisor with all agent tools and system prompt
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("placeholder", "{messages}"),
        ]
    )

    router = create_react_agent(
        model=supervisor_llm,
        tools=[
            route_to_quill,
            route_to_screen_forge,
            route_to_macro_lens,
            route_to_earnings_whisperer,
            route_to_news_sentry,
            route_to_risk_shield,
            route_to_tax_scout,
            route_to_hedge_smith,
            route_to_portfolio,  # Fallback
            route_to_research,  # Fallback
        ],
        prompt=prompt,
    )

    return router
