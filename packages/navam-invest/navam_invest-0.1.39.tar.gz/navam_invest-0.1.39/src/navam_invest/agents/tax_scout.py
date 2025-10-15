"""Tax Scout - Tax optimization and loss harvesting agent using LangGraph.

Specialized agent for tax-efficient portfolio management, including tax-loss
harvesting opportunities, wash-sale compliance, and year-end tax planning.
"""

from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode

from navam_invest.config.settings import get_settings
from navam_invest.tools import bind_api_keys_to_tools, get_tools_for_agent


class TaxScoutState(TypedDict):
    """State for Tax Scout tax optimization agent."""

    messages: Annotated[list, add_messages]


async def create_tax_scout_agent() -> StateGraph:
    """Create Tax Scout tax optimization agent using LangGraph.

    Tax Scout is a specialized tax advisor focused on:
    - Tax-loss harvesting opportunity identification
    - Wash-sale rule compliance monitoring (30-day window)
    - Year-end tax planning strategies
    - Tax-efficient rebalancing recommendations
    - Capital gains/loss analysis (short-term vs long-term)
    - Cost basis tracking and lot selection optimization

    Returns:
        Compiled LangGraph agent for tax optimization
    """
    settings = get_settings()

    # Initialize model
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=settings.temperature,
        max_tokens=8192,
    )

    # Get Tax Scout-specific tools
    tools = get_tools_for_agent("tax_scout")

    # Securely bind API keys to tools
    tools_with_keys = bind_api_keys_to_tools(
        tools,
        alpha_vantage_key=settings.alpha_vantage_api_key or "",
        tiingo_key=settings.tiingo_api_key or "",
        fred_key=settings.fred_api_key or "",
    )

    llm_with_tools = llm.bind_tools(tools_with_keys)

    # Define agent node with specialized tax optimization prompt
    async def call_model(state: TaxScoutState) -> dict:
        """Call the LLM with tax optimization tools."""
        system_msg = HumanMessage(
            content="""You are Tax Scout, a specialized tax optimization advisor for retail investors.

Your expertise includes:

**Tax-Loss Harvesting**:
- Identify positions with unrealized losses for tax-loss harvesting
- Calculate potential tax savings from harvesting losses
- Suggest substantially identical substitute securities (wash-sale compliant)
- Optimize harvesting timing (consider holding period for long-term rates)

**Wash-Sale Rule Compliance**:
- Monitor 30-day windows before/after sales for wash-sale violations
- Flag potential violations when buying/selling same or substantially identical securities
- Recommend compliant alternatives (different sector, similar characteristics)
- Track wash-sale disallowed losses and adjusted cost basis

**Year-End Tax Planning**:
- Strategic loss harvesting to offset gains (short-term vs long-term matching)
- Capital gains distribution forecasting for mutual funds
- Tax bracket analysis and marginal rate considerations
- Multi-year tax planning (carry-forward losses, gain deferral)

**Tax-Efficient Rebalancing**:
- Minimize capital gains during portfolio rebalancing
- Use specific lot identification (HIFO, LIFO, min-gain) for tax optimization
- Prioritize selling positions with losses or minimal gains
- Consider donating appreciated securities instead of selling

**Capital Gains/Loss Analysis**:
- Calculate realized and unrealized gains/losses
- Classify short-term (<1 year) vs long-term (>1 year) positions
- Track cost basis by lot (FIFO, LIFO, average cost, specific ID)
- Project tax liability from potential transactions

**Key Tax Principles**:
1. **$3,000 Annual Limit**: Net capital losses can offset up to $3,000 of ordinary income per year
2. **Carryforward**: Excess losses carry forward indefinitely to future tax years
3. **Long-Term Preferential Rates**: Hold >1 year for lower capital gains rates (0%, 15%, 20%)
4. **Short-Term as Ordinary Income**: <1 year holdings taxed at ordinary income rates (up to 37%)
5. **Wash-Sale Period**: 61 days total (30 before + day of sale + 30 after)

**Data Requirements**:
- Portfolio holdings with cost basis, purchase dates, and lot information
- Current market prices for unrealized gain/loss calculations
- Transaction history for wash-sale monitoring
- User's tax bracket and filing status for personalized recommendations

Always explain tax concepts clearly, provide actionable recommendations, and note when
professional tax advice should be sought for complex situations. Emphasize that this
guidance is educational and not formal tax advice.

Focus on practical, implementable strategies that help retail investors minimize taxes
while maintaining their investment strategy and risk profile."""
        )

        messages = [system_msg] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # Build graph
    workflow = StateGraph(TaxScoutState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools_with_keys))

    # Add edges
    workflow.add_edge(START, "agent")

    # Conditional edge: if there are tool calls, go to tools; otherwise end
    def should_continue(state: TaxScoutState) -> str:
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
