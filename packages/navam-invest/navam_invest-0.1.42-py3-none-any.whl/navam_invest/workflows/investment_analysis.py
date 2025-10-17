"""Investment Analysis Workflow - Comprehensive 5-agent sequential analysis.

This workflow coordinates five specialized agents to provide comprehensive investment analysis:
1. Quill (Equity Research) - Bottom-up fundamental analysis
2. News Sentry (Event Monitor) - Material events, insider trading, recent news
3. Macro Lens (Market Strategist) - Top-down macro validation and timing
4. Risk Shield (Risk Manager) - Portfolio fit, concentration risk, exposure analysis
5. Tax Scout (Tax Advisor) - Tax implications of buying/selling

The workflow combines all perspectives to deliver a complete investment recommendation.
"""

from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from navam_invest.config.settings import get_settings
from navam_invest.tools import bind_api_keys_to_tools, get_tools_for_agent


class InvestmentAnalysisState(TypedDict):
    """State for investment analysis workflow.

    This state is shared across all agents in the sequential workflow,
    allowing each agent to see prior analyses when providing their perspective.
    """

    messages: Annotated[list, add_messages]
    symbol: str  # Stock symbol being analyzed
    quill_analysis: str  # Results from Quill's fundamental analysis
    news_events: str  # Results from News Sentry's event monitoring
    macro_context: str  # Results from Macro Lens's regime analysis
    risk_assessment: str  # Results from Risk Shield's risk analysis
    tax_implications: str  # Results from Tax Scout's tax analysis


async def create_investment_analysis_workflow() -> StateGraph:
    """Create a sequential multi-agent workflow for comprehensive investment analysis.

    Workflow sequence:
    1. User provides symbol via /analyze command
    2. Quill analyzes fundamentals and provides investment thesis
    3. News Sentry checks for material events, insider trading, recent news
    4. Macro Lens assesses macro regime and validates timing
    5. Risk Shield evaluates portfolio fit and concentration risk
    6. Tax Scout analyzes tax implications of buying/selling
    7. Synthesis combines all perspectives into final recommendation

    Returns:
        Compiled LangGraph workflow
    """
    settings = get_settings()

    # Initialize LLM
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=settings.temperature,
        max_tokens=8192,  # Ensure full responses without truncation
    )

    # Get tools for each agent
    quill_tools = get_tools_for_agent("quill")
    news_sentry_tools = get_tools_for_agent("news_sentry")
    macro_tools = get_tools_for_agent("macro_lens")
    risk_shield_tools = get_tools_for_agent("risk_shield")
    tax_scout_tools = get_tools_for_agent("tax_scout")

    # Bind API keys to tools
    quill_tools_with_keys = bind_api_keys_to_tools(
        quill_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        finnhub_key=settings.finnhub_api_key or "",
        tiingo_key=settings.tiingo_api_key or "",
        newsapi_key=settings.newsapi_api_key or "",
    )

    news_sentry_tools_with_keys = bind_api_keys_to_tools(
        news_sentry_tools,
        finnhub_key=settings.finnhub_api_key or "",
        newsapi_key=settings.newsapi_api_key or "",
    )

    macro_tools_with_keys = bind_api_keys_to_tools(
        macro_tools,
        fred_key=settings.fred_api_key or "",
        newsapi_key=settings.newsapi_api_key or "",
    )

    risk_shield_tools_with_keys = bind_api_keys_to_tools(
        risk_shield_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
    )

    tax_scout_tools_with_keys = bind_api_keys_to_tools(
        tax_scout_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
    )

    # Agent 1: Quill - Fundamental Analysis
    async def quill_agent(state: InvestmentAnalysisState) -> dict:
        """Quill performs bottom-up fundamental analysis."""
        symbol = state["symbol"]

        system_prompt = f"""You are Quill, an expert equity research analyst. Analyze {symbol} and provide a comprehensive investment thesis.

Your analysis should include:
1. **Business Overview**: What does the company do? Competitive position?
2. **Financial Health**: Revenue growth, profitability, cash flow trends (5-year view if available)
3. **Valuation**: Is the stock fairly valued? P/E, P/B, DCF-based fair value estimate
4. **Investment Thesis**: Bull case, bear case, key catalysts
5. **Recommendation**: BUY/HOLD/SELL with confidence level

Focus on **fundamental quality** and **long-term value**. Use all available tools to gather data.

Format your response as a concise investment thesis (3-4 paragraphs) that will be combined with macro analysis."""

        # Bind tools and system prompt to LLM
        quill_llm = llm.bind_tools(quill_tools_with_keys).bind(system=system_prompt)

        response = await quill_llm.ainvoke(state["messages"])

        # Store Quill's analysis in state for Macro Lens to reference
        analysis_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "quill_analysis": analysis_text,
        }

    # Agent 2: News Sentry - Event Monitoring
    async def news_sentry_agent(state: InvestmentAnalysisState) -> dict:
        """News Sentry checks for material events and recent news."""
        symbol = state["symbol"]
        quill_analysis = state.get("quill_analysis", "")

        system_prompt = f"""You are News Sentry, an expert event detection analyst. You've received a fundamental analysis of {symbol} from Quill.

**Quill's Analysis**:
{quill_analysis}

Your task: Check for **material events and recent news** that could impact the investment thesis:
1. **8-K Filings**: Any material events filed recently (M&A, management changes, bankruptcy)?
2. **Insider Trading**: Recent Form 4 filings showing insider buying/selling?
3. **Breaking News**: Recent news or announcements affecting {symbol}?
4. **Analyst Actions**: Upgrades, downgrades, price target changes?

Provide a **news check** (2-3 paragraphs) that either:
- ✅ **Confirms thesis**: "No material negative events. Recent news supports..."
- ⚠️ **Requires attention**: "Recent insider selling warrants monitoring..."
- ❌ **Contradicts thesis**: "Material 8-K filing reveals..."

Use 8-K monitoring, Form 4 checks, and news analysis tools."""

        # Bind tools and system prompt to LLM
        news_llm = llm.bind_tools(news_sentry_tools_with_keys).bind(system=system_prompt)

        response = await news_llm.ainvoke(state["messages"])

        news_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "news_events": news_text,
        }

    # Agent 3: Macro Lens - Macro Validation
    async def macro_lens_agent(state: InvestmentAnalysisState) -> dict:
        """Macro Lens validates timing based on macro regime."""
        symbol = state["symbol"]
        quill_analysis = state.get("quill_analysis", "")
        news_events = state.get("news_events", "")

        system_prompt = f"""You are Macro Lens, an expert market strategist. You've received analyses of {symbol} from previous agents.

**Quill's Analysis**:
{quill_analysis}

**News Sentry's Check**:
{news_events}

Your task: Assess whether **NOW is the right time** to invest in {symbol} based on:
1. **Current Macro Regime**: What economic cycle phase are we in?
2. **Sector Positioning**: How does {symbol}'s sector perform in this regime?
3. **Timing Assessment**: Is this a good entry point given macro conditions?
4. **Risk Factors**: What macro risks could derail the investment thesis?

Provide a **macro validation** (2-3 paragraphs) that either:
- ✅ **Confirms timing**: "Macro conditions support this investment because..."
- ⚠️ **Suggests caution**: "Wait for better entry point because..."
- ❌ **Contradicts thesis**: "Macro headwinds make this risky because..."

Use treasury yield curve, economic indicators, and current regime analysis."""

        # Bind tools and system prompt to LLM
        macro_llm = llm.bind_tools(macro_tools_with_keys).bind(system=system_prompt)

        response = await macro_llm.ainvoke(state["messages"])

        macro_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "macro_context": macro_text,
        }

    # Agent 4: Risk Shield - Risk Assessment
    async def risk_shield_agent(state: InvestmentAnalysisState) -> dict:
        """Risk Shield evaluates portfolio fit and concentration risk."""
        symbol = state["symbol"]
        quill_analysis = state.get("quill_analysis", "")
        news_events = state.get("news_events", "")
        macro_context = state.get("macro_context", "")

        system_prompt = f"""You are Risk Shield, an expert risk management analyst. You've received analyses of {symbol} from previous agents.

**Quill's Analysis**:
{quill_analysis}

**News Sentry's Check**:
{news_events}

**Macro Lens's Context**:
{macro_context}

Your task: Assess **portfolio fit and risk exposure** for investing in {symbol}:
1. **Concentration Risk**: Would adding {symbol} increase sector/stock concentration?
2. **Volatility Assessment**: Historical volatility and drawdown risk?
3. **Portfolio Fit**: Does this match portfolio risk tolerance?
4. **Exposure Check**: What is the appropriate position size given risk?

Provide a **risk assessment** (2-3 paragraphs) covering:
- ✅ **Acceptable risk**: "Position size of X% fits portfolio risk profile..."
- ⚠️ **Moderate concern**: "Concentration in tech warrants limiting exposure..."
- ❌ **High risk**: "Volatility and correlation suggest avoiding or hedging..."

Use volatility analysis and correlation tools."""

        # Bind tools and system prompt to LLM
        risk_llm = llm.bind_tools(risk_shield_tools_with_keys).bind(system=system_prompt)

        response = await risk_llm.ainvoke(state["messages"])

        risk_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "risk_assessment": risk_text,
        }

    # Agent 5: Tax Scout - Tax Implications
    async def tax_scout_agent(state: InvestmentAnalysisState) -> dict:
        """Tax Scout analyzes tax implications of buying or selling."""
        symbol = state["symbol"]
        quill_analysis = state.get("quill_analysis", "")
        risk_assessment = state.get("risk_assessment", "")

        system_prompt = f"""You are Tax Scout, an expert tax optimization analyst. You've received analyses of {symbol} from previous agents.

**Quill's Analysis**:
{quill_analysis}

**Risk Shield's Assessment**:
{risk_assessment}

Your task: Analyze **tax implications** of investing in {symbol}:
1. **Capital Gains**: If buying, when to sell for long-term gains?
2. **Tax-Loss Harvesting**: Any current losers to sell before buying {symbol}?
3. **Wash Sale Risk**: Check 30-day windows for wash sale violations
4. **Tax Efficiency**: Is now tax-efficient timing for this investment?

Provide a **tax assessment** (2 paragraphs) covering:
- ✅ **Tax-efficient**: "No wash sale concerns. Buying now allows long-term gains by..."
- ⚠️ **Timing consideration**: "Wait 30 days to avoid wash sale on XYZ position..."
- ❌ **Tax inefficient**: "Year-end approaching - defer to January for better tax treatment..."

Focus on practical tax optimization advice."""

        # Bind tools and system prompt to LLM
        tax_llm = llm.bind_tools(tax_scout_tools_with_keys).bind(system=system_prompt)

        response = await tax_llm.ainvoke(state["messages"])

        tax_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "tax_implications": tax_text,
        }

    # Synthesis: Combine all five analyses
    async def synthesize_recommendation(state: InvestmentAnalysisState) -> dict:
        """Combine all agent analyses into final comprehensive recommendation."""
        symbol = state["symbol"]
        quill_analysis = state.get("quill_analysis", "No fundamental analysis available")
        news_events = state.get("news_events", "No news check available")
        macro_context = state.get("macro_context", "No macro analysis available")
        risk_assessment = state.get("risk_assessment", "No risk assessment available")
        tax_implications = state.get("tax_implications", "No tax analysis available")

        synthesis_prompt = f"""Synthesize the following comprehensive analyses for {symbol} into a final investment recommendation:

**FUNDAMENTAL ANALYSIS (Quill)**:
{quill_analysis}

**NEWS & EVENTS CHECK (News Sentry)**:
{news_events}

**MACRO VALIDATION (Macro Lens)**:
{macro_context}

**RISK ASSESSMENT (Risk Shield)**:
{risk_assessment}

**TAX IMPLICATIONS (Tax Scout)**:
{tax_implications}

Provide a **final recommendation** with:
1. **Overall Rating**: BUY / HOLD / SELL (with confidence: High/Medium/Low)
2. **Key Reasoning**: 2-3 sentences combining both fundamental and macro perspectives
3. **Suggested Action**: What should an investor do right now?
4. **Risk Warning**: Most important risk to monitor

Keep it concise (4-5 sentences total)."""

        synthesis_msg = HumanMessage(content=synthesis_prompt)
        final_response = await llm.ainvoke([synthesis_msg])

        return {"messages": [final_response]}

    # Build the sequential workflow graph
    workflow = StateGraph(InvestmentAnalysisState)

    # Add agent nodes
    workflow.add_node("quill", quill_agent)
    workflow.add_node("news_sentry", news_sentry_agent)
    workflow.add_node("macro_lens", macro_lens_agent)
    workflow.add_node("risk_shield", risk_shield_agent)
    workflow.add_node("tax_scout", tax_scout_agent)
    workflow.add_node("synthesize", synthesize_recommendation)

    # Add tool execution nodes
    workflow.add_node("quill_tools", ToolNode(quill_tools_with_keys))
    workflow.add_node("news_sentry_tools", ToolNode(news_sentry_tools_with_keys))
    workflow.add_node("macro_tools", ToolNode(macro_tools_with_keys))
    workflow.add_node("risk_shield_tools", ToolNode(risk_shield_tools_with_keys))
    workflow.add_node("tax_scout_tools", ToolNode(tax_scout_tools_with_keys))

    # Helper functions to check if tools were called
    def quill_should_continue(state: InvestmentAnalysisState) -> str:
        """Check if Quill made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "quill_tools"
        return "news_sentry"

    def news_sentry_should_continue(state: InvestmentAnalysisState) -> str:
        """Check if News Sentry made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "news_sentry_tools"
        return "macro_lens"

    def macro_should_continue(state: InvestmentAnalysisState) -> str:
        """Check if Macro Lens made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "macro_tools"
        return "risk_shield"

    def risk_shield_should_continue(state: InvestmentAnalysisState) -> str:
        """Check if Risk Shield made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "risk_shield_tools"
        return "tax_scout"

    def tax_scout_should_continue(state: InvestmentAnalysisState) -> str:
        """Check if Tax Scout made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tax_scout_tools"
        return "synthesize"

    # Define the workflow with tool execution loops
    # Quill → News Sentry → Macro Lens → Risk Shield → Tax Scout → Synthesis

    workflow.add_edge(START, "quill")
    workflow.add_conditional_edges(
        "quill",
        quill_should_continue,
        {"quill_tools": "quill_tools", "news_sentry": "news_sentry"}
    )
    workflow.add_edge("quill_tools", "quill")  # Loop back after tool execution

    workflow.add_conditional_edges(
        "news_sentry",
        news_sentry_should_continue,
        {"news_sentry_tools": "news_sentry_tools", "macro_lens": "macro_lens"}
    )
    workflow.add_edge("news_sentry_tools", "news_sentry")

    workflow.add_conditional_edges(
        "macro_lens",
        macro_should_continue,
        {"macro_tools": "macro_tools", "risk_shield": "risk_shield"}
    )
    workflow.add_edge("macro_tools", "macro_lens")

    workflow.add_conditional_edges(
        "risk_shield",
        risk_shield_should_continue,
        {"risk_shield_tools": "risk_shield_tools", "tax_scout": "tax_scout"}
    )
    workflow.add_edge("risk_shield_tools", "risk_shield")

    workflow.add_conditional_edges(
        "tax_scout",
        tax_scout_should_continue,
        {"tax_scout_tools": "tax_scout_tools", "synthesize": "synthesize"}
    )
    workflow.add_edge("tax_scout_tools", "tax_scout")

    workflow.add_edge("synthesize", END)

    return workflow.compile()
