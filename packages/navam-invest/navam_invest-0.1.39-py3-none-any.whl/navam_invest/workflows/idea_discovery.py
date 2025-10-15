"""Idea Discovery Workflow - Systematic investment idea generation.

This workflow coordinates three specialized agents to generate and validate investment ideas:
1. Screen Forge (Equity Screener) - Systematic stock screening with factor-based filters
2. Quill (Equity Research) - Deep fundamental analysis on top candidates
3. Risk Shield (Risk Manager) - Portfolio fit and concentration risk assessment

The workflow provides a complete pipeline from systematic screening to validated investment ideas.
"""

from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from navam_invest.config.settings import get_settings
from navam_invest.tools import bind_api_keys_to_tools, get_tools_for_agent


class IdeaDiscoveryState(TypedDict):
    """State for idea discovery workflow.

    This state is shared across all agents in the sequential workflow,
    allowing each agent to see prior analyses when providing their perspective.
    """

    messages: Annotated[list, add_messages]
    screening_criteria: str  # User's screening criteria or preferences
    screen_results: str  # Results from Screen Forge's screening
    fundamental_analysis: str  # Results from Quill's analysis of top candidates
    risk_assessment: str  # Results from Risk Shield's portfolio fit analysis


async def create_idea_discovery_workflow() -> StateGraph:
    """Create a sequential multi-agent workflow for systematic idea generation.

    Workflow sequence:
    1. User provides screening criteria via /discover command
    2. Screen Forge performs systematic screening and identifies top candidates
    3. Quill analyzes fundamentals of top 3-5 candidates with investment thesis
    4. Risk Shield assesses portfolio fit and concentration risk for each candidate
    5. Synthesis combines all perspectives into final ranked recommendations

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
    screen_forge_tools = get_tools_for_agent("screen_forge")
    quill_tools = get_tools_for_agent("quill")
    risk_shield_tools = get_tools_for_agent("risk_shield")

    # Bind API keys to tools
    screen_forge_tools_with_keys = bind_api_keys_to_tools(
        screen_forge_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        finnhub_key=settings.finnhub_api_key or "",
    )

    quill_tools_with_keys = bind_api_keys_to_tools(
        quill_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        finnhub_key=settings.finnhub_api_key or "",
        tiingo_key=settings.tiingo_api_key or "",
        newsapi_key=settings.newsapi_api_key or "",
    )

    risk_shield_tools_with_keys = bind_api_keys_to_tools(
        risk_shield_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
    )

    # Agent 1: Screen Forge - Systematic Screening
    async def screen_forge_agent(state: IdeaDiscoveryState) -> dict:
        """Screen Forge performs systematic equity screening."""
        criteria = state.get("screening_criteria", "")

        system_prompt = f"""You are Screen Forge, an expert equity screener specializing in systematic stock discovery.

User's screening criteria: {criteria if criteria else "Generate a balanced watchlist of quality growth stocks"}

Your task: Perform systematic screening to identify **10-15 high-quality investment candidates** that match the criteria.

**Screening Framework:**
1. **Factor Analysis**: Apply value, growth, quality, and momentum filters
2. **Quantitative Filters**: Market cap >$1B, positive earnings, adequate liquidity
3. **Ranking System**: Score candidates on multiple factors and rank them
4. **Output Format**: Provide top 10-15 ranked candidates with key metrics

**Output Requirements:**
- List candidates with ticker, company name, and 1-2 standout metrics
- Rank candidates by screening score (1 = best)
- For top 5 candidates, provide brief rationale (2-3 sentences each)
- Suggest which 3-5 candidates warrant deep fundamental analysis

**Example Output Format:**
```
RANKED CANDIDATES (Top 15):

1. TICKER - Company Name | Score: 8.5/10
   P/E: 15.2, Revenue Growth: 25%, ROE: 18%, Margin: 12%
   Standout: Strong revenue growth with expanding margins

[... more candidates ...]

TOP 3 FOR DEEP DIVE:
1. TICKER1 - Exceptional growth with reasonable valuation
2. TICKER2 - Quality business with improving fundamentals
3. TICKER3 - Undervalued with strong balance sheet
```

Use all available screening and fundamental tools to identify high-quality candidates."""

        # Bind tools and system prompt to LLM
        screen_llm = llm.bind_tools(screen_forge_tools_with_keys).bind(
            system=system_prompt
        )

        response = await screen_llm.ainvoke(state["messages"])

        # Store Screen Forge's results in state for Quill to reference
        results_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "screen_results": results_text,
        }

    # Agent 2: Quill - Fundamental Analysis of Top Candidates
    async def quill_agent(state: IdeaDiscoveryState) -> dict:
        """Quill performs deep fundamental analysis on top candidates."""
        screen_results = state.get("screen_results", "")

        system_prompt = f"""You are Quill, an expert equity research analyst. You've received a ranked list of investment candidates from Screen Forge.

**Screen Forge's Results**:
{screen_results}

Your task: Perform **deep fundamental analysis** on the **top 3-5 candidates** identified by Screen Forge.

For each candidate, provide:
1. **Business Overview**: What does the company do? Competitive position?
2. **Financial Health**: Revenue/earnings trends, profitability, cash flow (focus on most recent data)
3. **Valuation**: Is the stock fairly valued? P/E, P/B, relative valuation vs peers
4. **Investment Thesis**: Bull case, bear case, key catalysts (2-3 paragraphs)
5. **Recommendation**: BUY/HOLD/SELL with confidence level (High/Medium/Low)

**Output Format (Per Candidate)**:
```
CANDIDATE 1: TICKER - Company Name

Business: [1-2 sentences on what they do and competitive position]

Financials:
- Revenue: $XXM (YoY growth: X%)
- Earnings: $X.XX EPS (YoY growth: X%)
- Margins: Gross X%, Operating X%, Net X%
- Cash Flow: $XXM FCF, X% FCF margin

Valuation:
- P/E: XX.X (Industry avg: XX.X)
- P/B: X.X
- Fair Value Estimate: $XX (Current: $XX, Upside: X%)

Investment Thesis:
[2-3 paragraphs covering bull/bear case, catalysts, risks]

Recommendation: BUY/HOLD/SELL | Confidence: High/Medium/Low
```

Focus on **quality of analysis** over quantity. Provide thorough research for top 3-5 picks."""

        # Bind tools and system prompt to LLM
        quill_llm = llm.bind_tools(quill_tools_with_keys).bind(system=system_prompt)

        response = await quill_llm.ainvoke(state["messages"])

        # Store Quill's analysis in state for Risk Shield to reference
        analysis_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "fundamental_analysis": analysis_text,
        }

    # Agent 3: Risk Shield - Portfolio Fit Assessment
    async def risk_shield_agent(state: IdeaDiscoveryState) -> dict:
        """Risk Shield assesses portfolio fit and concentration risk."""
        screen_results = state.get("screen_results", "")
        fundamental_analysis = state.get("fundamental_analysis", "")

        system_prompt = f"""You are Risk Shield, an expert risk management analyst. You've received screening results and fundamental analysis from previous agents.

**Screen Forge's Results**:
{screen_results}

**Quill's Analysis**:
{fundamental_analysis}

Your task: Assess **portfolio fit and risk** for the top candidates analyzed by Quill.

For each candidate, evaluate:
1. **Volatility Assessment**: Historical volatility (30-day, 90-day), beta, max drawdown
2. **Correlation Analysis**: How does this correlate with existing portfolio holdings?
3. **Concentration Risk**: Would adding this position increase sector/stock concentration?
4. **Position Sizing**: Recommended position size (% of portfolio) given risk profile
5. **Risk/Reward**: Expected return vs volatility profile

**Output Format (Per Candidate)**:
```
RISK ASSESSMENT: TICKER - Company Name

Volatility:
- 30-day volatility: X%
- 90-day volatility: X%
- Beta: X.X (vs S&P 500)
- Max drawdown (1Y): -X%

Portfolio Fit:
- Correlation with portfolio: X.X (low/medium/high)
- Sector concentration impact: [Assessment]
- Diversification benefit: Yes/No/Neutral

Position Sizing:
- Conservative allocation: X% of portfolio
- Moderate allocation: X% of portfolio
- Aggressive allocation: X% of portfolio
- Recommended: X% (based on risk tolerance)

Risk Rating: Low/Medium/High | Risk/Reward: Favorable/Neutral/Unfavorable
```

Provide **practical risk guidance** to help with position sizing decisions."""

        # Bind tools and system prompt to LLM
        risk_llm = llm.bind_tools(risk_shield_tools_with_keys).bind(system=system_prompt)

        response = await risk_llm.ainvoke(state["messages"])

        # Store Risk Shield's assessment in state for synthesis
        risk_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "risk_assessment": risk_text,
        }

    # Synthesis: Combine all three analyses into ranked recommendations
    async def synthesize_recommendations(state: IdeaDiscoveryState) -> dict:
        """Combine all agent analyses into final ranked investment recommendations."""
        criteria = state.get("screening_criteria", "User's investment criteria")
        screen_results = state.get("screen_results", "No screening results available")
        fundamental_analysis = state.get(
            "fundamental_analysis", "No fundamental analysis available"
        )
        risk_assessment = state.get("risk_assessment", "No risk assessment available")

        synthesis_prompt = f"""Synthesize the following systematic idea discovery analyses into a final ranked watchlist:

**SCREENING CRITERIA**:
{criteria}

**SCREENING RESULTS (Screen Forge)**:
{screen_results}

**FUNDAMENTAL ANALYSIS (Quill)**:
{fundamental_analysis}

**RISK ASSESSMENT (Risk Shield)**:
{risk_assessment}

Provide **FINAL RANKED RECOMMENDATIONS** with:

1. **Top 3 Investment Ideas** (Ranked 1-3):
   - Ticker, company name, current price
   - One-sentence investment thesis
   - Key catalyst (near-term driver)
   - Recommended position size (% of portfolio)
   - Entry price target (or "current prices attractive")
   - Risk rating: Low/Medium/High

2. **Action Steps**:
   - Which positions to initiate now vs monitor
   - Any additional research needed before investing
   - Timeline for portfolio deployment

3. **Portfolio Impact Summary**:
   - Expected portfolio diversification benefit
   - Sector allocation impact
   - Overall risk/return profile change

**Format Example**:
```
FINAL RANKED RECOMMENDATIONS

1. TICKER - Company Name | $XX.XX | BUY
   Thesis: [One sentence investment case]
   Catalyst: [Near-term catalyst]
   Position Size: X% | Entry Target: $XX | Risk: Medium

[... 2 more recommendations ...]

ACTION STEPS:
- Initiate positions in TICKER1 and TICKER2 at current prices
- Monitor TICKER3 for pullback to $XX entry point
- Set position size limits: X% max per holding

PORTFOLIO IMPACT:
- Adds X% to tech sector allocation
- Expected portfolio volatility: +/-X% (acceptable)
- Diversification: Positive (low correlation with existing holdings)
```

Keep it actionable and concise (6-8 sentences total)."""

        synthesis_msg = HumanMessage(content=synthesis_prompt)
        final_response = await llm.ainvoke([synthesis_msg])

        return {"messages": [final_response]}

    # Build the sequential workflow graph
    workflow = StateGraph(IdeaDiscoveryState)

    # Add agent nodes
    workflow.add_node("screen_forge", screen_forge_agent)
    workflow.add_node("quill", quill_agent)
    workflow.add_node("risk_shield", risk_shield_agent)
    workflow.add_node("synthesize", synthesize_recommendations)

    # Add tool execution nodes
    workflow.add_node("screen_forge_tools", ToolNode(screen_forge_tools_with_keys))
    workflow.add_node("quill_tools", ToolNode(quill_tools_with_keys))
    workflow.add_node("risk_shield_tools", ToolNode(risk_shield_tools_with_keys))

    # Helper functions to check if tools were called
    def screen_forge_should_continue(state: IdeaDiscoveryState) -> str:
        """Check if Screen Forge made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "screen_forge_tools"
        return "quill"

    def quill_should_continue(state: IdeaDiscoveryState) -> str:
        """Check if Quill made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "quill_tools"
        return "risk_shield"

    def risk_shield_should_continue(state: IdeaDiscoveryState) -> str:
        """Check if Risk Shield made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "risk_shield_tools"
        return "synthesize"

    # Define the workflow with tool execution loops
    # Screen Forge → Quill → Risk Shield → Synthesis

    workflow.add_edge(START, "screen_forge")
    workflow.add_conditional_edges(
        "screen_forge",
        screen_forge_should_continue,
        {"screen_forge_tools": "screen_forge_tools", "quill": "quill"},
    )
    workflow.add_edge("screen_forge_tools", "screen_forge")  # Loop back after tool execution

    workflow.add_conditional_edges(
        "quill",
        quill_should_continue,
        {"quill_tools": "quill_tools", "risk_shield": "risk_shield"},
    )
    workflow.add_edge("quill_tools", "quill")

    workflow.add_conditional_edges(
        "risk_shield",
        risk_shield_should_continue,
        {"risk_shield_tools": "risk_shield_tools", "synthesize": "synthesize"},
    )
    workflow.add_edge("risk_shield_tools", "risk_shield")

    workflow.add_edge("synthesize", END)

    return workflow.compile()
