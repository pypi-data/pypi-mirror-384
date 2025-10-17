"""Portfolio Protection Workflow - Risk assessment with hedging strategies.

This workflow coordinates two specialized agents to design comprehensive portfolio protection:
1. Risk Shield (Risk Manager) - Analyzes portfolio exposures, vulnerabilities, and risk metrics
2. Hedge Smith (Options Strategist) - Designs protective options strategies tailored to identified risks

The workflow provides a complete pipeline from risk assessment to actionable hedging recommendations.
"""

from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from navam_invest.config.settings import get_settings
from navam_invest.tools import bind_api_keys_to_tools, get_tools_for_agent


class PortfolioProtectionState(TypedDict):
    """State for portfolio protection workflow.

    This state is shared across all agents in the sequential workflow,
    allowing each agent to see prior analyses when providing their perspective.
    """

    messages: Annotated[list, add_messages]
    portfolio_context: str  # User's portfolio holdings and allocation information
    risk_assessment: str  # Results from Risk Shield's analysis
    hedging_strategies: str  # Results from Hedge Smith's strategy design


async def create_portfolio_protection_workflow() -> StateGraph:
    """Create a sequential multi-agent workflow for portfolio hedging.

    Workflow sequence:
    1. User provides portfolio holdings via /protect command
    2. Risk Shield analyzes portfolio exposures, vulnerabilities, and risk metrics
    3. Hedge Smith designs protective options strategies tailored to identified risks
    4. Synthesis combines both perspectives into actionable hedging plan

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
    risk_shield_tools = get_tools_for_agent("risk_shield")
    hedge_smith_tools = get_tools_for_agent("hedge_smith")

    # Bind API keys to tools
    risk_shield_tools_with_keys = bind_api_keys_to_tools(
        risk_shield_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        newsapi_key=settings.newsapi_api_key or "",
    )

    hedge_smith_tools_with_keys = bind_api_keys_to_tools(
        hedge_smith_tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
    )

    # Agent 1: Risk Shield - Portfolio Risk Analysis
    async def risk_shield_agent(state: PortfolioProtectionState) -> dict:
        """Risk Shield analyzes portfolio exposures and vulnerabilities."""
        portfolio_context = state.get("portfolio_context", "")

        system_prompt = f"""You are Risk Shield, an expert portfolio risk manager specializing in comprehensive risk analysis and exposure monitoring.

User's portfolio context: {portfolio_context if portfolio_context else "Analyze user's current holdings for risk exposures"}

Your task: Conduct **comprehensive portfolio risk assessment** identifying key vulnerabilities requiring protection.

**Risk Analysis Framework:**
1. **Concentration Risk**: Identify positions >15% of portfolio (single-stock risk)
2. **Sector/Theme Concentration**: Check for >30% allocation to any sector (e.g., tech, energy)
3. **Drawdown Analysis**: Calculate max historical drawdown for each position and portfolio
4. **Volatility Metrics**: Analyze position volatility (standard deviation, beta)
5. **Correlation Analysis**: Identify highly correlated positions (>0.7) that amplify risk
6. **Tail Risk**: Assess exposure to black swan events (VIX levels, market regime)
7. **Downside Scenarios**: Model portfolio impact under stress scenarios (-10%, -20%, -30% market moves)

**Output Requirements:**
- List all positions with concentration risk (>10% portfolio weight)
- Calculate portfolio-level metrics: overall beta, volatility, max drawdown potential
- Identify vulnerable positions requiring hedging (high beta, high volatility, concentrated)
- Estimate potential losses under stress scenarios
- Prioritize hedging recommendations by risk severity (CRITICAL/HIGH/MEDIUM)

**Example Output Format:**
```
PORTFOLIO RISK ASSESSMENT:

Portfolio Overview:
- Total Value: $XXX,XXX
- Number of Positions: XX
- Portfolio Beta: X.XX (vs S&P 500)
- Portfolio Volatility: XX% annualized
- Estimated Max Drawdown: -XX% (under -20% market scenario)

CONCENTRATION RISKS (Priority: CRITICAL):
1. TICKER1 - Company Name
   Position Size: $XX,XXX (XX% of portfolio)
   Current Price: $XX.XX | Beta: X.XX | Volatility: XX%
   Max Historical Drawdown: -XX% (from [date] to [date])
   Downside Risk: -$X,XXX (under -20% market move)
   Recommendation: HEDGE - Consider protective put or collar strategy

2. TICKER2 - Company Name
   Position Size: $XX,XXX (XX% of portfolio)
   Sector: [Sector] (Total sector allocation: XX%)
   Volatility: XX% | Beta: X.XX
   Correlation with TICKER1: 0.XX (amplified risk)
   Recommendation: HEDGE - Protect against sector-wide downturn

[... more positions ...]

SECTOR CONCENTRATION (Priority: HIGH):
- Technology: XX% of portfolio (XX% above recommended max)
  Tickers: [TICKER1, TICKER2, ...]
  Recommendation: Hedge at sector level (index puts on QQQ/XLK)

STRESS TEST RESULTS:
Market Scenario: -10% S&P 500 decline
- Portfolio Impact: -$XX,XXX (-XX%)
- Most Vulnerable: [TICKER1] -XX%, [TICKER2] -XX%

Market Scenario: -20% S&P 500 decline
- Portfolio Impact: -$XX,XXX (-XX%)
- Most Vulnerable: [TICKER1] -XX%, [TICKER2] -XX%

TAIL RISK INDICATORS:
- VIX Level: XX (Normal: <20 | Elevated: 20-30 | High: >30)
- Market Regime: [Bull/Bear/Sideways]
- Hedge Recommendation: [Now/Monitor/Defer] based on risk/reward

HEDGING PRIORITIES:
CRITICAL (Immediate Protection Needed):
- TICKER1: $XX,XXX position, XX% concentration, high beta X.XX
- Sector Tech: $XX,XXX total, XX% allocation

HIGH (Strong Protection Recommended):
- TICKER2: $XX,XXX position, elevated volatility XX%
- Correlated positions: TICKER3 + TICKER4 (correlation 0.XX)

MEDIUM (Consider if cost-effective):
- Overall portfolio tail risk protection
- Moderate-sized positions with acceptable volatility
```

**Risk Severity Classification:**
- CRITICAL: >20% portfolio concentration, or beta >1.5, or recent -30%+ drawdown
- HIGH: >15% portfolio concentration, or sector >30%, or volatility >40%
- MEDIUM: >10% portfolio concentration, or elevated beta 1.2-1.5, or moderate volatility

Provide **data-driven, quantitative risk assessment** that Hedge Smith can use to design targeted protection strategies."""

        # Bind tools and system prompt to LLM
        risk_llm = llm.bind_tools(risk_shield_tools_with_keys).bind(system=system_prompt)

        response = await risk_llm.ainvoke(state["messages"])

        # Store Risk Shield's results in state for Hedge Smith to reference
        results_text = response.content if hasattr(response, "content") else str(
            response
        )

        return {
            "messages": [response],
            "risk_assessment": results_text,
        }

    # Agent 2: Hedge Smith - Protective Strategy Design
    async def hedge_smith_agent(state: PortfolioProtectionState) -> dict:
        """Hedge Smith designs protective options strategies for identified risks."""
        portfolio_context = state.get("portfolio_context", "")
        risk_assessment = state.get("risk_assessment", "")

        system_prompt = f"""You are Hedge Smith, an expert options strategist specializing in portfolio protection strategies.

**Portfolio Context:**
{portfolio_context}

**Risk Shield's Analysis:**
{risk_assessment}

Your task: Design **cost-effective protective options strategies** for the risks identified by Risk Shield.

For each critical/high-priority risk, provide:

**Strategy Options:**

1. **Protective Put** (Direct downside protection):
   - Position: [TICKER], $X,XXX at risk
   - Recommended strike: $XX (XX% out-of-the-money)
   - Expiration: [Date] (XX days, XX months)
   - Cost: $XXX per contract (X% of position value)
   - Protection: Limits loss to XX% below current price
   - Break-even: $XX (current price - put premium)

2. **Collar Strategy** (Zero-cost / low-cost protection):
   - Position: [TICKER], $X,XXX at risk
   - Buy protective put: $XX strike
   - Sell covered call: $XX strike (to offset put cost)
   - Net cost: $XX (or net credit if call premium > put premium)
   - Protection range: Max loss XX%, max gain XX%
   - Ideal for: High conviction holdings where moderate upside cap acceptable

3. **Index Put Spread** (Sector/market protection):
   - For sector concentration (e.g., tech >30% portfolio)
   - Buy [QQQ/SPY/XLK] $XXX put
   - Sell [QQQ/SPY/XLK] $XXX put (spread to reduce cost)
   - Net cost: $XXX
   - Protection: Portfolio declines >X% if index drops >Y%
   - Advantage: Cheaper than individual stock puts, covers correlated positions

4. **Portfolio-Level Protection** (Tail risk hedge):
   - VIX calls or long-dated index puts
   - Cost: X% of portfolio value
   - Protection: Significant payoff in -20%+ market crash
   - Frequency: Quarterly roll, adjust based on market regime

**Output Format (Per Position/Risk)**:
```
PROTECTIVE STRATEGY: TICKER - Company Name
Position Value: $XX,XXX (XX% of portfolio)
Risk Identified: [Concentration / High Beta / Sector Exposure / Volatility]
Current Price: $XX.XX

RECOMMENDED STRATEGY: [Protective Put / Collar / Defer]

Option 1: Protective Put (Direct Protection)
- Strike: $XX (XX% OTM)
- Expiration: [Date] (XX days)
- Contracts: X (protecting XXX shares)
- Premium: $X.XX per share = $XXX total cost (X% of position)
- Protection: Loss limited to $X,XXX (XX% max drawdown)
- Break-even: $XX (stock must rise $X to cover premium)
- Annualized Cost: XX% if rolled quarterly

Option 2: Collar (Cost-Reduced Protection)
- Buy put: $XX strike (XX% OTM)
- Sell call: $XX strike (XX% OTM)
- Net cost: $XXX (or $XXX credit)
- Protection: Loss limited to XX%, gain limited to XX%
- Best if: High conviction, willing to cap upside at XX%
- Expiration: [Date]

Option 3: Do Nothing / Monitor
- Rationale: [Risk acceptable given outlook / Protection too expensive / etc.]
- Trigger: Re-evaluate if stock drops below $XX or volatility >XX%

RECOMMENDATION: [Specific strategy] for [reason]
Cost-Benefit Analysis:
- Protection cost: $XXX (X% of position)
- Potential saved loss: $X,XXX (if stock drops XX%)
- Risk/Reward: [Favorable / Neutral / Expensive] given current volatility
```

**Sector-Level Strategy Example:**
```
SECTOR PROTECTION: Technology (XX% portfolio allocation)
Affected Positions: [TICKER1, TICKER2, TICKER3] = $XXX,XXX total

RECOMMENDED STRATEGY: QQQ Put Spread
- Buy QQQ $XXX put (current QQQ: $XXX)
- Sell QQQ $XXX put (spread width: $XX)
- Expiration: [Date] (XX days)
- Contracts: XX (match sector delta exposure)
- Net cost: $X,XXX
- Protection: Breakeven if QQQ drops XX%, max payout $XX,XXX
- Advantage: Single trade protects entire sector exposure, lower cost than individual puts
```

**Portfolio Summary:**
```
TOTAL HEDGING PLAN

IMMEDIATE HEDGES (Critical Risk):
1. TICKER1: Protective put, $XXX cost, limits loss to $X,XXX
2. Tech Sector: QQQ put spread, $XXX cost, protects $XX,XXX allocation

MODERATE HEDGES (High Risk, Cost-Dependent):
3. TICKER2: Collar strategy, $XXX cost (or credit), XX% protection
4. TICKER3: Monitor, re-evaluate if drops below $XX

TOTAL HEDGING COST: $X,XXX (X% of portfolio value)
POTENTIAL PROTECTED VALUE: $XX,XXX
MAXIMUM LOSS WITH HEDGES: -$X,XXX (vs -$XX,XXX unhedged)

COST-BENEFIT:
- Hedging cost: X% of portfolio
- Reduced max drawdown: From -XX% to -X% (XX% improvement)
- Recommendation: [Implement all / Implement critical only / Defer] based on [market outlook / portfolio risk tolerance]
```

**Design Principles:**
- Match hedge size to risk severity (critical > high > medium)
- Optimize cost vs protection (consider spreads, collars to reduce premium)
- Use index hedges for sector/correlation risks (more efficient)
- Provide clear cost-benefit analysis for each recommendation
- Consider user's outlook (hedge more if bearish, less if bullish)

Provide **practical, actionable hedging strategies** with transparent cost-benefit trade-offs."""

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
            "hedging_strategies": strategy_text,
        }

    # Synthesis: Combine risk assessment + hedging strategies into actionable plan
    async def synthesize_protection_plan(state: PortfolioProtectionState) -> dict:
        """Combine risk analysis and hedging strategies into final action plan."""
        portfolio_context = state.get(
            "portfolio_context", "User's portfolio for protection analysis"
        )
        risk_assessment = state.get(
            "risk_assessment", "No risk assessment available"
        )
        hedging_strategies = state.get(
            "hedging_strategies", "No hedging strategies designed"
        )

        synthesis_prompt = f"""Synthesize the following portfolio protection analyses into a final actionable plan:

**PORTFOLIO CONTEXT**:
{portfolio_context}

**RISK ASSESSMENT (Risk Shield)**:
{risk_assessment}

**HEDGING STRATEGIES (Hedge Smith)**:
{hedging_strategies}

Provide **FINAL PORTFOLIO PROTECTION PLAN**:

1. **Immediate Hedges** (Execute now - Critical Risk):
   - Specific positions requiring urgent protection
   - Exact trade instructions: "Buy X put contracts, $XX strike, [expiration]"
   - Cost per hedge and total hedging cost
   - Expected protection: "Limits loss to $X,XXX"

2. **Cost-Optimized Hedges** (Execute if cost-effective - High Risk):
   - Collar strategies (sell calls to offset put cost)
   - Index put spreads for sector protection
   - Trade instructions with both legs of strategy
   - Net cost or credit for each trade

3. **Monitor & Defer** (Medium Risk - acceptable for now):
   - Positions with moderate risk but expensive protection
   - Trigger points for re-evaluation: "If TICKER drops below $XX, hedge"
   - Market conditions to watch: VIX level, sector trends

4. **Total Hedging Summary**:
   - Total cost: $X,XXX (X% of portfolio value)
   - Protected value: $XX,XXX positions
   - Unhedged max loss: -$XX,XXX (-XX% portfolio)
   - Hedged max loss: -$X,XXX (-X% portfolio)
   - Risk reduction: XX percentage points of downside protection

5. **Cost-Benefit Recommendation**:
   - Is hedging worth it? [Yes/No/Partial] based on:
     - Hedging cost (X%) vs max protected loss (XX%)
     - Current market regime (VIX XX, trend [bullish/bearish])
     - Portfolio risk tolerance
   - Recommendation: [Implement all hedges / Implement critical only / Defer hedging]

6. **Execution Checklist**:
   - [ ] Critical hedges: [List tickers/strategies]
   - [ ] Optimal hedges: [List if cost-effective]
   - [ ] Set monitoring alerts: [Trigger prices/dates]
   - [ ] Review quarterly: [Next review date]

**Example Format:**
```
FINAL PORTFOLIO PROTECTION PLAN

IMMEDIATE HEDGES (Critical Risk - Execute Today):
1. TICKER1 Protective Put
   → Buy 10 contracts, $XX strike, [expiration]
   → Cost: $X,XXX (X% of position)
   → Protection: Limits loss to $X,XXX (XX% max)

2. Tech Sector Index Hedge
   → Buy 5 QQQ $XXX put / Sell 5 QQQ $XXX put (spread)
   → Cost: $XXX
   → Protection: $XX,XXX sector allocation, breakeven if QQQ -X%

COST-OPTIMIZED HEDGES (High Risk - Recommended):
3. TICKER2 Collar
   → Buy XX put $XX strike + Sell XX call $XX strike
   → Net cost: $XXX (or credit)
   → Protection: XX% downside, XX% upside cap

MONITOR (Medium Risk - Defer for now):
4. TICKER3: Set alert if drops below $XX (currently $XX)
5. Portfolio tail risk: Re-evaluate if VIX rises above 30 (currently XX)

TOTAL PROTECTION PLAN:
- Hedging Cost: $X,XXX (X% of portfolio)
- Protected Positions: $XX,XXX (XX% of portfolio)
- Max Loss (Unhedged): -$XX,XXX (-XX%)
- Max Loss (Hedged): -$X,XXX (-X%)
- Downside Protection: XX percentage points

RECOMMENDATION: [Implement all / Implement critical only / Defer]
Rationale: [Cost is X% for XX% protection, [favorable/expensive] given current market regime]
```

Keep it **actionable with clear trade instructions and cost-benefit justification** (8-10 bullet points total)."""

        synthesis_msg = HumanMessage(content=synthesis_prompt)
        final_response = await llm.ainvoke([synthesis_msg])

        return {"messages": [final_response]}

    # Build the sequential workflow graph
    workflow = StateGraph(PortfolioProtectionState)

    # Add agent nodes
    workflow.add_node("risk_shield", risk_shield_agent)
    workflow.add_node("hedge_smith", hedge_smith_agent)
    workflow.add_node("synthesize", synthesize_protection_plan)

    # Add tool execution nodes
    workflow.add_node("risk_shield_tools", ToolNode(risk_shield_tools_with_keys))
    workflow.add_node("hedge_smith_tools", ToolNode(hedge_smith_tools_with_keys))

    # Helper functions to check if tools were called
    def risk_shield_should_continue(state: PortfolioProtectionState) -> str:
        """Check if Risk Shield made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "risk_shield_tools"
        return "hedge_smith"

    def hedge_smith_should_continue(state: PortfolioProtectionState) -> str:
        """Check if Hedge Smith made tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "hedge_smith_tools"
        return "synthesize"

    # Define the workflow with tool execution loops
    # Risk Shield → Hedge Smith → Synthesis

    workflow.add_edge(START, "risk_shield")
    workflow.add_conditional_edges(
        "risk_shield",
        risk_shield_should_continue,
        {"risk_shield_tools": "risk_shield_tools", "hedge_smith": "hedge_smith"},
    )
    workflow.add_edge("risk_shield_tools", "risk_shield")  # Loop back after tool execution

    workflow.add_conditional_edges(
        "hedge_smith",
        hedge_smith_should_continue,
        {"hedge_smith_tools": "hedge_smith_tools", "synthesize": "synthesize"},
    )
    workflow.add_edge("hedge_smith_tools", "hedge_smith")

    workflow.add_edge("synthesize", END)

    return workflow.compile()
