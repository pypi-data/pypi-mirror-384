<div align="center">

# 🧠 Navam Invest

**AI-Powered Investment Intelligence for Retail Investors**

[![PyPI version](https://badge.fury.io/py/navam-invest.svg)](https://badge.fury.io/py/navam-invest)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/navam-invest)](https://pepy.tech/project/navam-invest)

Institutional-grade portfolio intelligence powered by **10 specialized AI agents**
Built on [LangGraph](https://langchain-ai.github.io/langgraph/) • Powered by [Anthropic Claude](https://www.anthropic.com/claude)

[Quick Start](#-quick-start) •
[Features](#-key-features) •
[AI Agents](#-specialized-ai-agents) •
[Documentation](#-documentation) •
[Examples](#-example-workflows)

</div>

---

## 🎯 What is Navam Invest?

**Replace $1,000-$10,000/year wealth management fees with AI agents that research, analyze, and explain investment decisions in plain English.**

Navam Invest is an **open-source AI investment advisory platform** designed for retail investors managing $50K-$1M portfolios. Instead of paying 1% AUM fees, you get a **team of 10 specialized AI agents** with **automatic intent-based routing**—all running locally with your API keys, using free public data.

### Why Choose Navam Invest?

<table>
<tr>
<td width="50%">

**🏦 Institutional Intelligence, Retail Access**
- 10 specialized AI agents (equity research, earnings analysis, risk management, tax optimization, options strategies)
- **Automatic routing**: Just ask naturally—no need to know which agent to use
- Multi-agent workflows combining bottom-up + top-down analysis

</td>
<td width="50%">

**💰 Zero Lock-In, Maximum Value**
- Core features work with 100% free APIs (Yahoo Finance + SEC EDGAR)
- No subscriptions, no recurring fees
- Your data stays yours—runs completely locally

</td>
</tr>
<tr>
<td width="50%">

**🔍 Transparent & Explainable**
- Watch AI agents reason in real-time with progressive streaming
- Full audit trails of tool calls and data sources
- Educational explanations, not black-box recommendations

</td>
<td width="50%">

**⚡ Production-Ready Today**
- Interactive terminal UI (TUI) with real-time agent streaming
- 32 tools across 9 APIs (3 require zero setup)
- Auto-save reports, multi-agent orchestration

</td>
</tr>
</table>

---

## ✨ Key Features

### 🔀 Automatic Intent-Based Routing (NEW in v0.1.36)

**No more manual agent switching!** Just ask your question naturally:

```bash
navam invest

# Simply ask - the router automatically selects the right agent(s)
> Should I invest in AAPL?
# → Router analyzes intent
# → Routes to Quill (fundamentals) + Macro Lens (timing) + Risk Shield (exposure)
# → Synthesizes comprehensive recommendation

> Find undervalued tech stocks with strong earnings momentum
# → Router detects screening + earnings intent
# → Routes to Screen Forge + Earnings Whisperer

> Protect my NVDA position with options
# → Router detects hedging intent
# → Routes to Hedge Smith for options strategies
```

**Power users** can still use manual commands (`/quill`, `/hedge`, `/risk`) for direct agent control.

### 🤖 10 Specialized AI Agents

Each agent is purpose-built with curated tools and expert system prompts:

| Agent | Purpose | Tools | Example Query |
|-------|---------|-------|---------------|
| **[Quill](#-quill---equity-research-analyst)** | Deep fundamental research | 36 | "Analyze AAPL with DCF valuation and insider activity" |
| **[Earnings Whisperer](#-earnings-whisperer---earnings-specialist)** | Earnings surprise analysis | 14 | "Find post-earnings drift opportunities in NVDA" |
| **[Screen Forge](#-screen-forge---equity-screener)** | Systematic stock screening | 15 | "Screen for stocks with 3+ consecutive earnings beats" |
| **[Macro Lens](#-macro-lens---market-strategist)** | Top-down macro analysis | 13 | "What's the current economic regime for tech stocks?" |
| **[News Sentry](#-news-sentry---real-time-event-monitor)** | Real-time event detection | 13 | "Alert me to material 8-K filings and insider trades" |
| **[Risk Shield](#-risk-shield---portfolio-risk-manager)** | Portfolio risk management | 18 | "Calculate VAR and analyze concentration risks" |
| **[Tax Scout](#-tax-scout---tax-optimization-specialist)** | Tax-loss harvesting | 12 | "Identify tax-loss harvesting opportunities" |
| **[Hedge Smith](#-hedge-smith---options-strategist)** | Options strategies | 13 | "Design a protective collar for my AAPL position" |
| **Atlas** | Strategic asset allocation | 12 | "Create an IPS for $200K portfolio" |
| **Portfolio/Research** | Legacy general-purpose | 24/10 | Backward compatibility |

### 🔀 Multi-Agent Workflows (NEW in v0.1.37)

**Agents don't just answer questions—they collaborate in sophisticated workflows:**

#### `/analyze` - Comprehensive Investment Analysis (5 Agents)
```bash
/analyze MSFT

# 1. Quill performs bottom-up fundamental analysis
#    → Financial health, valuation, earnings trends
# 2. News Sentry checks for material events
#    → 8-K filings, insider trading, breaking news
# 3. Macro Lens validates with top-down regime analysis
#    → Economic cycles, sector positioning, yield curve
# 4. Risk Shield assesses portfolio fit
#    → Concentration risk, VAR, correlation analysis
# 5. Tax Scout evaluates tax implications
#    → Wash-sale checks, holding period optimization
# 6. Final synthesis combines all perspectives
#    → BUY/HOLD/SELL with confidence level and reasoning
```

#### `/discover` - Systematic Idea Generation (3 Agents) **NEW!**
```bash
/discover quality growth stocks with strong margins

# 1. Screen Forge identifies 10-15 candidates
#    → Factor-based screening, momentum analysis
# 2. Quill analyzes top 3-5 picks
#    → Deep fundamental analysis, valuation
# 3. Risk Shield assesses portfolio fit
#    → Position sizing, concentration analysis
# 4. Final synthesis ranks candidates
#    → Actionable recommendations with entry points
```

**Result**: Institutional-quality investment analysis in seconds, not hours.

### 📊 Free & Premium Data Sources

**32 tools across 9 APIs** (3 completely free, 6 with generous free tiers):

| Data Source | Coverage | Free Tier | Cost |
|-------------|----------|-----------|------|
| **Yahoo Finance** 🆓 | Real-time quotes, earnings, analyst ratings, ownership | Unlimited | **FREE** |
| **SEC EDGAR** 🆓 | Corporate filings (10-K, 10-Q, 8-K), insider transactions | Unlimited | **FREE** |
| **U.S. Treasury** 🆓 | Yield curves, treasury rates | Unlimited | **FREE** |
| **Tiingo** | 5-year historical fundamentals | 50 symbols/hr | Optional |
| **Finnhub** | News/social sentiment, insider trades | 60 calls/min | Optional |
| **Alpha Vantage** | Stock prices, company overviews | 25-500 calls/day | Optional |
| **FRED** | Economic indicators (GDP, CPI, unemployment) | Unlimited | Optional |
| **NewsAPI.org** | Market news, headlines | 1,000 calls/day | Optional |
| **Anthropic Claude** | AI reasoning engine (Sonnet 4.5) | Pay-as-you-go | **Required** |

**💡 80% of functionality works with just Yahoo Finance + SEC EDGAR (no API keys needed!)**

### 💬 Modern Terminal UI with Progressive Streaming

**Built with Textual framework** for a responsive, beautiful CLI experience:

- ✅ **Progressive streaming**: Watch sub-agent tool calls appear in real-time (NEW in v0.1.36)
- ✅ **Real-time reasoning**: See agents think and make decisions live
- ✅ **Smart input management**: Auto-disabled during processing (no duplicate queries)
- ✅ **Tool execution tracking**: See exactly which data sources agents are calling
- ✅ **Multi-agent progress**: Visual workflow transitions with status updates
- ✅ **Markdown rendering**: Tables, code blocks, syntax highlighting
- ✅ **Auto-save reports**: All responses >200 chars saved to `reports/` directory
- ✅ **Keyboard shortcuts**: `Ctrl+C` (clear), `Ctrl+Q` (quit)

---

## 🚀 Quick Start

### Installation

**Requirements**: Python 3.9+ and an Anthropic API key

```bash
# Install from PyPI
pip install navam-invest

# Start the interactive terminal
navam invest
```

### 5-Minute Setup

**1. Create environment file:**

```bash
cp .env.example .env
```

**2. Add your Anthropic API key** (required):

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your free key at [console.anthropic.com](https://console.anthropic.com/)
💰 **Cost**: ~$3-15/month for typical usage (pay-as-you-go)

**3. Optional: Add free-tier API keys** (recommended for full features):

```bash
# Optional - all have generous free tiers
FRED_API_KEY=your_key_here          # Unlimited economic data
TIINGO_API_KEY=your_key_here        # 50 symbols/hr historical data
FINNHUB_API_KEY=your_key_here       # 60 calls/min sentiment data
NEWSAPI_API_KEY=your_key_here       # 1,000 calls/day news
ALPHA_VANTAGE_API_KEY=your_key_here # 25-500 calls/day quotes
```

[Get free API keys →](docs/user-guide/getting-started.md#get-free-api-keys)

**4. Verify setup:**

```bash
navam invest
> /api
# Shows status table: ✅ working / ❌ failed / ⚪ not configured
```

### First Query

```bash
navam invest

# NEW: Just ask naturally - automatic routing!
> Should I invest in Apple stock right now?
# Router automatically selects Quill, Macro Lens, and Risk Shield

> Find undervalued tech companies with strong earnings
# Router automatically selects Screen Forge and Earnings Whisperer

> How can I reduce my tax bill before year-end?
# Router automatically selects Tax Scout

# Or use workflows for systematic analysis
> /analyze MSFT
# Comprehensive 5-agent investment analysis

> /discover dividend stocks with P/E under 20
# Systematic 3-agent idea generation workflow

# Or use manual commands for specific agents (power users)
> /quill
> Analyze Microsoft's earnings trends and institutional ownership

> /macro
> What's the current economic regime for tech stocks?

> /risk
> Calculate VAR for my portfolio and identify concentration risks
```

**🎓 New to Navam Invest?** Check the [Getting Started Guide](docs/user-guide/getting-started.md) for detailed walkthroughs.

---

## 🤖 Specialized AI Agents

### ⭐ Quill - Equity Research Analyst

**Deep fundamental analysis & investment thesis development**

<details>
<summary><b>View Capabilities & Examples</b></summary>

**What Quill Does**:
- 📊 **DCF Valuation**: Discounted cash flow models with sensitivity analysis
- 📈 **5-Year Trends**: Revenue growth, margins, ROIC, FCF, debt ratios
- 💰 **Earnings Analysis**: Historical beats, estimates, surprise patterns
- 🎯 **Analyst Coverage**: Consensus ratings, price targets, upgrades/downgrades
- 🏢 **Ownership Tracking**: Institutional holders, insider transactions (Form 4)
- 📋 **SEC Filings**: 10-K/10-Q deep-dives, 8-K material events, XBRL data
- 💵 **Dividend Analysis**: Yield, payout sustainability, history
- 📰 **News Validation**: Company-specific news with sentiment

**Tools**: 36 specialized tools across Yahoo Finance, SEC EDGAR, Tiingo, Finnhub, NewsAPI

**Example Queries**:
```
# Automatic routing (just ask naturally)
> Analyze NVDA fundamentals and give me a buy/hold/sell recommendation

# Manual mode (power users)
> /quill
> Deep dive on AAPL: recent earnings, institutional ownership changes, and DCF valuation
```

**Expected Output**: 5-section investment thesis with BUY/HOLD/SELL recommendation, fair value range, key catalysts, and risk factors.

</details>

### 📊 Earnings Whisperer - Earnings Specialist

**Earnings surprise analysis & post-earnings drift detection**

<details>
<summary><b>View Capabilities & Examples</b></summary>

**What Earnings Whisperer Does**:
- 🎯 **Historical Tracking**: 4-8 quarter earnings surprise analysis
- 📈 **Drift Detection**: 1-3 day post-earnings momentum patterns
- 🔄 **Analyst Revisions**: Estimate changes post-earnings
- ✅ **Quality Assessment**: Revenue vs EPS beats, non-recurring items
- 📅 **Calendar Monitoring**: Upcoming earnings with probability scoring
- 🏆 **Pattern Recognition**: Consistent beaters, accelerating growth, quality issues
- 💹 **Trading Signals**: BUY/HOLD/SELL based on drift probability

**Tools**: 14 specialized tools across Yahoo Finance, SEC, Finnhub

**Example Queries**:
```
# Automatic routing
> Is there a post-earnings drift opportunity in META after recent earnings?

# Manual mode
> /earnings
> Analyze TSLA's last 6 quarters - average beat percentage and drift patterns
```

**Expected Output**: Earnings momentum scorecard with drift probability, pattern analysis, and trading recommendation.

</details>

### 🔍 Screen Forge - Equity Screener

**Systematic stock discovery & idea generation**

<details>
<summary><b>View Capabilities & Examples</b></summary>

**What Screen Forge Does**:
- 📐 **Multi-Factor Screening**: Value, growth, quality, momentum factors
- 🎯 **Systematic Discovery**: Weekly watchlist generation with ranking
- 📈 **Earnings Momentum**: Filter for consistent earnings beaters
- ⬆️ **Analyst Activity**: Upgrade/downgrade-based screening
- 💬 **Sentiment Validation**: News and social sentiment checks
- 🔗 **Seamless Handoff**: Passes top candidates to Quill for deep-dive

**Tools**: 15 specialized tools across Yahoo Finance, Finnhub, Alpha Vantage

**Example Queries**:
```
# Automatic routing
> Find undervalued growth stocks with strong earnings momentum

# Manual mode
> /screen
> Screen for stocks with P/E under 15, 3+ consecutive earnings beats, and positive sentiment
```

**Expected Output**: Ranked table of 10-20 candidates with screening criteria, key metrics, and suggested next steps.

</details>

### 🌍 Macro Lens - Market Strategist

**Top-down economic analysis & regime identification**

<details>
<summary><b>View Capabilities & Examples</b></summary>

**What Macro Lens Does**:
- 🔄 **Economic Cycles**: 4-phase regime analysis (early/mid/late expansion, recession)
- 📈 **Yield Curve**: Interpretation and recession signal detection (inversions)
- 🏭 **Sector Allocation**: Macro-driven positioning guidance
- 📊 **Factor Recommendations**: Value vs growth, size, volatility tilts
- 📉 **Macro Tracking**: Inflation, GDP, employment, Fed policy
- 📊 **Market Indices**: S&P 500, Nasdaq, VIX correlation analysis
- 💹 **Interest Rates**: Fed funds, treasury rates, credit spreads

**Tools**: 13 specialized tools across FRED, U.S. Treasury, Yahoo Finance, NewsAPI

**Example Queries**:
```
# Automatic routing
> What's the current market environment for tech stocks?

# Manual mode
> /macro
> Analyze the yield curve - is it signaling recession? Which sectors should I overweight?
```

**Expected Output**: Regime assessment with sector allocation matrix, factor positioning, and macro risk scenarios.

</details>

### 🗞️ News Sentry - Real-Time Event Monitor

**Material event detection & breaking news alerts**

<details>
<summary><b>View Capabilities & Examples</b></summary>

**What News Sentry Does**:
- 📋 **8-K Monitoring**: Material corporate events (M&A, management changes, bankruptcy)
- 📝 **Form 4 Tracking**: Insider buying/selling by officers and directors
- 📰 **Breaking News**: Real-time company-specific news with sentiment
- 📊 **Analyst Actions**: Rating changes, price target updates
- 🎯 **Event Prioritization**: CRITICAL/HIGH/MEDIUM/LOW urgency scoring
- ⚡ **Rapid Response**: Detect market-moving events as they happen

**Tools**: 13 specialized tools across SEC EDGAR, NewsAPI, Finnhub, Yahoo Finance

**Example Queries**:
```
# Automatic routing
> Any material events or insider activity at TSLA recently?

# Manual mode
> /news
> Monitor AAPL for 8-K filings, insider transactions, and breaking news in last 7 days
```

**Expected Output**: Prioritized event list with urgency levels, event details, and recommended actions.

</details>

### 🛡️ Risk Shield - Portfolio Risk Manager

**Comprehensive risk analysis & exposure monitoring**

<details>
<summary><b>View Capabilities & Examples</b></summary>

**What Risk Shield Does**:
- 📊 **Concentration Analysis**: Sector, geographic, single-stock exposures
- 📉 **Drawdown Metrics**: Historical drawdowns, peak-to-trough, recovery periods
- 💹 **VAR Calculations**: Value at Risk (95%, 99% confidence levels)
- 🎲 **Scenario Testing**: Stress tests against historical crises (2008, 2020)
- 🔗 **Correlation Analysis**: Diversification quality, correlation matrices
- 📈 **Volatility Metrics**: Portfolio vol, beta, Sharpe, Sortino ratios
- ⚠️ **Limit Breach Detection**: Position size, sector concentration thresholds
- 🛠️ **Risk Mitigation**: Hedging strategies, rebalancing recommendations

**Tools**: 18 specialized tools across market data, fundamentals, macro indicators, treasury data

**Example Queries**:
```
# Automatic routing
> Analyze my portfolio risk and recommend mitigation strategies

# Manual mode
> /risk
> Calculate VAR at 95% and 99%, identify sector concentration risks, stress test against 2008 crisis
```

**Expected Output**: Risk scorecard (1-10 scale), concentration analysis, VAR metrics, stress test results, and actionable mitigation recommendations.

</details>

### 💰 Tax Scout - Tax Optimization Specialist

**Tax-loss harvesting & wash-sale compliance**

<details>
<summary><b>View Capabilities & Examples</b></summary>

**What Tax Scout Does**:
- 💸 **Tax-Loss Harvesting**: Identify positions with unrealized losses
- ⏰ **Wash-Sale Compliance**: 30-day rule monitoring (IRS Section 1091)
- 🔄 **Replacement Candidates**: Find substantially different securities
- 📊 **Capital Gains Analysis**: Short-term vs long-term tracking
- 📅 **Year-End Planning**: Strategic positioning before Dec 31 deadline
- ⚖️ **Tax-Efficient Rebalancing**: Minimize gains during portfolio adjustments
- 📋 **Lot-Level Analysis**: FIFO, LIFO, specific lot identification

**Tools**: 12 specialized tools for portfolio data, market pricing, fundamentals

**Example Queries**:
```
# Automatic routing
> How can I reduce my tax bill before year-end?

# Manual mode
> /tax
> Identify tax-loss harvesting opportunities with >5% unrealized losses, check wash-sale violations
```

**Expected Output**: TLH opportunities table with tax savings estimates, wash-sale violations, replacement candidates, and year-end action plan.

</details>

### 🎯 Hedge Smith - Options Strategist

**Options strategies for portfolio protection & yield enhancement**

<details>
<summary><b>View Capabilities & Examples</b></summary>

**What Hedge Smith Does**:
- 🛡️ **Protective Collars**: Simultaneous OTM put purchase + OTM call sale for downside protection with capped upside
- 💰 **Covered Calls**: Sell call options against existing holdings to generate premium income
- 📉 **Protective Puts**: Portfolio insurance through put purchases with cost/benefit optimization
- 💵 **Cash-Secured Puts**: Generate income while waiting to acquire stock at lower price
- 🎯 **Strike Selection**: Optimal strike selection (5-10% OTM for protection, 10-20% for income)
- 📅 **Expiration Optimization**: 30-45 days for theta decay, 60-90 days for protection
- 📊 **Options Greeks**: Delta, gamma, theta, vega, IV percentile analysis
- ⚖️ **Risk/Reward Profiling**: Max profit, max loss, breakeven, probability estimates

**Tools**: 13 specialized tools for options chain data, market data, fundamentals, volatility

**Example Queries**:
```
# Automatic routing
> How can I protect my AAPL position with options?

# Manual mode
> /hedge
> I hold 500 shares of AAPL at $180 cost, currently $200. Design a protective collar for 45-day expiration.
```

**Expected Output**: Complete strategy specification with specific strikes, premiums, Greeks, risk/reward analysis, and exit strategy.

</details>

---

## 💡 Example Workflows

### Multi-Agent Investment Analysis

**Command**: `/analyze <SYMBOL>` or just ask naturally

**What Happens**:

1. **Quill** performs bottom-up fundamental analysis
2. **News Sentry** checks for material events and insider trading
3. **Macro Lens** validates with top-down economic context
4. **Risk Shield** assesses portfolio fit and concentration risks
5. **Tax Scout** evaluates tax implications and timing
6. **Synthesis** combines all perspectives into final recommendation

<details>
<summary><b>Example: Comprehensive MSFT Analysis (click to expand)</b></summary>

```
You: Should I invest in Microsoft?

🔀 Router analyzing your query to select appropriate agent(s)...

Router (Analyzing Intent):
→ Detected investment decision query
→ Routing to Quill (fundamental analysis)
→ Routing to News Sentry (event monitoring)
→ Routing to Macro Lens (market timing validation)
→ Routing to Risk Shield (exposure assessment)
→ Routing to Tax Scout (tax implications)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUILL: FUNDAMENTAL ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quill (Equity Research):
  → Calling route_to_quill
     Quill analyzing: Should I invest in Microsoft...
     Running specialist tools (fundamental analysis, valuation, investment thesis)...
      → get_quote({'symbol': 'MSFT'})
      → get_earnings_history({'symbol': 'MSFT'})
      → get_analyst_recommendations({'symbol': 'MSFT'})
      → get_financials({'symbol': 'MSFT'})
  ✓ Quill (Fundamental Analysis) completed

**Fundamental Assessment**: STRONG
- Price: $420.45 (+0.8%), P/E 31x, Market Cap $3.1T
- 4 consecutive earnings beats, avg +4.2% surprise
- 89% buy ratings, mean target $475 (+13% upside)
- Revenue +15% YoY, 42% gross margin, $87B FCF
- Exceptional profitability (42% ROE)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEWS SENTRY: EVENT MONITORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

News Sentry (Event Monitor):
  → Calling route_to_news_sentry
     News Sentry analyzing: Material events for Microsoft...
     Running specialist tools (8-K monitoring, insider trades)...
      → get_latest_8k({'symbol': 'MSFT'})
      → get_insider_transactions({'symbol': 'MSFT'})
  ✓ News Sentry (Event Monitoring) completed

**Material Events**: NEUTRAL
- No significant 8-K filings in last 30 days
- Routine insider sales by executives (tax-related)
- No unusual insider buying activity

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MACRO LENS: TIMING VALIDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Macro Lens (Market Strategist):
  → Calling route_to_macro_lens
     Macro Lens analyzing: What is the current market environment...
     Running specialist tools (market timing, sector allocation, economic regime)...
      → get_key_macro_indicators()
      → get_treasury_yield_curve()
      → get_market_indices()
  ✓ Macro Lens (Market Timing) completed

**Macro Context**: LATE EXPANSION with CAUTION
- GDP +2.4%, CPI +3.1%, Unemployment 3.7%
- 10Y-2Y inverted -0.54% (recession warning)
- S&P 500 +12% YTD, Nasdaq -8% from highs, VIX 14.2
- Late expansion phase suggests staged entry

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RISK SHIELD: EXPOSURE ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Risk Shield (Portfolio Risk):
  → Calling route_to_risk_shield
     Risk Shield analyzing: What are the key risk considerations...
     Running specialist tools (portfolio risk, VAR, drawdown analysis)...
      → get_volatility_metrics({'symbol': 'MSFT'})
      → calculate_portfolio_beta({'symbol': 'MSFT'})
  ✓ Risk Shield (Portfolio Risk) completed

**Risk Profile**: MODERATE
- Beta: 0.95 (slightly less volatile than market)
- Defensive characteristics (enterprise subscriptions)
- Position sizing: Recommend 5-10% of portfolio max

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TAX SCOUT: TAX IMPLICATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tax Scout (Tax Optimization):
  → Calling route_to_tax_scout
     Tax Scout analyzing: Tax considerations for purchase...
  ✓ Tax Scout (Tax Optimization) completed

**Tax Considerations**: NO ISSUES
- No wash-sale concerns (new purchase)
- Consider tax-advantaged accounts for large positions
- Hold >1 year for long-term capital gains treatment

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL SYNTHESIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RECOMMENDATION: BUY (Dollar-Cost Average)
📊 Confidence Level: MEDIUM

**Key Reasoning**:

Microsoft shows exceptional fundamental quality:
- 42% ROE, $87B annual FCF (best-in-class capital efficiency)
- Strong competitive moats (Azure cloud, enterprise software lock-in)
- Consistent earnings beats (+4.2% avg surprise, 4 quarters)
- 89% analyst buy ratings, $475 mean target (+13% upside)

However, macro timing suggests staged entry:
- Late expansion phase (GDP slowing from 2.8% to 2.4%)
- Inverted yield curve (-0.54%) signals 70% recession probability
- Tech sector vulnerable (Nasdaq -8% from highs)

**Suggested Action**:

Dollar-cost average over 3-6 months:
- Tranche 1: 40% now (defensive exposure to quality)
- Tranche 2: 30% if MSFT dips below $390 (-7% from current)
- Tranche 3: 30% if macro deteriorates (recession confirmed)

Microsoft's defensive characteristics position it to outperform
cyclical tech peers in downturn.

**Risk Warnings**:
1. Azure growth deceleration below 25% YoY would weaken thesis
2. Recession could compress P/E to 24-26x (15-20% downside)
3. If yield curve steepens rapidly, pause accumulation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Report saved to: reports/MSFT_analysis_20251012_143022.md
```

</details>

### Systematic Idea Generation

**Command**: `/discover [CRITERIA]` **NEW in v0.1.37!**

**What Happens**:

1. **Screen Forge** identifies 10-15 candidates using factor-based screening
2. **Quill** performs deep fundamental analysis on top 3-5 picks
3. **Risk Shield** assesses portfolio fit and position sizing for each
4. **Synthesis** ranks candidates with actionable recommendations

<details>
<summary><b>Example: Discover Dividend Stocks (click to expand)</b></summary>

```
You: /discover dividend stocks with P/E under 20 and yield over 3%

Idea Discovery Workflow: Starting systematic screening...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCREEN FORGE: CANDIDATE IDENTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Screen Forge (Equity Screener):
  🔍 Screen Forge identifying candidates...
    → get_stock_screener
    → get_dividend_stocks
    → get_financial_ratios

**Screening Results**: 12 CANDIDATES IDENTIFIED

| Symbol | Price | P/E | Yield | Payout | Score |
|--------|-------|-----|-------|--------|-------|
| VZ     | $38.50 | 8.2x | 6.8% | 54% | 8.5 |
| MO     | $43.20 | 9.1x | 7.9% | 78% | 8.2 |
| T      | $16.80 | 7.5x | 6.2% | 55% | 8.0 |
| ABBV   | $172.50 | 15.3x | 3.8% | 45% | 7.8 |
| PFE    | $28.40 | 11.2x | 5.9% | 65% | 7.5 |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUILL: FUNDAMENTAL ANALYSIS (TOP 3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quill (Equity Research):
  📊 Quill analyzing top picks...
    → Analyzing VZ, MO, T

**Top Pick #1: Verizon (VZ)**
- **Valuation**: Attractive at 8.2x P/E (telecom avg: 12x)
- **Dividend Safety**: Strong (54% payout, $8B annual FCF)
- **Business Quality**: Infrastructure moat, recession-resistant
- **5-Year Returns**: Total return 45% (35% from dividends)
- **Rating**: BUY

**Top Pick #2: Altria (MO)**
- **Valuation**: Cheap at 9.1x P/E
- **Dividend Safety**: Moderate risk (78% payout)
- **Business Quality**: Declining smoker base, regulatory risk
- **5-Year Returns**: Total return 38% (mostly dividends)
- **Rating**: HOLD (monitor payout sustainability)

**Top Pick #3: AT&T (T)**
- **Valuation**: Very cheap at 7.5x P/E
- **Dividend Safety**: Stable (55% payout, post-cut)
- **Business Quality**: Fiber buildout improving outlook
- **5-Year Returns**: Total return 28% (post-dividend cut recovery)
- **Rating**: HOLD (improving fundamentals)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RISK SHIELD: PORTFOLIO FIT ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Risk Shield (Risk Manager):
  🛡️ Risk Shield assessing portfolio fit...
    → calculate_correlation
    → assess_sector_concentration

**Position Sizing Recommendations**:
- **VZ**: 5-7% allocation (defensive core holding)
- **MO**: 2-3% allocation (higher risk, satellite position)
- **T**: 3-5% allocation (value/turnaround play)

**Concentration Risk**: MODERATE
- 10-15% combined telecom exposure acceptable
- Provides defensive characteristics, recession hedge
- Low correlation with tech-heavy portfolios

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **RANKED INVESTMENT IDEAS**

**#1 BEST: Verizon (VZ) - BUY**
- Entry: $38-40 range
- Target yield: 6.5-7.0%
- Position size: 5-7% of portfolio
- Thesis: Infrastructure moat + recession-resistant + attractive valuation

**#2 HOLD: Altria (MO) - Monitor**
- Entry: Below $42 (current $43.20)
- Target yield: 8%+
- Position size: 2-3% maximum (satellite)
- Thesis: High yield but declining business, payout risk

**#3 HOLD: AT&T (T) - Turnaround Play**
- Entry: $15-17 range
- Target yield: 6-7%
- Position size: 3-5%
- Thesis: Post-cut stabilization, fiber buildout upside

**Action Steps**:
1. Start with VZ (5% allocation) for defensive income core
2. Watch for MO dip below $42 for small satellite position
3. Monitor AT&T fiber subscriber growth for entry signal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Report saved to: reports/report_idea_discovery_20251012_145200.md
```

</details>

---

## 📚 Documentation

### User Guides

- 🚀 **[Getting Started](docs/user-guide/getting-started.md)** - Installation, setup, first queries, troubleshooting
- ❓ **[FAQ](docs/faq.md)** - 100+ answered questions covering all features
- 🤖 **[Agents Guide](docs/user-guide/agents.md)** - Complete reference for all 10 specialized agents
- 🔀 **[Multi-Agent Workflows](docs/user-guide/multi-agent-workflows.md)** - Agent collaboration patterns
- 🛠️ **[API Tools](docs/user-guide/api-tools.md)** - Data sources and tool capabilities

### Developer Resources

- 📦 **[PyPI Package](https://pypi.org/project/navam-invest/)** - Latest releases and version history
- 🔧 **[GitHub Repository](https://github.com/navam-io/navam-invest)** - Source code, issues, pull requests
- 🏗️ **[Architecture](docs/architecture/about.md)** - System design and technical overview
- 📝 **[Release Notes](backlog/)** - Detailed changelog for each version
- 📖 **[LangGraph Guide](refer/langgraph/)** - Multi-agent patterns & best practices

### API Documentation

- **[Anthropic Claude](https://docs.anthropic.com/)** - AI reasoning engine
- **[LangGraph](https://langchain-ai.github.io/langgraph/)** - Agent orchestration framework
- **[Yahoo Finance (yfinance)](https://github.com/ranaroussi/yfinance)** - Free market data library
- **[SEC EDGAR](https://www.sec.gov/edgar/sec-api-documentation)** - Corporate filings API
- **[Alpha Vantage](https://www.alphavantage.co/documentation/)** - Stock market data
- **[Tiingo](https://www.tiingo.com/documentation/)** - Historical fundamentals
- **[Finnhub](https://finnhub.io/docs/api)** - Alternative data & sentiment
- **[FRED](https://fred.stlouisfed.org/docs/api/fred/)** - Economic indicators

---

## 🗺️ Roadmap

### Current Release: v0.1.37 (In Development)

**Latest Features**:
- ✅ **Extended `/analyze` Workflow**: 5-agent comprehensive analysis (Quill + News Sentry + Macro Lens + Risk Shield + Tax Scout)
- ✅ **`/discover` Workflow**: NEW systematic idea generation (Screen Forge + Quill + Risk Shield)
- ✅ **Progressive Streaming**: Real-time display of sub-agent tool calls as they execute
- ✅ **State Accumulation**: Each agent receives context from previous agents
- ✅ **Workflow Synthesis**: Comprehensive recommendations integrating all perspectives

**Recently Completed** (v0.1.36):
- ✅ **Automatic Intent-Based Routing**: No more manual agent switching—just ask naturally
- ✅ **Router Agent**: LangGraph tool-calling supervisor coordinating 10 specialist agents
- ✅ **Enhanced Transparency**: Watch router analyze intent and select appropriate agents
- ✅ **Backward Compatible**: All `/command` syntax still works for power users

**Earlier Releases**:
- ✅ **Hedge Smith Agent**: Options strategies (collars, covered calls, puts), Greeks analysis (v0.1.35)
- ✅ **Tax Scout Agent**: Tax-loss harvesting, wash-sale compliance, year-end planning (v0.1.34)
- ✅ **Risk Shield Agent**: Portfolio risk management, VAR, drawdown analysis (v0.1.33)
- ✅ **News Sentry Agent**: Real-time 8-K monitoring, insider tracking, breaking news (v0.1.32)

**Planned for v0.1.38** (Q1 2025):
- [ ] **New Workflows**: `/optimize-tax` (Tax Scout + Hedge Smith), `/protect` (Risk Shield + Hedge Smith)
- [ ] **API Caching Layer**: DuckDB-based caching to reduce API calls and improve performance
- [ ] **Workflow Progress Visualization**: Enhanced TUI display for multi-agent workflows

### Future Releases

**v0.2.0+** (Q2 2025):
- [ ] **Backtesting Engine**: Test investment strategies on historical data
- [ ] **Web UI**: Browser-based interface (in addition to TUI)
- [ ] **State Persistence**: PostgreSQL checkpointer for LangGraph
- [ ] **Cloud Deployment**: LangGraph Cloud integration
- [ ] **Custom Agents**: User-defined agent templates and tools
- [ ] **Python SDK**: Programmatic API for third-party integrations

### Recent Releases

<details>
<summary><b>v0.1.36 (Oct 15, 2025) - Router Agent & Progressive Streaming</b></summary>

- ✅ Automatic intent-based routing eliminates manual agent switching
- ✅ Router supervisor agent coordinates 10 specialist agents
- ✅ Progressive streaming shows real-time sub-agent tool calls
- ✅ AsyncIO queue-based streaming architecture
- ✅ Enhanced transparency with router reasoning display
- ✅ Backward compatible with manual `/command` syntax
- ✅ 16 comprehensive tests (all passing)

[Full Release Notes](backlog/release-0.1.36.md)

</details>

<details>
<summary><b>v0.1.35 (Oct 13, 2025) - Hedge Smith Agent</b></summary>

- ✅ Options strategies for portfolio protection and yield enhancement
- ✅ Protective collars, covered calls, protective puts, cash-secured puts
- ✅ Greeks analysis (delta, gamma, theta, vega, IV)
- ✅ Strike selection and expiration optimization
- ✅ 13 specialized tools for options analysis
- ✅ TUI integration with `/hedge` command

[Full Release Notes](backlog/release-0.1.35.md)

</details>

<details>
<summary><b>v0.1.34 (Oct 12, 2025) - Tax Scout Agent</b></summary>

- ✅ Tax-loss harvesting opportunity identification
- ✅ Wash-sale rule compliance monitoring (30-day windows)
- ✅ Year-end tax planning strategies
- ✅ 12 specialized tools for tax optimization
- ✅ TUI integration with `/tax` command

[Full Release Notes](backlog/release-0.1.34.md)

</details>

<details>
<summary><b>v0.1.33 (Oct 9, 2025) - Risk Shield Agent</b></summary>

- ✅ Portfolio risk management (VAR, drawdown, concentration)
- ✅ 18 specialized tools across market data and macro indicators
- ✅ Comprehensive system prompt with risk assessment frameworks
- ✅ TUI integration with `/risk` command

[Full Release Notes](backlog/release-0.1.33.md)

</details>

---

## 🤝 Contributing

We welcome contributions! Navam Invest is built by retail investors, for retail investors.

### Ways to Contribute

- 🐛 **[Report Bugs](https://github.com/navam-io/navam-invest/issues)** - Submit detailed bug reports
- 💡 **[Suggest Features](https://github.com/navam-io/navam-invest/issues)** - Share ideas for new agents or workflows
- 📝 **[Improve Docs](https://github.com/navam-io/navam-invest/pulls)** - Make documentation clearer
- 🔧 **[Submit PRs](https://github.com/navam-io/navam-invest/pulls)** - Code contributions for bugs or features

### Development Workflow

1. **Fork and clone**: `git clone https://github.com/your-username/navam-invest.git`
2. **Create branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** with tests and documentation
4. **Run quality checks**:
   ```bash
   black src/ tests/        # Format code
   ruff check src/ tests/   # Lint
   mypy src/                # Type check
   pytest                   # Run tests
   ```
5. **Commit**: `git commit -m "feat: Add amazing feature"`
6. **Push and create PR** with detailed description

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

**Key Points**:
- ✅ Free for personal and commercial use
- ✅ Modify and distribute as you wish
- ✅ No warranty provided

---

## 🙏 Acknowledgments

### Core Technologies

- **[Anthropic](https://www.anthropic.com/)** - Claude AI reasoning engine (Sonnet 4.5)
- **[LangChain](https://www.langchain.com/)** - Agent framework ecosystem (LangGraph orchestration)
- **[Textual](https://textual.textualize.io/)** - Modern terminal UI framework

### Data Providers

- **[Yahoo Finance](https://finance.yahoo.com/)** - Free real-time quotes, earnings, analyst ratings
- **[SEC EDGAR](https://www.sec.gov/edgar)** - Corporate filings (10-K, 10-Q, 8-K, Form 4)
- **[U.S. Treasury](https://home.treasury.gov/)** - Yield curves, treasury rates
- **[Alpha Vantage](https://www.alphavantage.co/)** - Stock market data
- **[Tiingo](https://www.tiingo.com/)** - Historical fundamentals
- **[Finnhub](https://finnhub.io/)** - Alternative data & sentiment
- **[FRED](https://fred.stlouisfed.org/)** - Federal Reserve economic data
- **[NewsAPI.org](https://newsapi.org/)** - Market news & headlines

---

<div align="center">

**Built with ❤️ for retail investors**

[![Star on GitHub](https://img.shields.io/github/stars/navam-io/navam-invest?style=social)](https://github.com/navam-io/navam-invest)
[![Follow on Twitter](https://img.shields.io/twitter/follow/navam_io?style=social)](https://twitter.com/navam_io)

[⬆ Back to Top](#-navam-invest)

</div>
