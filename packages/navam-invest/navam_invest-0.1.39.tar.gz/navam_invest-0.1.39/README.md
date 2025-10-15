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
- Auto-save reports, multi-agent orchestration, ESC cancellation

</td>
</tr>
</table>

---

## ✨ Key Features

### 🔀 Automatic Intent-Based Routing (v0.1.36+)

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

### 🔀 Multi-Agent Workflows

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

#### `/discover` - Systematic Idea Generation (3 Agents)
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

#### `/optimize-tax` - Tax-Loss Harvesting (2 Agents) **NEW in v0.1.39!**
```bash
/optimize-tax I hold GOOGL at $150, now $120 and ETHUSD at $2500, now $1800

# 1. Tax Scout identifies tax-loss harvesting opportunities
#    → Unrealized losses >5%, wash-sale compliance, tax savings
# 2. Hedge Smith designs replacement strategies
#    → Sector ETF substitutes, synthetic long options, correlation analysis
# 3. Final synthesis provides actionable tax plan
#    → Immediate actions, year-end optimization, compliance checklist
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

- ✅ **Progressive streaming**: Watch sub-agent tool calls appear in real-time
- ✅ **Real-time reasoning**: See agents think and make decisions live
- ✅ **ESC cancellation**: Cancel long-running operations anytime (NEW in v0.1.38)
- ✅ **Non-blocking execution**: Scroll and interact while agents work
- ✅ **Smart input management**: Auto-disabled during processing (no duplicate queries)
- ✅ **Tool execution tracking**: See exactly which data sources agents are calling
- ✅ **Multi-agent progress**: Visual workflow transitions with status updates
- ✅ **Markdown rendering**: Tables, code blocks, syntax highlighting
- ✅ **Auto-save reports**: All responses >200 chars saved to `reports/` directory
- ✅ **Keyboard shortcuts**: `ESC` (cancel), `Ctrl+C` (clear), `Ctrl+Q` (quit)

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

> /optimize-tax I hold GOOGL at $150, now $120
# Tax-loss harvesting with replacement strategies (NEW!)

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

# NEW: Use /optimize-tax workflow for full analysis
> /optimize-tax I hold GOOGL at $150, now $120
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

# NEW: Use /optimize-tax workflow for tax-loss replacement strategies
> /optimize-tax I hold GOOGL at $150, now $120
# Hedge Smith suggests sector ETF or synthetic long options
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

[... similar sections for News Sentry, Macro Lens, Risk Shield, Tax Scout ...]

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Report saved to: reports/MSFT_analysis_20251012_143022.md
```

</details>

### Tax-Loss Harvesting Workflow (NEW!)

**Command**: `/optimize-tax [PORTFOLIO]`

**What Happens**:

1. **Tax Scout** identifies tax-loss harvesting opportunities with wash-sale compliance
2. **Hedge Smith** designs replacement strategies to maintain exposure
3. **Synthesis** provides actionable tax optimization plan

<details>
<summary><b>Example: Tax Optimization for GOOGL + ETHUSD (click to expand)</b></summary>

```
You: /optimize-tax I hold GOOGL at $150, now $120 and ETHUSD at $2500, now $1800

Tax Optimization Workflow: Starting tax-loss harvesting analysis...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TAX SCOUT: TAX-LOSS IDENTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tax Scout (Tax Optimization):
  💰 Tax Scout identifying loss harvesting opportunities...
    → get_quote
    → check_wash_sale_window

**TAX-LOSS HARVESTING OPPORTUNITIES**:

1. GOOGL - Alphabet Inc.
   Current Price: $120.00 | Cost Basis: $150.00 | Unrealized Loss: -$30.00 (-20%)
   Holding Period: 180 days (Long-term capital loss)
   Wash-Sale Risk: None (no recent purchases)
   Tax Savings Estimate: $6,000 (assuming 20% LTCG bracket)
   Maintain Exposure? YES (core tech holding)

2. ETHUSD - Ethereum
   Current Price: $1,800 | Cost Basis: $2,500 | Unrealized Loss: -$700 (-28%)
   Holding Period: 45 days (Short-term capital loss)
   Wash-Sale Risk: None
   Tax Savings Estimate: $259 (assuming 37% ordinary income bracket)
   Maintain Exposure? YES (crypto allocation)

**RECOMMENDED ACTIONS**:
- Immediate harvest: GOOGL (significant long-term loss, no wash-sale risk)
- Immediate harvest: ETHUSD (crypto exempt from wash-sale = harvest with zero cost)

**POSITIONS REQUIRING REPLACEMENT STRATEGY**:
- GOOGL: Maintain tech exposure, need 31-day substitute
- ETHUSD: Can rebuy immediately (crypto exempt), but consider strategy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEDGE SMITH: REPLACEMENT STRATEGIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hedge Smith (Options Strategist):
  🛡️ Hedge Smith designing replacement strategies...
    → get_options_chain
    → get_sector_etf_alternatives

**REPLACEMENT STRATEGY: GOOGL**

Option 1: Sector ETF Substitute (RECOMMENDED)
- Ticker: XLK - Technology Select Sector SPDR ETF
- Correlation: 0.75 (wash-sale compliant)
- Investment: $120 × shares (match original position size)
- Hold for: 31+ days, then repurchase GOOGL if desired
- Tracking: Expected 75% correlation during hold period

Option 2: Synthetic Long (Options)
- Buy 1 call contract @ $120 strike, 60-day expiration
- Sell 1 put contract @ $120 strike, 60-day expiration
- Net cost: ~$2.50 per share ($250 per contract)
- Delta: ~1.0 (matches stock exposure)
- Expiration: Allows repurchase of stock after 31 days

**RECOMMENDATION**: Sector ETF substitute (XLK) for simplicity

**REPLACEMENT STRATEGY: ETHUSD**

Option 1: Execute sell + immediate rebuy (RECOMMENDED)
- Crypto exempt from wash-sale rules (IRS Notice 2014-21)
- Harvest loss: -$700 tax deduction
- Rebuy immediately: Maintain same exposure with zero gap
- Tax Benefit: Pure tax savings with no disruption

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL TAX OPTIMIZATION PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **IMMEDIATE ACTIONS** (Execute today):

1. Sell GOOGL @ market
   → Replace with XLK (Tech ETF) for 31+ days
   → Tax savings: $6,000 | Hold ETF 31+ days

2. Sell ETHUSD @ market
   → Rebuy immediately (crypto exempt from wash-sale)
   → Tax savings: $259 | Maintain same exposure

**TOTAL TAX IMPACT**:
- Total harvestable losses: -$6,259
- Estimated tax savings: $6,259
- Cost of replacement: $0 (ETF fees negligible, crypto rebuy instant)
- Net tax benefit: $6,259

**COMPLIANCE CHECKLIST**:
- [ ] Confirm no GOOGL purchases in last 30 days (review transaction history)
- [ ] Select replacement security (XLK or 31-day cash hold)
- [ ] Maintain similar portfolio allocation and risk profile
- [ ] Document cost basis and trade dates for tax reporting
- [ ] Set 31-day calendar reminder to avoid repurchase violations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Report saved to: reports/report_tax_optimization_20251014_123710.md
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

### Current Release: v0.1.38 (Oct 14, 2025)

**Latest Features**:
- ✅ **ESC Cancellation**: Cancel long-running agent operations anytime
- ✅ **Non-blocking TUI**: Scroll and interact while agents work
- ✅ **Worker-based Execution**: Textual worker pattern for responsive UI
- ✅ **Graceful Stream Cleanup**: Proper async stream handling on cancellation

**In Development** (v0.1.39):
- 🚧 **`/optimize-tax` Workflow**: Tax-loss harvesting with replacement strategies (Tax Scout + Hedge Smith)
- 🚧 **Worker-based Workflows**: Non-blocking execution for all multi-agent workflows

### Recent Releases

**v0.1.37** (Oct 12, 2025):
- ✅ **Extended `/analyze` Workflow**: 5-agent comprehensive analysis (Quill + News Sentry + Macro Lens + Risk Shield + Tax Scout)
- ✅ **`/discover` Workflow**: Systematic idea generation (Screen Forge + Quill + Risk Shield)
- ✅ **Progressive Streaming**: Real-time display of sub-agent tool calls
- ✅ **State Accumulation**: Each agent receives context from previous agents

**v0.1.36** (Oct 11, 2025):
- ✅ **Automatic Intent-Based Routing**: No more manual agent switching—just ask naturally
- ✅ **Router Agent**: LangGraph tool-calling supervisor coordinating 10 specialist agents
- ✅ **Enhanced Transparency**: Watch router analyze intent and select appropriate agents
- ✅ **Backward Compatible**: All `/command` syntax still works for power users

**v0.1.35** (Oct 10, 2025):
- ✅ **Hedge Smith Agent**: Options strategies (collars, covered calls, puts), Greeks analysis

**v0.1.34** (Oct 9, 2025):
- ✅ **Tax Scout Agent**: Tax-loss harvesting, wash-sale compliance, year-end planning

**v0.1.33** (Oct 8, 2025):
- ✅ **Risk Shield Agent**: Portfolio risk management, VAR, drawdown analysis

**v0.1.32** (Oct 7, 2025):
- ✅ **News Sentry Agent**: Real-time 8-K monitoring, insider tracking, breaking news

### Planned Features

**v0.1.39+** (Q4 2025):
- [ ] **`/protect` Workflow**: Portfolio hedging (Risk Shield + Hedge Smith)
- [ ] **API Caching Layer**: DuckDB-based caching to reduce API calls
- [ ] **Workflow Progress Visualization**: Enhanced TUI display for multi-agent workflows

**v0.2.0+** (Q1 2026):
- [ ] **Backtesting Engine**: Test investment strategies on historical data
- [ ] **Web UI**: Browser-based interface (in addition to TUI)
- [ ] **State Persistence**: PostgreSQL checkpointer for LangGraph
- [ ] **Cloud Deployment**: LangGraph Cloud integration
- [ ] **Custom Agents**: User-defined agent templates and tools
- [ ] **Python SDK**: Programmatic API for third-party integrations

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
