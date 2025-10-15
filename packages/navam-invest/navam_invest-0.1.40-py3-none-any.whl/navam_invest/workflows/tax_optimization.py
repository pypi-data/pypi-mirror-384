"""Tax Optimization Workflow - Tax-loss harvesting with compliant replacement strategies.

This workflow coordinates two specialized agents to optimize portfolio tax efficiency:
1. Tax Scout (Tax Optimizer) - Identifies tax-loss harvesting opportunities with wash-sale compliance
2. Hedge Smith (Options Strategist) - Designs strategies to maintain exposure during wash-sale window

The workflow provides a complete pipeline from tax-loss identification to compliant replacement strategies.
"""

from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from navam_invest.config.settings import get_settings
from navam_invest.tools import bind_api_keys_to_tools, get_tools_for_agent


class TaxOptimizationState(TypedDict):
    """State for tax optimization workflow.

    This state is shared across all agents in the sequential workflow,
    allowing each agent to see prior analyses when providing their perspective.
    """

    messages: Annotated[list, add_messages]
    portfolio_context: str  # User's portfolio holdings and cost basis information
    tax_loss_opportunities: str  # Results from Tax Scout's analysis
    replacement_strategies: str  # Results from Hedge Smith's strategy design


async def create_tax_optimization_workflow() -> StateGraph:
    """Create a sequential multi-agent workflow for tax-loss harvesting.

    Workflow sequence:
    1. User provides portfolio holdings (or file path) via /optimize-tax command
    2. Tax Scout identifies tax-loss harvesting opportunities and wash-sale compliance
    3. Hedge Smith designs replacement strategies to maintain exposure during wash-sale window
    4. Synthesis combines both perspectives into actionable tax optimization plan

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
    tax_scout_tools = get_tools_for_agent("tax_scout")
    hedge_smith_tools = get_tools_for_agent("hedge_smith")

    # Bind API keys to tools
    tax_scout_tools_with_keys = bind_api_keys_to_tools(
        tax_scout_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        newsapi_key=settings.newsapi_api_key or "",
    )

    hedge_smith_tools_with_keys = bind_api_keys_to_tools(
        hedge_smith_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
    )

    # Agent 1: Tax Scout - Tax-Loss Harvesting Analysis
    async def tax_scout_agent(state: TaxOptimizationState) -> dict:
        """Tax Scout identifies tax-loss harvesting opportunities."""
        portfolio_context = state.get("portfolio_context", "")

        system_prompt = f"""You are Tax Scout, an expert tax optimization analyst specializing in tax-loss harvesting strategies.

User's portfolio context: {portfolio_context if portfolio_context else "Analyze user's current holdings for tax-loss harvesting opportunities"}

Your task: Identify **tax-loss harvesting opportunities** in the user's portfolio while ensuring **wash-sale rule compliance**.

**Tax-Loss Harvesting Framework:**
1. **Unrealized Loss Identification**: Find positions trading below cost basis (>5% loss threshold recommended)
2. **Holding Period Analysis**: Check if positions held >30 days (short-term vs long-term capital gains)
3. **Wash-Sale Window Check**: Verify no purchases 30 days before or after potential sale
4. **Tax Impact Calculation**: Estimate tax savings from harvesting losses (consider user's tax bracket if known)
5. **Replacement Strategy Needs**: Identify positions where user wants to maintain market exposure

**Output Requirements:**
- List all positions with unrealized losses >5%
- Calculate potential tax savings for each position
- Flag any wash-sale violations if positions were recently purchased
- Identify positions where user should maintain exposure (require replacement strategy)
- Suggest optimal timing for tax-loss harvesting (year-end vs immediate)

**Example Output Format:**
```
TAX-LOSS HARVESTING OPPORTUNITIES:

1. TICKER - Company Name
   Current Price: $XX.XX | Cost Basis: $XX.XX | Unrealized Loss: -$X,XXX (-XX%)
   Holding Period: XX days (Short-term/Long-term)
   Wash-Sale Risk: None / WARN: Recently purchased on [date]
   Tax Savings Estimate: $XXX (assuming XX% tax bracket)
   Maintain Exposure? Yes/No

[... more opportunities ...]

RECOMMENDED ACTIONS:
- Immediate harvest: [tickers with no wash-sale risk, significant losses]
- Year-end harvest: [tickers with smaller losses, optimize for tax year]
- Avoid: [tickers with wash-sale violations]

POSITIONS REQUIRING REPLACEMENT STRATEGY:
- TICKER1: Maintain exposure to [sector/theme], need 31-day substitute
- TICKER2: Core holding, consider options strategy during wash-sale window
```

**Compliance Notes:**
- Wash-sale rule: Cannot buy "substantially identical" security 30 days before/after sale
- Substantially identical: Same stock, options on same stock, convertible bonds
- Non-identical alternatives: Different company in same sector, sector ETFs, index funds
- Options strategy: Can maintain exposure using options during 31-day window

Use all available market data and portfolio analysis tools to identify opportunities."""

        # Bind tools and system prompt to LLM
        tax_llm = llm.bind_tools(tax_scout_tools_with_keys).bind(system=system_prompt)

        response = await tax_llm.ainvoke(state["messages"])

        # Store Tax Scout's results in state for Hedge Smith to reference
        results_text = response.content if hasattr(response, "content") else str(
            response
        )

        return {
            "messages": [response],
            "tax_loss_opportunities": results_text,
        }

    # Agent 2: Hedge Smith - Replacement Strategy Design
    async def hedge_smith_agent(state: TaxOptimizationState) -> dict:
        """Hedge Smith designs strategies to maintain exposure during wash-sale window."""
        portfolio_context = state.get("portfolio_context", "")
        tax_loss_opportunities = state.get("tax_loss_opportunities", "")

        system_prompt = f"""You are Hedge Smith, an expert options strategist specializing in tax-efficient portfolio management.

**Portfolio Context:**
{portfolio_context}

**Tax Scout's Analysis:**
{tax_loss_opportunities}

Your task: Design **wash-sale compliant replacement strategies** for positions that Tax Scout identified as requiring maintained exposure.

For each position requiring replacement, provide:

**Strategy Options:**

1. **Sector ETF Substitute** (Simplest):
   - Recommended sector ETF ticker
   - Correlation with sold position (target: 0.7-0.9, not "substantially identical")
   - Holding period: Maintain for 31 days minimum
   - Expected tracking vs original position

2. **Synthetic Long via Options** (Most precise):
   - Strategy: Long call + short put at same strike (synthetic stock)
   - Recommended strikes and expirations (minimum 31 days out)
   - Cost vs holding original stock
   - Delta exposure (target: ~1.0 to match stock)
   - Greeks analysis (theta decay, vega risk)

3. **Protective Strategy** (If high conviction):
   - If stock expected to rebound, use protective put instead of selling
   - Calculate break-even vs tax-loss harvesting benefit
   - Compare: harvest loss now vs wait for recovery

**Output Format (Per Position)**:
```
REPLACEMENT STRATEGY: TICKER - Company Name
Original Position: XXX shares @ $XX.XX cost basis
Tax-Loss Opportunity: -$X,XXX loss available to harvest

RECOMMENDED STRATEGY: [Sector ETF / Synthetic Long / Wait]

Option 1: Sector ETF Substitute
- Ticker: [ETF symbol] - [ETF name]
- Correlation: 0.XX (wash-sale compliant)
- Investment: $X,XXX (match original position size)
- Hold for: 31+ days, then repurchase [TICKER] if desired
- Tracking: Expected X% correlation during hold period

Option 2: Synthetic Long (Options)
- Buy [X] call contracts @ $XX strike, [expiration]
- Sell [X] put contracts @ $XX strike, [expiration]
- Net cost: $X,XXX (compare to original position)
- Delta: ~1.0 (matches stock exposure)
- Greeks: Theta -$XX/day, Vega $XX per 1% IV change
- Expiration: [Date] - allows repurchase of stock after 31 days

Option 3: Tax Efficiency Analysis
- Harvest loss now: Save $XXX in taxes this year
- Wait for recovery: Potential $XXX gain if rebounds XX%
- Recommendation: [Harvest / Wait] based on [reasoning]

RECOMMENDATION: [Specific strategy] for [reason]
```

**Design Principles:**
- Maintain similar market exposure (beta, sector, volatility)
- Minimize cost and complexity
- Ensure wash-sale compliance (>30 days, not substantially identical)
- Consider user's tax situation and market outlook

Provide **practical, actionable strategies** that balance tax efficiency with portfolio objectives."""

        # Bind tools and system prompt to LLM
        hedge_llm = llm.bind_tools(hedge_smith_tools_with_keys).bind(
            system=system_prompt
        )

        response = await hedge_llm.ainvoke(state["messages"])

        # Store Hedge Smith's strategies in state for synthesis
        strategy_text = response.content if hasattr(response, "content") else str(
            response
        )

        return {
            "messages": [response],
            "replacement_strategies": strategy_text,
        }

    # Synthesis: Combine tax analysis + replacement strategies into actionable plan
    async def synthesize_tax_plan(state: TaxOptimizationState) -> dict:
        """Combine tax analysis and replacement strategies into final action plan."""
        portfolio_context = state.get(
            "portfolio_context", "User's portfolio for tax optimization"
        )
        tax_loss_opportunities = state.get(
            "tax_loss_opportunities", "No tax-loss opportunities identified"
        )
        replacement_strategies = state.get(
            "replacement_strategies", "No replacement strategies designed"
        )

        synthesis_prompt = f"""Synthesize the following tax optimization analyses into a final actionable plan:

**PORTFOLIO CONTEXT**:
{portfolio_context}

**TAX-LOSS OPPORTUNITIES (Tax Scout)**:
{tax_loss_opportunities}

**REPLACEMENT STRATEGIES (Hedge Smith)**:
{replacement_strategies}

Provide **FINAL TAX OPTIMIZATION ACTION PLAN**:

1. **Immediate Actions** (Execute now):
   - Positions to sell immediately (no wash-sale risk, clear tax benefit)
   - Specific trade instructions: "Sell XXX shares of TICKER at market"
   - Estimated tax savings: $X,XXX total

2. **Replacement Positions** (Execute same day):
   - For each sold position requiring maintained exposure:
     - Ticker to sell: XXX shares of TICKER
     - Replacement: [Specific ETF / Options strategy]
     - Trade instructions: "Buy XXX shares of [ETF]" or "Buy X call + Sell X put"
     - Duration: Hold 31+ days, then can repurchase original if desired

3. **Year-End Optimization** (Hold for December):
   - Positions with smaller losses to harvest in December
   - Estimated tax savings if executed: $X,XXX
   - Calendar reminder: Review in [month]

4. **Avoid These Actions** (Wash-sale violations):
   - Do NOT sell: [tickers with recent purchases]
   - Wait until [date] to harvest these losses

5. **Total Tax Impact Summary**:
   - Total harvestable losses: -$X,XXX
   - Estimated tax savings (XX% bracket): $X,XXX
   - Cost of replacement strategies: $XXX (fees, spreads, option premium)
   - Net tax benefit: $X,XXX

6. **Compliance Checklist**:
   - [ ] No purchases of sold securities for 31 days
   - [ ] Replacement securities are not "substantially identical"
   - [ ] Maintain similar portfolio allocation and risk profile
   - [ ] Document cost basis and trade dates for tax reporting

**Example Format:**
```
FINAL TAX OPTIMIZATION PLAN

IMMEDIATE ACTIONS (Execute today):
1. Sell 100 shares TICKER1 @ market
   → Replace with 100 shares [SECTOR ETF]
   → Tax savings: $XXX | Hold 31+ days

2. Sell 50 shares TICKER2 @ market
   → No replacement needed (low conviction)
   → Tax savings: $XXX

YEAR-END HARVEST (Review December):
3. TICKER3: -$XXX loss available
   → Monitor for entry in Q4

AVOID (Wash-sale risk):
- TICKER4: Purchased [date], wait until [date] to sell

TOTAL IMPACT:
- Tax Savings: $X,XXX
- Replacement Cost: $XXX
- Net Benefit: $X,XXX
- Portfolio Exposure: Maintained via ETF substitutes
```

Keep it **actionable and compliant** (6-8 bullet points total)."""

        synthesis_msg = HumanMessage(content=synthesis_prompt)
        final_response = await llm.ainvoke([synthesis_msg])

        return {"messages": [final_response]}

    # Build the sequential workflow graph
    workflow = StateGraph(TaxOptimizationState)

    # Add agent nodes
    workflow.add_node("tax_scout", tax_scout_agent)
    workflow.add_node("hedge_smith", hedge_smith_agent)
    workflow.add_node("synthesize", synthesize_tax_plan)

    # Add tool execution nodes
    workflow.add_node("tax_scout_tools", ToolNode(tax_scout_tools_with_keys))
    workflow.add_node("hedge_smith_tools", ToolNode(hedge_smith_tools_with_keys))

    # Helper functions to check if tools were called
    def tax_scout_should_continue(state: TaxOptimizationState) -> str:
        """Check if Tax Scout made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tax_scout_tools"
        return "hedge_smith"

    def hedge_smith_should_continue(state: TaxOptimizationState) -> str:
        """Check if Hedge Smith made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "hedge_smith_tools"
        return "synthesize"

    # Define the workflow with tool execution loops
    # Tax Scout → Hedge Smith → Synthesis

    workflow.add_edge(START, "tax_scout")
    workflow.add_conditional_edges(
        "tax_scout",
        tax_scout_should_continue,
        {"tax_scout_tools": "tax_scout_tools", "hedge_smith": "hedge_smith"},
    )
    workflow.add_edge("tax_scout_tools", "tax_scout")  # Loop back after tool execution

    workflow.add_conditional_edges(
        "hedge_smith",
        hedge_smith_should_continue,
        {"hedge_smith_tools": "hedge_smith_tools", "synthesize": "synthesize"},
    )
    workflow.add_edge("hedge_smith_tools", "hedge_smith")

    workflow.add_edge("synthesize", END)

    return workflow.compile()
