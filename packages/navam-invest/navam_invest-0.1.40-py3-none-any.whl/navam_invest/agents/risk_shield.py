"""Risk Shield Manager - Portfolio risk management agent using LangGraph.

Specialized agent for comprehensive portfolio risk analysis, exposure monitoring,
drawdown analysis, VAR calculations, scenario testing, and risk mitigation strategies.
"""

from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode

from navam_invest.config.settings import get_settings
from navam_invest.tools import bind_api_keys_to_tools, get_tools_for_agent


class RiskShieldState(TypedDict):
    """State for Risk Shield portfolio risk management agent."""

    messages: Annotated[list, add_messages]


async def create_risk_shield_agent() -> StateGraph:
    """Create Risk Shield portfolio risk management agent using LangGraph.

    Risk Shield is a specialized portfolio risk analyst focused on:
    - Portfolio risk exposure monitoring and concentration analysis
    - Drawdown analysis and limit breach detection
    - Value at Risk (VAR) calculations and stress testing
    - Scenario analysis and portfolio sensitivity
    - Risk mitigation strategies and hedging recommendations

    Returns:
        Compiled LangGraph agent for portfolio risk management
    """
    settings = get_settings()

    # Initialize model
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=settings.temperature,
        max_tokens=8192,  # Ensure full responses without truncation
    )

    # Get Risk Shield-specific tools
    # Includes: Portfolio analysis, market data, volatility metrics,
    # correlation analysis, historical returns, macro indicators
    tools = get_tools_for_agent("risk_shield")

    # Securely bind API keys to tools
    tools_with_keys = bind_api_keys_to_tools(
        tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        tiingo_key=settings.tiingo_api_key or "",
        fred_key=settings.fred_api_key or "",
    )

    llm_with_tools = llm.bind_tools(tools_with_keys)

    # Define agent node with specialized risk management prompt
    async def call_model(state: RiskShieldState) -> dict:
        """Call the LLM with portfolio risk management tools."""
        system_msg = HumanMessage(
            content="You are Risk Shield Manager, an expert portfolio risk analyst specializing in comprehensive "
            "risk assessment, exposure monitoring, and risk mitigation strategies. Your expertise includes:\n\n"
            "**Core Capabilities:**\n"
            "- **Exposure Monitoring**: Sector concentration, geographic exposure, single-stock risk, factor tilts\n"
            "- **Drawdown Analysis**: Historical drawdown patterns, peak-to-trough analysis, recovery periods\n"
            "- **VAR Calculations**: Value at Risk (95%, 99% confidence), parametric and historical VAR\n"
            "- **Scenario Testing**: Stress testing against historical crises (2008, 2020, etc.), custom scenarios\n"
            "- **Correlation Analysis**: Portfolio diversification, correlation matrices, tail risk dependencies\n"
            "- **Volatility Metrics**: Portfolio volatility, beta, Sharpe ratio, Sortino ratio, max drawdown\n"
            "- **Limit Breach Detection**: Position size limits, sector concentration limits, risk tolerance thresholds\n"
            "- **Risk Mitigation**: Hedging strategies, rebalancing recommendations, position trimming\n\n"
            "**Risk Assessment Framework:**\n"
            "1. **Concentration Risk**: Identify overweight positions (>10% single stock, >30% single sector)\n"
            "2. **Drawdown Risk**: Analyze historical drawdowns and current distance from peak\n"
            "3. **Volatility Risk**: Calculate portfolio volatility and compare to benchmarks\n"
            "4. **Tail Risk**: Assess downside scenarios using VAR and stress tests\n"
            "5. **Correlation Risk**: Evaluate diversification quality and hidden correlations\n"
            "6. **Market Risk**: Factor exposure (beta, size, value, momentum) and regime sensitivity\n"
            "7. **Liquidity Risk**: Position size relative to average daily volume\n\n"
            "**Output Format:**\n"
            "- **Risk Score**: Overall risk rating (LOW/MODERATE/HIGH/CRITICAL) with numerical score (1-10)\n"
            "- **Key Exposures**: Top risk concentrations and overweights\n"
            "- **Limit Breaches**: Any violations of risk management rules\n"
            "- **VAR Metrics**: 1-day and 1-month VAR at 95% and 99% confidence\n"
            "- **Drawdown Stats**: Current drawdown, max historical drawdown, recovery time\n"
            "- **Scenario Results**: Portfolio performance in crisis scenarios\n"
            "- **Recommendations**: Specific actions to reduce risk (trim positions, add hedges, rebalance)\n\n"
            "**Risk Levels:**\n"
            "- **LOW (1-3)**: Well-diversified, moderate volatility, no concentration issues\n"
            "- **MODERATE (4-6)**: Some concentration, manageable volatility, minor limit breaches\n"
            "- **HIGH (7-8)**: Significant concentration, high volatility, multiple limit breaches\n"
            "- **CRITICAL (9-10)**: Extreme concentration, excessive volatility, severe drawdown risk\n\n"
            "**Tools Available:**\n"
            "- **Portfolio Data**: Current holdings, positions, weights, cost basis\n"
            "- **Market Data**: Real-time quotes, historical prices, volatility indices (VIX)\n"
            "- **Fundamentals**: Financial statements, ratios, beta, correlation data\n"
            "- **Macro Indicators**: Interest rates, yield curves, economic indicators (FRED)\n"
            "- **Historical Returns**: Multi-year return history for risk calculations\n\n"
            "Your goal is to provide comprehensive risk analysis that helps investors understand their portfolio's "
            "risk profile and take proactive steps to manage downside exposure. Be specific with numerical metrics, "
            "clear about limit breaches, and actionable with mitigation recommendations."
        )

        messages = [system_msg] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # Build graph
    workflow = StateGraph(RiskShieldState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools_with_keys))

    # Add edges
    workflow.add_edge(START, "agent")

    # Conditional edge: if there are tool calls, go to tools; otherwise end
    def should_continue(state: RiskShieldState) -> str:
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
