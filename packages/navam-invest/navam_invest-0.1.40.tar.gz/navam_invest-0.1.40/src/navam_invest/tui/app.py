"""Textual-based TUI for Navam Invest."""

import asyncio
import random
from typing import Optional

from langchain_core.messages import HumanMessage
from rich.markdown import Markdown
from rich.table import Table
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Input, RichLog
from textual.worker import Worker, WorkerState

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
from navam_invest.agents.router import create_router_agent, set_streaming_queue
from navam_invest.workflows import (
    create_investment_analysis_workflow,
    create_idea_discovery_workflow,
    create_portfolio_protection_workflow,
    create_tax_optimization_workflow,
)
from navam_invest.config.settings import ConfigurationError
from navam_invest.utils import check_all_apis, save_investment_report, save_agent_report

# Example prompts for each agent
PORTFOLIO_EXAMPLES = [
    "What's the current price and overview of AAPL?",
    "Show me the fundamentals and financial ratios for TSLA",
    "What insider trades have happened at MSFT recently?",
    "Screen for tech stocks with P/E ratio under 20 and market cap over $10B",
    "Get the latest 10-K filing for GOOGL",
    "Show me institutional holdings (13F filings) for NVDA",
    "Compare the financial ratios of AAPL and MSFT",
    "What does the latest 10-Q for AMZN reveal about their business?",
]

RESEARCH_EXAMPLES = [
    "What's the current GDP growth rate?",
    "Show me key macro indicators: GDP, CPI, and unemployment",
    "What does the Treasury yield curve look like today?",
    "Calculate the 10-year minus 2-year yield spread",
    "What's the current debt-to-GDP ratio?",
    "How has inflation (CPI) trended over the past year?",
    "What's the current federal funds rate?",
    "Is the yield curve inverted? What does that signal?",
]

QUILL_EXAMPLES = [
    "Analyze AAPL and provide an investment thesis with fair value",
    "What's your investment recommendation for TSLA? Include catalysts and risks",
    "Deep dive on MSFT: business quality, financials, and valuation",
    "Build an investment case for GOOGL with DCF-based fair value",
    "Analyze NVDA's 5-year fundamental trends and provide a thesis",
    "What does the latest 10-K reveal about AMZN's business model?",
    "Compare META and SNAP: which is the better investment and why?",
    "Thesis on NFLX: analyze subscriber growth, margins, and competition",
]

SCREEN_FORGE_EXAMPLES = [
    "Screen for value stocks: P/E under 15, P/B under 2, market cap over $1B",
    "Find growth stocks with revenue growth >20% and expanding margins",
    "Screen for quality companies: ROE >15%, net margin >10%, low debt",
    "Identify dividend stocks with yield >3% and 5+ year payment history",
    "Find small-cap growth stocks: market cap $300M-$2B, growth >25%",
    "Screen for tech stocks with strong momentum and positive analyst sentiment",
    "Find undervalued healthcare stocks with strong fundamentals",
    "Screen for large-cap stocks with consistent earnings growth and low volatility",
]

MACRO_LENS_EXAMPLES = [
    "What's the current macro regime? Are we in expansion, peak, or recession?",
    "Analyze the yield curve. Is it signaling recession risk?",
    "What sectors should I overweight given current economic conditions?",
    "Assess inflation trends and Fed policy implications for markets",
    "What factor exposures (value/growth, size, quality) make sense now?",
    "Identify top 3 macro risks to monitor over the next 6 months",
    "How do current GDP, unemployment, and inflation compare to historical norms?",
    "Should I be defensive or cyclical given the economic cycle phase?",
]

EARNINGS_WHISPERER_EXAMPLES = [
    "Analyze AAPL earnings history - are they consistent beaters?",
    "What's TSLA's earnings surprise trend over the last 4 quarters?",
    "Is there a post-earnings drift opportunity in NVDA after recent earnings?",
    "When is MSFT's next earnings date? What are analyst estimates?",
    "Show me GOOGL's earnings quality - revenue vs EPS beats",
    "Track analyst estimate revisions for AMZN post-earnings",
    "Find stocks with 3+ consecutive quarters beating estimates",
    "Analyze META's earnings momentum and recommend a trade",
]

NEWS_SENTRY_EXAMPLES = [
    "What material events (8-K filings) happened at TSLA in the last 30 days?",
    "Show me recent insider trading activity (Form 4) for AAPL",
    "Are there any breaking news events for NVDA that I should know about?",
    "Track analyst rating changes for MSFT over the past week",
    "Monitor GOOGL for material corporate events - any M&A, management changes?",
    "Alert me to any critical events for META - bankruptcy, CEO changes, etc.",
    "What's the sentiment around recent AMZN news?",
    "Check for insider buying clusters in tech stocks",
]

RISK_SHIELD_EXAMPLES = [
    "Analyze my portfolio risk - what are my concentration exposures?",
    "Calculate VAR for my holdings at 95% and 99% confidence levels",
    "What's my portfolio's maximum drawdown and current risk score?",
    "Run a stress test - how would my portfolio perform in a 2008-style crisis?",
    "Identify any sector concentration risks in my portfolio",
    "What's my portfolio volatility compared to S&P 500?",
    "Check if I'm breaching any position size limits (>10% single stock)",
    "Recommend risk mitigation strategies for my current exposures",
]

TAX_SCOUT_EXAMPLES = [
    "Identify tax-loss harvesting opportunities in my portfolio",
    "Check for potential wash-sale violations in my recent transactions",
    "What are my short-term vs long-term capital gains/losses?",
    "Recommend tax-efficient rebalancing strategies for my portfolio",
    "Calculate potential tax savings from harvesting losses this year",
    "Suggest substitute securities for positions I want to harvest",
    "What's my carryforward loss balance from previous years?",
    "Plan year-end tax moves to minimize my 2025 tax liability",
]

HEDGE_SMITH_EXAMPLES = [
    "Design a protective collar for my 500 AAPL shares at $200",
    "What covered call strategy can generate 2-3% monthly income on MSFT?",
    "I need downside protection on NVDA - suggest a put buying strategy",
    "How can I use options to acquire GOOGL at a lower price?",
    "Analyze options chain for TSLA - which strikes have best risk/reward?",
    "Create a collar strategy to lock in gains on my tech portfolio",
    "What's the cost of insuring my 1000 shares of AMZN with puts?",
    "Design a covered call strategy for META - optimize strike and expiration",
]

WORKFLOW_EXAMPLES = [
    "/analyze AAPL - Complete investment analysis (fundamental + macro)",
    "/analyze MSFT - Should I invest? Get both bottom-up and top-down view",
    "/analyze NVDA - Multi-agent analysis combining Quill and Macro Lens",
    "/analyze GOOGL - Comprehensive thesis with macro timing validation",
]


class ChatUI(App):
    """Navam Invest chat interface."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #chat-log {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        overflow-x: hidden;
        overflow-y: auto;
    }

    #input-container {
        height: auto;
        padding: 1;
    }

    #user-input {
        width: 100%;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+c", "clear", "Clear"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.portfolio_agent: Optional[object] = None
        self.research_agent: Optional[object] = None
        self.quill_agent: Optional[object] = None
        self.screen_forge_agent: Optional[object] = None
        self.macro_lens_agent: Optional[object] = None
        self.earnings_whisperer_agent: Optional[object] = None
        self.news_sentry_agent: Optional[object] = None
        self.risk_shield_agent: Optional[object] = None
        self.tax_scout_agent: Optional[object] = None
        self.hedge_smith_agent: Optional[object] = None
        self.router_agent: Optional[object] = None
        self.investment_workflow: Optional[object] = None
        self.idea_discovery_workflow: Optional[object] = None
        self.portfolio_protection_workflow: Optional[object] = None
        self.tax_optimization_workflow: Optional[object] = None
        self.current_agent: str = "portfolio"
        self.router_mode: bool = True  # True = automatic routing, False = manual agent selection
        self.agents_initialized: bool = False
        self.streaming_queue: Optional[asyncio.Queue] = None  # Queue for sub-agent tool call streaming
        self.streaming_task: Optional[asyncio.Task] = None  # Background task for queue consumption
        self.agent_worker: Optional[Worker] = None  # Worker for agent execution
        self.cancellation_requested: bool = False  # Flag to track cancellation request

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
        yield Container(
            Input(
                placeholder="Ask about stocks or economic indicators (/examples for ideas, /help for commands)...",
                id="user-input",
            ),
            id="input-container",
        )
        yield Footer()

    async def _consume_streaming_events(self, chat_log: RichLog) -> None:
        """Background task to consume and display sub-agent tool call events from queue.

        This task runs concurrently with agent execution to provide progressive disclosure
        of tool calls made by sub-agents within router tools.

        Args:
            chat_log: The RichLog widget to write events to
        """
        try:
            while True:
                # Wait for event from queue (with timeout to allow task cancellation)
                try:
                    event = await asyncio.wait_for(self.streaming_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue

                # Process event based on type
                event_type = event.get("type")

                if event_type == "tool_call":
                    # Display sub-agent tool call in real-time
                    agent_name = event.get("agent", "Unknown")
                    tool_name = event.get("tool_name", "unknown")
                    tool_args = event.get("args", {})

                    # Format args for display (limit length)
                    args_str = str(tool_args)
                    if len(args_str) > 80:
                        args_str = args_str[:77] + "..."

                    # Write to chat log with proper indentation (showing hierarchy)
                    chat_log.write(f"[dim]      → {tool_name}({args_str})[/dim]\n")

                elif event_type == "tool_complete":
                    # Optional: Show tool completion
                    tool_name = event.get("tool_name", "unknown")
                    chat_log.write(f"[dim]      ✓ {tool_name}[/dim]\n")

                elif event_type == "error":
                    # Show errors from sub-agents
                    agent_name = event.get("agent", "Unknown")
                    error_msg = event.get("message", "Unknown error")
                    chat_log.write(f"[dim red]      ✗ {agent_name} error: {error_msg}[/dim]\n")

                # Mark task as done
                self.streaming_queue.task_done()

        except asyncio.CancelledError:
            # Task cancelled - clean shutdown
            pass
        except Exception as e:
            # Log unexpected errors but don't crash
            chat_log.write(f"[dim yellow]⚠️ Streaming error: {str(e)}[/dim]\n")

    async def on_mount(self) -> None:
        """Initialize agents when app mounts."""
        # Set initial status
        self.sub_title = "Initializing agents..."

        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(
            Markdown(
                "# Welcome to Navam Invest\n\n"
                "Your AI-powered investment advisor with **automatic intent-based routing**. "
                "Simply ask your question naturally - no need to select an agent!\n\n"
                "**💡 How it works:**\n"
                "- Just type your investment question (e.g., \"Should I invest in AAPL?\")\n"
                "- Router automatically selects the right specialist agent(s)\n"
                "- Get coordinated analysis from multiple agents when needed\n\n"
                "**🎯 Manual Agent Commands** (for power users):\n"
                "- `/portfolio` - Portfolio analysis agent\n"
                "- `/quill` - Equity research agent\n"
                "- `/screen` - Stock screening agent\n"
                "- `/macro` - Market strategist agent\n"
                "- `/earnings` - Earnings analyst agent\n"
                "- `/news` - Event monitoring agent\n"
                "- `/risk` - Risk manager agent\n"
                "- `/tax` - Tax optimization agent\n"
                "- `/hedge` - Options strategies agent\n"
                "- `/research` - Macro research agent\n\n"
                "**⚙️ Other Commands:**\n"
                "- `/router on|off` - Toggle automatic routing\n"
                "- `/analyze <SYMBOL>` - Multi-agent investment analysis workflow\n"
                "- `/discover [CRITERIA]` - Systematic idea generation workflow\n"
                "- `/protect [PORTFOLIO]` - Portfolio hedging workflow\n"
                "- `/optimize-tax [PORTFOLIO]` - Tax-loss harvesting workflow\n"
                "- `/examples` - Show example prompts\n"
                "- `/help` - Show all commands\n\n"
                "**Keyboard Shortcuts:** `ESC` Cancel | `Ctrl+C` Clear | `Ctrl+Q` Quit\n\n"
                "**Tip:** Just ask naturally - \"Find undervalued tech stocks\" or \"Analyze TSLA earnings\"!\n"
            )
        )

        # Initialize streaming queue for progressive disclosure of sub-agent tool calls
        self.streaming_queue = asyncio.Queue()
        set_streaming_queue(self.streaming_queue)

        # Initialize agents
        try:
            self.portfolio_agent = await create_portfolio_agent()
            self.research_agent = await create_research_agent()
            self.quill_agent = await create_quill_agent()
            self.screen_forge_agent = await create_screen_forge_agent()
            self.macro_lens_agent = await create_macro_lens_agent()
            self.earnings_whisperer_agent = await create_earnings_whisperer_agent()
            self.news_sentry_agent = await create_news_sentry_agent()
            self.risk_shield_agent = await create_risk_shield_agent()
            self.tax_scout_agent = await create_tax_scout_agent()
            self.hedge_smith_agent = await create_hedge_smith_agent()
            self.router_agent = await create_router_agent()
            self.investment_workflow = await create_investment_analysis_workflow()
            self.idea_discovery_workflow = await create_idea_discovery_workflow()
            self.portfolio_protection_workflow = await create_portfolio_protection_workflow()
            self.tax_optimization_workflow = await create_tax_optimization_workflow()
            self.agents_initialized = True
            self.sub_title = "Router: Active | Ready"
            chat_log.write("[green]✓ Agents initialized successfully (Portfolio, Research, Quill, Screen Forge, Macro Lens, Earnings Whisperer, News Sentry, Risk Shield, Tax Scout, Hedge Smith)[/green]")
            chat_log.write("[green]✓ Router agent initialized - automatic intent-based routing enabled![/green]")
            chat_log.write("[green]✓ Multi-agent workflows ready (Investment Analysis, Idea Discovery, Portfolio Protection, Tax Optimization)[/green]")
            chat_log.write("[dim]✓ Progressive streaming enabled for sub-agent tool calls[/dim]")
        except ConfigurationError as e:
            self.agents_initialized = False
            # Show helpful setup instructions for missing API keys
            chat_log.write(
                Markdown(
                    f"# ⚠️ Configuration Required\n\n"
                    f"{str(e)}\n\n"
                    f"---\n\n"
                    f"**Quick Setup:**\n\n"
                    f"1. Copy the example file: `cp .env.example .env`\n"
                    f"2. Edit `.env` and add your API key\n"
                    f"3. Restart the application: `navam invest`\n\n"
                    f"Press `Ctrl+Q` to quit."
                )
            )
        except Exception as e:
            self.agents_initialized = False
            chat_log.write(
                Markdown(
                    f"# ❌ Error Initializing Agents\n\n"
                    f"```\n{str(e)}\n```\n\n"
                    f"Please check your configuration and try again.\n\n"
                    f"Press `Ctrl+Q` to quit."
                )
            )

    async def _run_workflow_stream(
        self,
        workflow: object,
        initial_state: dict,
        workflow_name: str,
        chat_log: RichLog,
        node_messages: dict[str, str],
    ) -> tuple[dict, bool]:
        """Run workflow streaming in background (worker-compatible).

        Args:
            workflow: The LangGraph workflow to run
            initial_state: Initial state dictionary for the workflow
            workflow_name: Name of the workflow for logging
            chat_log: RichLog widget for output
            node_messages: Dict mapping node names to status messages

        Returns:
            tuple of (workflow_state, was_cancelled)
        """
        workflow_state = {}
        tool_calls_shown = set()
        was_cancelled = False

        try:
            # Create the stream
            stream = workflow.astream(
                initial_state,
                stream_mode=["values", "updates"]
            )

            # Iterate with cancellation awareness
            async for event in stream:
                # Check for cancellation FIRST (before processing)
                if self.cancellation_requested:
                    was_cancelled = True
                    break

                # Yield control to event loop periodically
                await asyncio.sleep(0)

                # Parse the event tuple
                if isinstance(event, tuple) and len(event) == 2:
                    event_type, event_data = event

                    # Handle node updates
                    if event_type == "updates":
                        for node_name, node_output in event_data.items():
                            # Show which agent/node is working
                            if node_name in node_messages:
                                chat_log.write(f"[dim]  {node_messages[node_name]}[/dim]\n")

                            # Show tool calls
                            if "messages" in node_output:
                                for msg in node_output["messages"]:
                                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                                        for tool_call in msg.tool_calls:
                                            call_id = tool_call.get("id", "")
                                            if call_id not in tool_calls_shown:
                                                tool_calls_shown.add(call_id)
                                                tool_name = tool_call.get("name", "unknown")
                                                tool_args = tool_call.get("args", {})

                                                # Format args for display
                                                args_preview = ", ".join(
                                                    f"{k}={str(v)[:30]}" for k, v in list(tool_args.items())[:3]
                                                )
                                                if len(tool_args) > 3:
                                                    args_preview += "..."

                                                chat_log.write(f"[dim]    → {tool_name}({args_preview})[/dim]\n")

                    # Handle final values
                    elif event_type == "values":
                        # Capture entire state
                        workflow_state = event_data

                        # Show final content if available
                        if "messages" in event_data and event_data["messages"]:
                            last_msg = event_data["messages"][-1]
                            if hasattr(last_msg, "content") and last_msg.content:
                                # Show final output
                                if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
                                    chat_log.write(Markdown(last_msg.content))

        except asyncio.CancelledError:
            # Worker was cancelled - clean up the stream
            was_cancelled = True
            # Try to close the stream gracefully
            try:
                await stream.aclose()
            except:
                pass
            # DON'T re-raise - return the result instead
            return workflow_state, was_cancelled
        except Exception as e:
            chat_log.write(f"\n[red]Error: {str(e)}[/red]")
            raise
        finally:
            # Ensure stream is closed
            try:
                if 'stream' in locals():
                    await stream.aclose()
            except:
                pass

        return workflow_state, was_cancelled

    async def _run_agent_stream(
        self,
        agent: object,
        message: str,
        agent_name: str,
        chat_log: RichLog,
    ) -> tuple[str, bool]:
        """Run agent streaming in background (worker-compatible).

        Returns:
            tuple of (agent_response, was_cancelled)
        """
        agent_response = ""
        tool_calls_shown = set()
        was_cancelled = False

        try:
            # Create the stream
            stream = agent.astream(
                {"messages": [HumanMessage(content=message)]},
                stream_mode=["values", "updates"]
            )

            # Iterate with cancellation awareness
            async for event in stream:
                # Check for cancellation FIRST (before processing)
                if self.cancellation_requested:
                    was_cancelled = True
                    break

                # Yield control to event loop periodically
                await asyncio.sleep(0)

                # Parse the event tuple
                if isinstance(event, tuple) and len(event) == 2:
                    event_type, event_data = event

                    # Handle node updates (shows which node executed)
                    if event_type == "updates":
                        for node_name, node_output in event_data.items():
                            # Show tool execution completion
                            if node_name == "tools" and "messages" in node_output:
                                for msg in node_output["messages"]:
                                    if hasattr(msg, "name"):
                                        tool_name = msg.name

                                        # Show completion with context for router agent tools
                                        if tool_name.startswith("route_to_"):
                                            agent_name_map = {
                                                "route_to_quill": "Quill (Fundamental Analysis)",
                                                "route_to_macro_lens": "Macro Lens (Market Timing)",
                                                "route_to_risk_shield": "Risk Shield (Portfolio Risk)",
                                                "route_to_screen_forge": "Screen Forge (Stock Screening)",
                                                "route_to_earnings_whisperer": "Earnings Whisperer (Earnings Analysis)",
                                                "route_to_news_sentry": "News Sentry (Event Monitoring)",
                                                "route_to_tax_scout": "Tax Scout (Tax Optimization)",
                                                "route_to_hedge_smith": "Hedge Smith (Options Strategies)",
                                                "route_to_portfolio": "Portfolio (General Analysis)",
                                                "route_to_research": "Research (Macro Data)",
                                            }
                                            agent_display = agent_name_map.get(tool_name, tool_name)
                                            chat_log.write(f"[dim]  ✓ {agent_display} completed[/dim]\n")
                                        else:
                                            chat_log.write(f"[dim]  ✓ {tool_name} completed[/dim]\n")

                            # Show agent making tool calls
                            elif node_name == "agent" and "messages" in node_output:
                                for msg in node_output["messages"]:
                                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                                        for tool_call in msg.tool_calls:
                                            call_id = tool_call.get("id", "")
                                            if call_id not in tool_calls_shown:
                                                tool_calls_shown.add(call_id)
                                                tool_name = tool_call.get("name", "unknown")
                                                tool_args = tool_call.get("args", {})

                                                # Enhanced display for router agent tools
                                                if tool_name.startswith("route_to_"):
                                                    agent_info = {
                                                        "route_to_quill": ("Quill", "fundamental analysis, valuation, investment thesis"),
                                                        "route_to_macro_lens": ("Macro Lens", "market timing, sector allocation, economic regime"),
                                                        "route_to_risk_shield": ("Risk Shield", "portfolio risk, VAR, drawdown analysis"),
                                                        "route_to_screen_forge": ("Screen Forge", "stock screening, factor discovery"),
                                                        "route_to_earnings_whisperer": ("Earnings Whisperer", "earnings analysis, surprises"),
                                                        "route_to_news_sentry": ("News Sentry", "event monitoring, insider trading"),
                                                        "route_to_tax_scout": ("Tax Scout", "tax optimization, loss harvesting"),
                                                        "route_to_hedge_smith": ("Hedge Smith", "options strategies, portfolio protection"),
                                                        "route_to_portfolio": ("Portfolio", "general portfolio analysis"),
                                                        "route_to_research": ("Research", "macroeconomic indicators"),
                                                    }
                                                    agent_name, capabilities = agent_info.get(tool_name, (tool_name, ""))
                                                    query_preview = tool_args.get("query", "")[:40]
                                                    chat_log.write(
                                                        f"[dim]  → Calling {tool_name}[/dim]\n"
                                                    )
                                                    chat_log.write(
                                                        f"[dim]     {agent_name} analyzing: {query_preview}...[/dim]\n"
                                                    )
                                                    chat_log.write(
                                                        f"[dim]     Running specialist tools ({capabilities})...[/dim]\n"
                                                    )
                                                else:
                                                    # Format args for display (for regular tools)
                                                    args_preview = ", ".join(
                                                        f"{k}={str(v)[:30]}" for k, v in list(tool_args.items())[:3]
                                                    )
                                                    if len(tool_args) > 3:
                                                        args_preview += "..."

                                                    chat_log.write(
                                                        f"[dim]  → Calling {tool_name}({args_preview})[/dim]\n"
                                                    )

                    # Handle complete state values
                    elif event_type == "values":
                        if "messages" in event_data and event_data["messages"]:
                            last_msg = event_data["messages"][-1]
                            if hasattr(last_msg, "content") and last_msg.content:
                                # Show final response only
                                if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
                                    agent_response = last_msg.content
                                    chat_log.write(Markdown(agent_response))

        except asyncio.CancelledError:
            # Worker was cancelled - clean up the stream
            was_cancelled = True
            # Try to close the stream gracefully
            try:
                await stream.aclose()
            except:
                pass
            # DON'T re-raise - return the result instead
            return agent_response, was_cancelled
        except Exception as e:
            chat_log.write(f"\n[red]Error: {str(e)}[/red]")
            raise
        finally:
            # Ensure stream is closed
            try:
                if 'stream' in locals():
                    await stream.aclose()
            except:
                pass

        return agent_response, was_cancelled

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        text = event.value.strip()
        if not text:
            return

        # Prevent input if agents failed to initialize
        if not self.agents_initialized:
            return

        # Get input widget and chat log
        input_widget = self.query_one("#user-input", Input)
        chat_log = self.query_one("#chat-log", RichLog)

        # Clear input and disable during processing
        input_widget.value = ""
        input_widget.disabled = True
        original_placeholder = input_widget.placeholder
        input_widget.placeholder = "⏳ Processing... (Press ESC to cancel)"

        # Update footer status
        self.sub_title = "Processing..."

        # Track whether we spawned a worker (worker-based commands need cleanup via on_worker_state_changed)
        spawned_worker = False

        try:
            # Handle commands
            if text.startswith("/"):
                await self._handle_command(text, chat_log)
                # Commands like /help, /router, /examples, /api don't spawn workers
                # Only workflow commands (/optimize-tax, /protect) spawn workers via _handle_command
                # Check if a worker was spawned (it will be set in self.agent_worker)
                spawned_worker = (self.agent_worker is not None and not self.agent_worker.is_finished)
                if not spawned_worker:
                    # Simple command - re-enable input immediately
                    return
                else:
                    # Worker-based command - cleanup will happen via on_worker_state_changed
                    return

            # Display user message
            chat_log.write(f"\n[bold cyan]You:[/bold cyan] {text}\n")

            # Get agent response
            # Route through router if router_mode=True, otherwise use manual agent selection
            if self.router_mode:
                # Automatic intent-based routing
                agent = self.router_agent
                agent_name = "Router (Analyzing Intent)"
                report_type = "router_analysis"
                chat_log.write("[dim]🔀 Router analyzing your query to select appropriate agent(s)...[/dim]\n")
            else:
                # Manual agent selection
                if self.current_agent == "portfolio":
                    agent = self.portfolio_agent
                    agent_name = "Portfolio Analyst"
                    report_type = "portfolio"
                elif self.current_agent == "research":
                    agent = self.research_agent
                    agent_name = "Market Researcher"
                    report_type = "research"
                elif self.current_agent == "quill":
                    agent = self.quill_agent
                    agent_name = "Quill (Equity Research)"
                    report_type = "equity_research"
                elif self.current_agent == "screen":
                    agent = self.screen_forge_agent
                    agent_name = "Screen Forge (Equity Screening)"
                    report_type = "screening"
                elif self.current_agent == "macro":
                    agent = self.macro_lens_agent
                    agent_name = "Macro Lens (Market Strategist)"
                    report_type = "macro_analysis"
                elif self.current_agent == "earnings":
                    agent = self.earnings_whisperer_agent
                    agent_name = "Earnings Whisperer"
                    report_type = "earnings"
                elif self.current_agent == "news":
                    agent = self.news_sentry_agent
                    agent_name = "News Sentry"
                    report_type = "news_monitoring"
                elif self.current_agent == "risk":
                    agent = self.risk_shield_agent
                    agent_name = "Risk Shield Manager"
                    report_type = "risk_analysis"
                elif self.current_agent == "tax":
                    agent = self.tax_scout_agent
                    agent_name = "Tax Scout"
                    report_type = "tax_optimization"
                elif self.current_agent == "hedge":
                    agent = self.hedge_smith_agent
                    agent_name = "Hedge Smith"
                    report_type = "options_strategies"
                else:
                    agent = self.portfolio_agent
                    agent_name = "Portfolio Analyst"
                    report_type = "portfolio"

            if not agent:
                chat_log.write("[red]Error: Agent not initialized[/red]")
                return

            chat_log.write(f"[bold green]{agent_name}:[/bold green] ")

            # Start background streaming consumer for progressive disclosure
            if self.router_mode:
                self.streaming_task = asyncio.create_task(self._consume_streaming_events(chat_log))

            # Reset cancellation flag
            self.cancellation_requested = False

            # Store context for worker completion handler
            self._current_text = text
            self._current_report_type = report_type

            # Run agent in worker (non-blocking)
            self.agent_worker = self.run_worker(
                self._run_agent_stream(agent, text, agent_name, chat_log),
                name="agent_execution",
                group="agent",
                exclusive=True,
            )

            # **KEY FIX**: Don't await worker.wait() - it blocks!
            # Worker runs in background, on_worker_state_changed handles completion
            spawned_worker = True  # Agent execution always spawns a worker

        except Exception as e:
            chat_log.write(f"\n[red]Error: {str(e)}[/red]")
            # Re-enable input on error
            input_widget.disabled = False
            input_widget.placeholder = original_placeholder
            if self.router_mode:
                self.sub_title = "Router: Active | Ready"
        finally:
            # Re-enable input ONLY for non-worker commands (simple commands like /help, /router, etc.)
            # Worker-based commands will be re-enabled via on_worker_state_changed
            if not spawned_worker:
                input_widget.disabled = False
                input_widget.placeholder = original_placeholder
                if self.router_mode:
                    self.sub_title = "Router: Active | Ready"
                else:
                    agent_display_names = {
                        "portfolio": "Portfolio",
                        "research": "Research",
                        "quill": "Quill",
                        "screen": "Screen Forge",
                        "macro": "Macro Lens",
                        "earnings": "Earnings Whisperer",
                        "news": "News Sentry",
                        "risk": "Risk Shield",
                        "tax": "Tax Scout",
                        "hedge": "Hedge Smith"
                    }
                    agent_name = agent_display_names.get(self.current_agent, self.current_agent.title())
                    self.sub_title = f"Manual: {agent_name} | Ready"
                input_widget.focus()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes (completion, cancellation, errors)."""
        # Only handle our agent/workflow execution workers
        if event.worker.name not in ["agent_execution", "workflow_execution"]:
            return

        # Get UI widgets
        try:
            input_widget = self.query_one("#user-input", Input)
            chat_log = self.query_one("#chat-log", RichLog)
        except Exception:
            return  # Widget not available

        # Worker finished (success or cancellation)
        if event.state == WorkerState.SUCCESS:
            result, was_cancelled = event.worker.result

            if was_cancelled:
                chat_log.write("\n[yellow]🛑 Execution cancelled by user[/yellow]\n")
                result = None  # Don't save cancelled responses

            # Handle workflow results (dict) vs agent results (str)
            if event.worker.name == "workflow_execution" and result and not was_cancelled:
                # Workflow execution - save workflow-specific report
                workflow_type = getattr(self, "_current_workflow_type", "workflow")
                workflow_context = getattr(self, "_current_workflow_context", "")

                try:
                    # Extract state data for report
                    if workflow_type == "tax_optimization":
                        portfolio_context = workflow_context
                        tax_loss_opportunities = result.get("tax_loss_opportunities", "")
                        replacement_strategies = result.get("replacement_strategies", "")

                        # Get final plan from last message
                        final_plan = ""
                        if "messages" in result and result["messages"]:
                            last_msg = result["messages"][-1]
                            if hasattr(last_msg, "content"):
                                final_plan = last_msg.content

                        report_path = save_agent_report(
                            content=f"# Tax Optimization Strategy\n\n## Portfolio Context\n{portfolio_context}\n\n## Tax-Loss Opportunities\n{tax_loss_opportunities}\n\n## Replacement Strategies\n{replacement_strategies}\n\n## Final Action Plan\n{final_plan}",
                            report_type="tax_optimization",
                            context={"portfolio": portfolio_context[:50]},
                        )
                        chat_log.write(f"\n[dim]📄 Report saved to: {report_path}[/dim]\n")

                    elif workflow_type == "portfolio_protection":
                        portfolio_context = workflow_context
                        risk_assessment = result.get("risk_assessment", "")
                        hedging_strategies = result.get("hedging_strategies", "")

                        # Get final plan from last message
                        final_plan = ""
                        if "messages" in result and result["messages"]:
                            last_msg = result["messages"][-1]
                            if hasattr(last_msg, "content"):
                                final_plan = last_msg.content

                        report_path = save_agent_report(
                            content=f"# Portfolio Protection Strategy\n\n## Portfolio Context\n{portfolio_context}\n\n## Risk Assessment\n{risk_assessment}\n\n## Hedging Strategies\n{hedging_strategies}\n\n## Final Protection Plan\n{final_plan}",
                            report_type="portfolio_protection",
                            context={"portfolio": portfolio_context[:50]},
                        )
                        chat_log.write(f"\n[dim]📄 Report saved to: {report_path}[/dim]\n")
                except Exception as save_error:
                    chat_log.write(f"\n[dim yellow]⚠️  Could not save report: {str(save_error)}[/dim]\n")

            elif event.worker.name == "agent_execution" and result and len(result) > 200 and not was_cancelled:
                # Agent execution - save agent response report
                try:
                    # Extract context from user message (e.g., stock symbols)
                    import re
                    text = getattr(self, "_current_text", "")
                    report_type = getattr(self, "_current_report_type", "general")
                    symbols = re.findall(r'\b[A-Z]{2,5}\b', text.upper())

                    context = {"query": text[:50]}
                    if symbols:
                        context["symbol"] = symbols[0]

                    report_path = save_agent_report(
                        content=result,
                        report_type=report_type,
                        context=context,
                    )
                    chat_log.write(f"\n[dim]📄 Report saved to: {report_path}[/dim]\n")
                except Exception as save_error:
                    chat_log.write(f"\n[dim yellow]⚠️  Could not save report: {str(save_error)}[/dim]\n")

            # Stop streaming consumer task if running
            if self.streaming_task and not self.streaming_task.done():
                self.streaming_task.cancel()
                self.streaming_task = None

            # Always re-enable input
            input_widget.disabled = False
            input_widget.placeholder = "Ask about stocks or economic indicators (/examples for ideas, /help for commands)..."

            # Update status to Ready with proper mode indicator
            if self.router_mode:
                self.sub_title = "Router: Active | Ready"
            else:
                agent_display_names = {
                    "portfolio": "Portfolio",
                    "research": "Research",
                    "quill": "Quill",
                    "screen": "Screen Forge",
                    "macro": "Macro Lens",
                    "earnings": "Earnings Whisperer",
                    "news": "News Sentry",
                    "risk": "Risk Shield",
                    "tax": "Tax Scout",
                    "hedge": "Hedge Smith"
                }
                agent_name = agent_display_names.get(self.current_agent, self.current_agent.title())
                self.sub_title = f"Manual: {agent_name} | Ready"

            # Focus back on input for next query
            input_widget.focus()

        # Handle worker errors
        elif event.state == WorkerState.ERROR:
            chat_log.write(f"\n[red]Worker error: {event.worker.error}[/red]\n")

            # Cleanup and re-enable input
            if self.streaming_task and not self.streaming_task.done():
                self.streaming_task.cancel()
                self.streaming_task = None

            input_widget.disabled = False
            input_widget.placeholder = "Ask about stocks or economic indicators (/examples for ideas, /help for commands)..."
            if self.router_mode:
                self.sub_title = "Router: Active | Ready"
            input_widget.focus()

        # Handle worker cancelled
        elif event.state == WorkerState.CANCELLED:
            # Cleanup already happened via SUCCESS path (was_cancelled=True)
            pass

    async def _handle_command(self, command: str, chat_log: RichLog) -> None:
        """Handle slash commands."""
        if command.startswith("/analyze"):
            # Extract symbol from command
            parts = command.split()
            if len(parts) != 2:
                chat_log.write(
                    Markdown(
                        "\n**Usage**: `/analyze <SYMBOL>`\n\n"
                        "Example: `/analyze AAPL`\n"
                    )
                )
                return

            symbol = parts[1].upper()
            chat_log.write(f"\n[bold cyan]You:[/bold cyan] Analyze {symbol}\n")
            chat_log.write(f"[bold green]Investment Analysis Workflow:[/bold green] Starting multi-agent analysis...\n")

            try:
                # Track analysis sections for report saving
                quill_analysis = ""
                macro_context = ""
                final_recommendation = ""

                # Run the workflow
                tool_calls_shown = set()
                async for event in self.investment_workflow.astream(
                    {
                        "messages": [HumanMessage(content=f"Analyze {symbol}")],
                        "symbol": symbol,
                        "quill_analysis": "",
                        "macro_context": "",
                    },
                    stream_mode=["values", "updates"]
                ):
                    # Parse the event tuple
                    if isinstance(event, tuple) and len(event) == 2:
                        event_type, event_data = event

                        # Handle node updates
                        if event_type == "updates":
                            for node_name, node_output in event_data.items():
                                # Show which agent is working
                                if node_name == "quill":
                                    chat_log.write("[dim]  📊 Quill analyzing fundamentals...[/dim]\n")
                                elif node_name == "macro_lens":
                                    chat_log.write("[dim]  🌍 Macro Lens validating timing...[/dim]\n")
                                elif node_name == "synthesize":
                                    chat_log.write("[dim]  🎯 Synthesizing recommendation...[/dim]\n")

                                # Show tool calls
                                if "messages" in node_output:
                                    for msg in node_output["messages"]:
                                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                                            for tool_call in msg.tool_calls:
                                                call_id = tool_call.get("id", "")
                                                if call_id not in tool_calls_shown:
                                                    tool_calls_shown.add(call_id)
                                                    tool_name = tool_call.get("name", "unknown")
                                                    chat_log.write(f"[dim]    → {tool_name}[/dim]\n")

                        # Handle final values
                        elif event_type == "values":
                            # Capture state data for report
                            if "quill_analysis" in event_data:
                                quill_analysis = event_data["quill_analysis"]
                            if "macro_context" in event_data:
                                macro_context = event_data["macro_context"]

                            if "messages" in event_data and event_data["messages"]:
                                last_msg = event_data["messages"][-1]
                                if hasattr(last_msg, "content") and last_msg.content:
                                    # Show final recommendation
                                    if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
                                        final_recommendation = last_msg.content
                                        chat_log.write("\n[bold green]Final Recommendation:[/bold green]\n")
                                        chat_log.write(Markdown(final_recommendation))

                # Save the complete report
                try:
                    report_path = save_investment_report(
                        symbol=symbol,
                        final_recommendation=final_recommendation,
                        quill_analysis=quill_analysis,
                        macro_context=macro_context,
                    )
                    chat_log.write(f"\n[dim]📄 Report saved to: {report_path}[/dim]\n")
                except Exception as save_error:
                    chat_log.write(f"\n[dim yellow]⚠️  Could not save report: {str(save_error)}[/dim]\n")

            except Exception as e:
                chat_log.write(f"\n[red]Error running workflow: {str(e)}[/red]")

        elif command.startswith("/discover"):
            # Extract optional criteria from command
            parts = command.split(maxsplit=1)
            criteria = parts[1] if len(parts) > 1 else "Generate a balanced watchlist of quality growth stocks"

            chat_log.write(f"\n[bold cyan]You:[/bold cyan] Discover investment ideas\n")
            if len(parts) > 1:
                chat_log.write(f"[dim]Criteria: {criteria}[/dim]\n")
            chat_log.write(f"[bold green]Idea Discovery Workflow:[/bold green] Starting systematic screening...\n")

            try:
                # Track analysis sections for report saving
                screen_results = ""
                fundamental_analysis = ""
                risk_assessment = ""
                final_recommendations = ""

                # Run the workflow
                tool_calls_shown = set()
                async for event in self.idea_discovery_workflow.astream(
                    {
                        "messages": [HumanMessage(content=criteria)],
                        "screening_criteria": criteria,
                        "screen_results": "",
                        "fundamental_analysis": "",
                        "risk_assessment": "",
                    },
                    stream_mode=["values", "updates"]
                ):
                    # Parse the event tuple
                    if isinstance(event, tuple) and len(event) == 2:
                        event_type, event_data = event

                        # Handle node updates
                        if event_type == "updates":
                            for node_name, node_output in event_data.items():
                                # Show which agent is working
                                if node_name == "screen_forge":
                                    chat_log.write("[dim]  🔍 Screen Forge identifying candidates...[/dim]\n")
                                elif node_name == "quill":
                                    chat_log.write("[dim]  📊 Quill analyzing top picks...[/dim]\n")
                                elif node_name == "risk_shield":
                                    chat_log.write("[dim]  🛡️ Risk Shield assessing portfolio fit...[/dim]\n")
                                elif node_name == "synthesize":
                                    chat_log.write("[dim]  🎯 Synthesizing final recommendations...[/dim]\n")

                                # Show tool calls
                                if "messages" in node_output:
                                    for msg in node_output["messages"]:
                                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                                            for tool_call in msg.tool_calls:
                                                call_id = tool_call.get("id", "")
                                                if call_id not in tool_calls_shown:
                                                    tool_calls_shown.add(call_id)
                                                    tool_name = tool_call.get("name", "unknown")
                                                    chat_log.write(f"[dim]    → {tool_name}[/dim]\n")

                        # Handle final values
                        elif event_type == "values":
                            # Capture state data for report
                            if "screen_results" in event_data:
                                screen_results = event_data["screen_results"]
                            if "fundamental_analysis" in event_data:
                                fundamental_analysis = event_data["fundamental_analysis"]
                            if "risk_assessment" in event_data:
                                risk_assessment = event_data["risk_assessment"]

                            if "messages" in event_data and event_data["messages"]:
                                last_msg = event_data["messages"][-1]
                                if hasattr(last_msg, "content") and last_msg.content:
                                    # Show final recommendation
                                    if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
                                        final_recommendations = last_msg.content
                                        chat_log.write("\n[bold green]Final Recommendations:[/bold green]\n")
                                        chat_log.write(Markdown(final_recommendations))

                # Save the complete report
                try:
                    report_path = save_agent_report(
                        content=f"# Investment Idea Discovery\n\n## Screening Criteria\n{criteria}\n\n## Screen Results\n{screen_results}\n\n## Fundamental Analysis\n{fundamental_analysis}\n\n## Risk Assessment\n{risk_assessment}\n\n## Final Recommendations\n{final_recommendations}",
                        report_type="idea_discovery",
                        context={"criteria": criteria[:50]},
                    )
                    chat_log.write(f"\n[dim]📄 Report saved to: {report_path}[/dim]\n")
                except Exception as save_error:
                    chat_log.write(f"\n[dim yellow]⚠️  Could not save report: {str(save_error)}[/dim]\n")

            except Exception as e:
                chat_log.write(f"\n[red]Error running workflow: {str(e)}[/red]")

        elif command.startswith("/optimize-tax"):
            # Extract optional portfolio context from command
            parts = command.split(maxsplit=1)
            portfolio_context = parts[1] if len(parts) > 1 else "Analyze my portfolio for tax-loss harvesting opportunities"

            chat_log.write(f"\n[bold cyan]You:[/bold cyan] Optimize tax strategy\n")
            if len(parts) > 1:
                chat_log.write(f"[dim]Portfolio: {portfolio_context}[/dim]\n")
            chat_log.write(f"[bold green]Tax Optimization Workflow:[/bold green] Starting tax-loss harvesting analysis...\n")

            # Prepare workflow state
            initial_state = {
                "messages": [HumanMessage(content=portfolio_context)],
                "portfolio_context": portfolio_context,
                "tax_loss_opportunities": "",
                "replacement_strategies": "",
            }

            # Node status messages
            node_messages = {
                "tax_scout": "💰 Tax Scout identifying loss harvesting opportunities...",
                "hedge_smith": "🛡️ Hedge Smith designing replacement strategies...",
                "synthesize": "🎯 Synthesizing final tax optimization plan...",
            }

            # Disable input and show processing state
            input_widget = self.query_one("#user-input", Input)
            input_widget.disabled = True
            input_widget.placeholder = "⏳ Processing... (Press ESC to cancel)"
            self.sub_title = "Processing..."

            # Reset cancellation flag
            self.cancellation_requested = False

            # Store context for completion handler
            self._current_workflow_type = "tax_optimization"
            self._current_workflow_context = portfolio_context

            # Run workflow in worker (non-blocking)
            self.agent_worker = self.run_worker(
                self._run_workflow_stream(
                    self.tax_optimization_workflow,
                    initial_state,
                    "Tax Optimization",
                    chat_log,
                    node_messages,
                ),
                name="workflow_execution",
                group="workflow",
                exclusive=True,
            )

        elif command.startswith("/protect"):
            # Extract optional portfolio context from command
            parts = command.split(maxsplit=1)
            portfolio_context = parts[1] if len(parts) > 1 else "Analyze my portfolio for hedging opportunities"

            chat_log.write(f"\n[bold cyan]You:[/bold cyan] Protect portfolio\n")
            if len(parts) > 1:
                chat_log.write(f"[dim]Portfolio: {portfolio_context}[/dim]\n")
            chat_log.write(f"[bold green]Portfolio Protection Workflow:[/bold green] Starting risk assessment and hedging analysis...\n")

            # Prepare workflow state
            initial_state = {
                "messages": [HumanMessage(content=portfolio_context)],
                "portfolio_context": portfolio_context,
                "risk_assessment": "",
                "hedging_strategies": "",
            }

            # Node status messages
            node_messages = {
                "risk_shield": "🛡️ Risk Shield analyzing portfolio exposures...",
                "hedge_smith": "⚔️ Hedge Smith designing protective strategies...",
                "synthesize": "🎯 Synthesizing final protection plan...",
            }

            # Disable input and show processing state
            input_widget = self.query_one("#user-input", Input)
            input_widget.disabled = True
            input_widget.placeholder = "⏳ Processing... (Press ESC to cancel)"
            self.sub_title = "Processing..."

            # Reset cancellation flag
            self.cancellation_requested = False

            # Store context for completion handler
            self._current_workflow_type = "portfolio_protection"
            self._current_workflow_context = portfolio_context

            # Run workflow in worker (non-blocking)
            self.agent_worker = self.run_worker(
                self._run_workflow_stream(
                    self.portfolio_protection_workflow,
                    initial_state,
                    "Portfolio Protection",
                    chat_log,
                    node_messages,
                ),
                name="workflow_execution",
                group="workflow",
                exclusive=True,
            )

        elif command == "/api":
            chat_log.write("\n[bold cyan]Checking API Status...[/bold cyan]\n")
            chat_log.write("[dim]Testing connectivity to all configured APIs...\n\n[/dim]")

            try:
                # Run API checks
                results = await check_all_apis()

                # Create Rich table
                table = Table(
                    title="API Status Report",
                    show_header=True,
                    header_style="bold magenta",
                    show_lines=True,
                )
                table.add_column("API Provider", style="cyan", width=18)
                table.add_column("Status", width=18)
                table.add_column("Details", style="dim", width=40)

                # Add rows
                for result in results:
                    # Color code status
                    status = result["status"]
                    if "✅" in status:
                        status_styled = f"[green]{status}[/green]"
                    elif "❌" in status:
                        status_styled = f"[red]{status}[/red]"
                    elif "⚠️" in status:
                        status_styled = f"[yellow]{status}[/yellow]"
                    else:
                        status_styled = f"[dim]{status}[/dim]"

                    table.add_row(
                        result["api"],
                        status_styled,
                        result["details"]
                    )

                # Display table
                chat_log.write(table)

                # Add summary
                working = sum(1 for r in results if "✅" in r["status"])
                failed = sum(1 for r in results if "❌" in r["status"])
                not_configured = sum(1 for r in results if "⚪" in r["status"])

                chat_log.write(
                    Markdown(
                        f"\n**Summary:** {working} working • {failed} failed • {not_configured} not configured\n\n"
                        f"💡 **Tips:**\n"
                        f"- Failed APIs: Check your `.env` file for correct API keys\n"
                        f"- Not configured: Optional - get free keys to unlock more features\n"
                        f"- Rate limited: Wait a few minutes and try again\n\n"
                        f"Run `python scripts/validate_newsapi_key.py` to validate NewsAPI.org specifically.\n"
                    )
                )

            except Exception as e:
                chat_log.write(f"\n[red]Error checking APIs: {str(e)}[/red]")

        elif command.startswith("/router"):
            # Handle router toggle command
            parts = command.split()
            if len(parts) == 1:
                # Show current router status
                status = "ON" if self.router_mode else "OFF"
                chat_log.write(
                    Markdown(
                        f"\n**Router Status:** {status}\n\n"
                        f"**Usage:**\n"
                        f"- `/router on` - Enable automatic intent-based routing\n"
                        f"- `/router off` - Disable automatic routing (manual agent selection)\n\n"
                        f"When router is ON, your queries are automatically routed to the appropriate specialist agent(s).\n"
                        f"When router is OFF, you must manually select agents using `/portfolio`, `/quill`, etc.\n"
                    )
                )
            elif len(parts) == 2:
                mode = parts[1].lower()
                if mode == "on":
                    self.router_mode = True
                    self.sub_title = "Router: Active | Ready"
                    chat_log.write("\n[green]✓ Router enabled - automatic intent-based routing activated![/green]\n")
                    chat_log.write("[dim]Your queries will be automatically routed to the appropriate specialist agent(s).[/dim]\n")
                elif mode == "off":
                    self.router_mode = False
                    agent_display_names = {
                        "portfolio": "Portfolio",
                        "research": "Research",
                        "quill": "Quill",
                        "screen": "Screen Forge",
                        "macro": "Macro Lens",
                        "earnings": "Earnings Whisperer",
                        "news": "News Sentry",
                        "risk": "Risk Shield",
                        "tax": "Tax Scout",
                        "hedge": "Hedge Smith"
                    }
                    agent_name = agent_display_names.get(self.current_agent, self.current_agent.title())
                    self.sub_title = f"Manual: {agent_name} | Ready"
                    chat_log.write("\n[green]✓ Router disabled - manual agent selection mode[/green]\n")
                    chat_log.write(f"[dim]Currently using: {agent_name}. Use `/portfolio`, `/quill`, etc. to switch agents.[/dim]\n")
                else:
                    chat_log.write(f"\n[yellow]Invalid option: {mode}. Use 'on' or 'off'.[/yellow]\n")
            else:
                chat_log.write("\n[yellow]Usage: /router [on|off][/yellow]\n")

        elif command == "/help":
            chat_log.write(
                Markdown(
                    "\n**Available Commands:**\n\n"
                    "**Router Control:**\n"
                    "- `/router on|off` - Toggle automatic intent-based routing (default: ON)\n\n"
                    "**Manual Agent Selection** (disables router):\n"
                    "- `/portfolio` - Portfolio analysis agent\n"
                    "- `/research` - Market research agent\n"
                    "- `/quill` - Quill equity research agent\n"
                    "- `/screen` - Screen Forge screening agent\n"
                    "- `/macro` - Macro Lens market strategist\n"
                    "- `/earnings` - Earnings Whisperer earnings analyst\n"
                    "- `/news` - News Sentry event monitoring agent\n"
                    "- `/risk` - Risk Shield portfolio risk manager\n"
                    "- `/tax` - Tax Scout tax optimization agent\n"
                    "- `/hedge` - Hedge Smith options strategies agent\n\n"
                    "**Multi-Agent Workflows:**\n"
                    "- `/analyze <SYMBOL>` - Complete investment analysis (Quill + Macro Lens + News Sentry + Risk Shield + Tax Scout)\n"
                    "- `/discover [CRITERIA]` - Systematic idea generation (Screen Forge + Quill + Risk Shield)\n"
                    "- `/protect [PORTFOLIO]` - Portfolio hedging workflow (Risk Shield + Hedge Smith)\n"
                    "- `/optimize-tax [PORTFOLIO]` - Tax-loss harvesting workflow (Tax Scout + Hedge Smith)\n\n"
                    "**Utilities:**\n"
                    "- `/api` - Check API connectivity and status\n"
                    "- `/examples` - Show example prompts\n"
                    "- `/clear` - Clear chat history\n"
                    "- `/quit` - Exit the application\n"
                    "- `/help` - Show this help message\n\n"
                    "**💡 Tip:** With router ON (default), just ask naturally - no need to select agents!\n"
                )
            )
        elif command == "/portfolio":
            self.router_mode = False
            self.current_agent = "portfolio"
            self.sub_title = "Manual: Portfolio | Ready"
            chat_log.write("\n[green]✓ Switched to Portfolio Analysis agent (manual mode)[/green]\n")
        elif command == "/research":
            self.router_mode = False
            self.current_agent = "research"
            self.sub_title = "Manual: Research | Ready"
            chat_log.write("\n[green]✓ Switched to Market Research agent (manual mode)[/green]\n")
        elif command == "/quill":
            self.router_mode = False
            self.current_agent = "quill"
            self.sub_title = "Manual: Quill | Ready"
            chat_log.write("\n[green]✓ Switched to Quill (Equity Research) agent (manual mode)[/green]\n")
        elif command == "/screen":
            self.router_mode = False
            self.current_agent = "screen"
            self.sub_title = "Manual: Screen Forge | Ready"
            chat_log.write("\n[green]✓ Switched to Screen Forge (Equity Screening) agent (manual mode)[/green]\n")
        elif command == "/macro":
            self.router_mode = False
            self.current_agent = "macro"
            self.sub_title = "Manual: Macro Lens | Ready"
            chat_log.write("\n[green]✓ Switched to Macro Lens (Market Strategist) agent (manual mode)[/green]\n")
        elif command == "/earnings":
            self.router_mode = False
            self.current_agent = "earnings"
            self.sub_title = "Manual: Earnings Whisperer | Ready"
            chat_log.write("\n[green]✓ Switched to Earnings Whisperer agent (manual mode)[/green]\n")
        elif command == "/news":
            self.router_mode = False
            self.current_agent = "news"
            self.sub_title = "Manual: News Sentry | Ready"
            chat_log.write("\n[green]✓ Switched to News Sentry (Event Monitoring) agent (manual mode)[/green]\n")
        elif command == "/risk":
            self.router_mode = False
            self.current_agent = "risk"
            self.sub_title = "Manual: Risk Shield | Ready"
            chat_log.write("\n[green]✓ Switched to Risk Shield (Portfolio Risk Manager) agent (manual mode)[/green]\n")
        elif command == "/tax":
            self.router_mode = False
            self.current_agent = "tax"
            self.sub_title = "Manual: Tax Scout | Ready"
            chat_log.write("\n[green]✓ Switched to Tax Scout (Tax Optimization) agent (manual mode)[/green]\n")
        elif command == "/hedge":
            self.router_mode = False
            self.current_agent = "hedge"
            self.sub_title = "Manual: Hedge Smith | Ready"
            chat_log.write("\n[green]✓ Switched to Hedge Smith (Options Strategies) agent (manual mode)[/green]\n")
        elif command == "/examples":
            # Show examples for current agent
            if self.current_agent == "portfolio":
                examples = PORTFOLIO_EXAMPLES
                agent_name = "Portfolio Analysis"
            elif self.current_agent == "research":
                examples = RESEARCH_EXAMPLES
                agent_name = "Market Research"
            elif self.current_agent == "quill":
                examples = QUILL_EXAMPLES
                agent_name = "Quill (Equity Research)"
            elif self.current_agent == "screen":
                examples = SCREEN_FORGE_EXAMPLES
                agent_name = "Screen Forge (Equity Screening)"
            elif self.current_agent == "macro":
                examples = MACRO_LENS_EXAMPLES
                agent_name = "Macro Lens (Market Strategist)"
            elif self.current_agent == "earnings":
                examples = EARNINGS_WHISPERER_EXAMPLES
                agent_name = "Earnings Whisperer"
            elif self.current_agent == "news":
                examples = NEWS_SENTRY_EXAMPLES
                agent_name = "News Sentry (Event Monitoring)"
            elif self.current_agent == "risk":
                examples = RISK_SHIELD_EXAMPLES
                agent_name = "Risk Shield (Portfolio Risk Manager)"
            elif self.current_agent == "tax":
                examples = TAX_SCOUT_EXAMPLES
                agent_name = "Tax Scout (Tax Optimization)"
            elif self.current_agent == "hedge":
                examples = HEDGE_SMITH_EXAMPLES
                agent_name = "Hedge Smith (Options Strategies)"
            else:
                examples = PORTFOLIO_EXAMPLES
                agent_name = "Portfolio Analysis"

            # Randomly select 4 examples to show
            selected_examples = random.sample(examples, min(4, len(examples)))

            examples_text = "\n".join(f"{i+1}. {ex}" for i, ex in enumerate(selected_examples))

            # Add workflow examples
            workflow_text = "\n".join(f"{i+1}. {ex}" for i, ex in enumerate(WORKFLOW_EXAMPLES))

            chat_log.write(
                Markdown(
                    f"\n**Example prompts for {agent_name} agent:**\n\n"
                    f"{examples_text}\n\n"
                    f"**Multi-Agent Workflows:**\n\n"
                    f"{workflow_text}\n\n"
                    f"💡 Try copying one of these or ask your own question!\n"
                )
            )
        elif command == "/clear":
            self.action_clear()
        elif command == "/quit":
            self.exit()
        else:
            chat_log.write(f"\n[yellow]Unknown command: {command}[/yellow]\n")

    def action_cancel(self) -> None:
        """Cancel the currently running agent execution (ESC key)."""
        if self.agent_worker and not self.agent_worker.is_finished:
            self.cancellation_requested = True
            try:
                chat_log = self.query_one("#chat-log", RichLog)
                chat_log.write("\n[yellow]⚠️  Cancellation requested - stopping agent...[/yellow]\n")
            except Exception:
                pass
            # Cancel the worker
            self.agent_worker.cancel()

    def action_clear(self) -> None:
        """Clear the chat log."""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.clear()
        chat_log.write(
            Markdown("# Chat Cleared\n\nType your question or use /help for commands.")
        )


async def run_tui() -> None:
    """Run the TUI application."""
    app = ChatUI()
    await app.run_async()
