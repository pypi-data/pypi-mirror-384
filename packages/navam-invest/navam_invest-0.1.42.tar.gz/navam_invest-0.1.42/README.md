<div align="center">

# 🧠 Navam Invest

**AI-Powered Investment Intelligence for Retail Investors**

[![PyPI version](https://badge.fury.io/py/navam-invest.svg)](https://badge.fury.io/py/navam-invest)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/navam-invest)](https://pepy.tech/project/navam-invest)

**Replace $1,000-$10,000/year wealth management fees with institutional-grade AI**

Built on [LangGraph](https://langchain-ai.github.io/langgraph/) • Powered by [Anthropic Claude](https://www.anthropic.com/claude)

[Quick Start](#-quick-start) •
[Features](#-what-you-get) •
[AI Agents](#-10-specialized-ai-agents) •
[Workflows](#-example-workflows) •
[Documentation](#-documentation)

</div>

---

## 🎯 What is Navam Invest?

An **open-source AI investment advisory platform** for retail investors managing $50K-$1M portfolios. Get **10 specialized AI agents** with **automatic intent-based routing**—all running locally with your API keys, using free public data.

**Just ask naturally. No commands to memorize.**

```bash
# Install and run
pip install navam-invest
navam invest

# Ask anything - AI routes to the right expert agents automatically
> Should I invest in Apple stock right now?
> Find undervalued tech stocks with strong earnings momentum
> How can I reduce my tax bill before year-end?
> Protect my NVDA position with options strategies
```

---

## 💡 What You Get

<table>
<tr>
<td width="50%">

### 🏦 Institutional Intelligence
**10 specialized AI agents** working together:
- **Equity Research** - Deep fundamental analysis
- **Earnings Analysis** - Post-earnings drift detection
- **Stock Screening** - Systematic idea generation
- **Macro Strategy** - Top-down economic context
- **Risk Management** - Portfolio exposure analysis
- **Tax Optimization** - Tax-loss harvesting
- **Options Strategies** - Portfolio hedging
- **Event Monitoring** - Real-time alerts
- **Asset Allocation** - Strategic planning

**+ Automatic routing** - Just ask naturally, no commands needed

</td>
<td width="50%">

### 💰 Zero Lock-In, Maximum Value
**Free to run** with public data:
- ✅ Yahoo Finance (unlimited, no key)
- ✅ SEC EDGAR (unlimited, no key)
- ✅ U.S. Treasury (unlimited, no key)
- ✅ 6 optional APIs (generous free tiers)

**Your data stays yours**:
- Runs 100% locally on your machine
- No subscription fees, no recurring costs
- Open source MIT license

</td>
</tr>
<tr>
<td width="50%">

### 🔍 Transparent & Explainable
**Watch AI agents think in real-time**:
- Progressive streaming of reasoning
- Full audit trails of data sources
- Educational explanations, not black boxes
- Tool execution tracking

**Production-ready features**:
- ESC to cancel long operations
- Auto-save all reports
- Smart API caching (instant responses)
- Non-blocking terminal UI

</td>
<td width="50%">

### ⚡ Rich Data Access
**32 tools across 9 APIs**:
- Real-time quotes & earnings
- SEC filings (10-K, 10-Q, 8-K)
- Insider transactions (Form 4)
- Economic indicators (GDP, CPI)
- Yield curves & interest rates
- News & sentiment analysis
- Options chains & Greeks
- Analyst ratings & estimates

**80% of features work with zero API keys!**

</td>
</tr>
</table>

---

## 🆚 Why Navam Invest?

<table>
<tr>
<th width="25%">Solution</th>
<th width="25%">Cost</th>
<th width="25%">Intelligence</th>
<th width="25%">Transparency</th>
</tr>
<tr>
<td><b>Wealth Manager</b></td>
<td>$1K-$10K/year<br>(1% AUM)</td>
<td>✅ Expert analysis</td>
<td>❌ Black box decisions</td>
</tr>
<tr>
<td><b>Robo-Advisor</b></td>
<td>$250-$1K/year<br>(0.25% AUM)</td>
<td>⚠️ Basic rebalancing</td>
<td>⚠️ Limited transparency</td>
</tr>
<tr>
<td><b>DIY Research</b></td>
<td>Free</td>
<td>⚠️ Time-consuming</td>
<td>✅ Full control</td>
</tr>
<tr>
<td><b>Navam Invest</b></td>
<td><b>$3-15/month</b><br>(AI API costs)</td>
<td><b>✅ 10 AI experts</b></td>
<td><b>✅ Full audit trails</b></td>
</tr>
</table>

---

## 🚀 Quick Start

### Installation (2 minutes)

**Requirements**: Python 3.9+ and an Anthropic API key

```bash
# Install from PyPI
pip install navam-invest

# Start the interactive terminal
navam invest
```

### Setup (3 minutes)

**1. Get your Anthropic API key** (required):

Visit [console.anthropic.com](https://console.anthropic.com/) and create a free account.
💰 **Cost**: ~$3-15/month for typical usage (pay-as-you-go, no subscription)

**2. Create environment file**:

```bash
# Copy example file
cp .env.example .env

# Add your key
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
```

**3. Optional: Add free-tier API keys** (recommended):

```bash
# All have generous free tiers - get keys at their websites
FRED_API_KEY=your_key_here          # Unlimited economic data
TIINGO_API_KEY=your_key_here        # 50 symbols/hr historical data
FINNHUB_API_KEY=your_key_here       # 60 calls/min sentiment
NEWSAPI_API_KEY=your_key_here       # 1,000 calls/day news
ALPHA_VANTAGE_API_KEY=your_key_here # 25-500 calls/day quotes
```

**4. Verify setup**:

```bash
navam invest
> /api
# Shows: ✅ working / ⚪ not configured / ❌ failed
```

### First Query (1 minute)

```bash
navam invest

# Optional: Pre-warm cache for faster queries
> /cache warm
# Loads 23 common queries (FAANG+ stocks, indices, GDP/CPI)
# Takes 60 seconds, but future queries are instant!

# Just ask naturally - automatic routing!
> Should I invest in Apple stock right now?
# → Router selects Quill (fundamentals), Macro Lens (timing), Risk Shield (exposure)
# → Comprehensive BUY/HOLD/SELL recommendation in 30 seconds

> Find undervalued tech stocks with strong earnings momentum
# → Router selects Screen Forge (screening) + Earnings Whisperer (earnings)
# → Ranked list of 10-15 candidates with analysis

# Or use workflows for systematic analysis
> /analyze MSFT
# 5-agent comprehensive investment analysis

> /optimize-tax I hold GOOGL at $150, now $120
# Tax-loss harvesting with replacement strategies

> /protect I hold 1000 NVDA shares, worried about correction
# Portfolio hedging with protective options

# Cache management (NEW in v0.1.41)
> /cache
# View hit rates, cached tools, API savings

> /cache clear
# Invalidate all cached entries
```

**🎓 New to Navam Invest?** See the [Getting Started Guide](docs/user-guide/getting-started.md) for detailed walkthroughs.

---

## ✨ Key Features

### 🔀 Automatic Intent-Based Routing (v0.1.36+)

**No more manual agent switching!** Just ask your question naturally:

```bash
# Simply ask - the router automatically selects the right agent(s)
> Should I invest in AAPL?
# → Routes to Quill (fundamentals) + Macro Lens (timing) + Risk Shield (exposure)

> Find undervalued tech stocks with strong earnings momentum
# → Routes to Screen Forge + Earnings Whisperer

> Protect my NVDA position with options
# → Routes to Hedge Smith for options strategies
```

**Power users** can still use manual commands (`/quill`, `/hedge`, `/risk`) for direct agent control.

### ⚡ Smart API Caching (v0.1.41+)

**DuckDB-powered caching** that dramatically reduces API calls:

- ✅ **42 cached tools** across 9 data sources
- ✅ **Intelligent TTL**: Real-time (60s), fundamentals (1h), economic data (24h)
- ✅ **Cache warming**: Pre-populate with `/cache warm` (23 common queries)
- ✅ **Performance stats**: `/cache` shows hit rates and API savings
- ✅ **Zero config**: Works out-of-the-box

**Expected Performance**:
- 20-40% hit rates on economic indicators
- 40-70% hit rates on treasury data
- 10-30% hit rates on equity data
- Higher over time as you query the same stocks repeatedly

### 💬 Modern Terminal UI

**Built with Textual framework** for responsive CLI:

- ✅ **Progressive streaming**: Watch tool calls appear in real-time
- ✅ **ESC cancellation**: Cancel long operations anytime (v0.1.38+)
- ✅ **Non-blocking**: Scroll and interact while agents work
- ✅ **Markdown rendering**: Tables, code blocks, syntax highlighting
- ✅ **Auto-save reports**: All responses >200 chars saved to `reports/`
- ✅ **Keyboard shortcuts**: `ESC` (cancel), `Ctrl+C` (clear), `Ctrl+Q` (quit)

---

## 🤖 10 Specialized AI Agents

Each agent is purpose-built with curated tools and expert system prompts:

| Agent | Purpose | Tools | Example Query |
|-------|---------|-------|---------------|
| **Quill** | Deep fundamental research | 36 | "Analyze AAPL with DCF valuation and insider activity" |
| **Earnings Whisperer** | Earnings surprise analysis | 14 | "Find post-earnings drift opportunities in NVDA" |
| **Screen Forge** | Systematic stock screening | 15 | "Screen for stocks with 3+ consecutive earnings beats" |
| **Macro Lens** | Top-down macro analysis | 13 | "What's the current economic regime for tech stocks?" |
| **News Sentry** | Real-time event detection | 13 | "Alert me to material 8-K filings and insider trades" |
| **Risk Shield** | Portfolio risk management | 18 | "Calculate VAR and analyze concentration risks" |
| **Tax Scout** | Tax-loss harvesting | 12 | "Identify tax-loss harvesting opportunities" |
| **Hedge Smith** | Options strategies | 13 | "Design a protective collar for my AAPL position" |
| **Atlas** | Strategic asset allocation | 12 | "Create an IPS for $200K portfolio" |
| **Portfolio/Research** | Legacy general-purpose | 24/10 | Backward compatibility |

<details>
<summary><b>📖 View detailed agent capabilities</b></summary>

### ⭐ Quill - Equity Research Analyst

**Deep fundamental analysis & investment thesis development**

**What Quill Does**:
- 📊 **DCF Valuation**: Discounted cash flow models with sensitivity analysis
- 📈 **5-Year Trends**: Revenue growth, margins, ROIC, FCF, debt ratios
- 💰 **Earnings Analysis**: Historical beats, estimates, surprise patterns
- 🎯 **Analyst Coverage**: Consensus ratings, price targets, upgrades/downgrades
- 🏢 **Ownership Tracking**: Institutional holders, insider transactions (Form 4)
- 📋 **SEC Filings**: 10-K/10-Q deep-dives, 8-K material events, XBRL data
- 💵 **Dividend Analysis**: Yield, payout sustainability, history
- 📰 **News Validation**: Company-specific news with sentiment

**Example Output**: 5-section investment thesis with BUY/HOLD/SELL recommendation, fair value range, key catalysts, and risk factors.

### 📊 Earnings Whisperer - Earnings Specialist

**Earnings surprise analysis & post-earnings drift detection**

**What Earnings Whisperer Does**:
- 🎯 **Historical Tracking**: 4-8 quarter earnings surprise analysis
- 📈 **Drift Detection**: 1-3 day post-earnings momentum patterns
- 🔄 **Analyst Revisions**: Estimate changes post-earnings
- ✅ **Quality Assessment**: Revenue vs EPS beats, non-recurring items
- 📅 **Calendar Monitoring**: Upcoming earnings with probability scoring
- 🏆 **Pattern Recognition**: Consistent beaters, accelerating growth
- 💹 **Trading Signals**: BUY/HOLD/SELL based on drift probability

**Example Output**: Earnings momentum scorecard with drift probability, pattern analysis, and trading recommendation.

### 🔍 Screen Forge - Equity Screener

**Systematic stock discovery & idea generation**

**What Screen Forge Does**:
- 📐 **Multi-Factor Screening**: Value, growth, quality, momentum factors
- 🎯 **Systematic Discovery**: Weekly watchlist generation with ranking
- 📈 **Earnings Momentum**: Filter for consistent earnings beaters
- ⬆️ **Analyst Activity**: Upgrade/downgrade-based screening
- 💬 **Sentiment Validation**: News and social sentiment checks
- 🔗 **Seamless Handoff**: Passes top candidates to Quill for deep-dive

**Example Output**: Ranked table of 10-20 candidates with screening criteria, key metrics, and suggested next steps.

### 🌍 Macro Lens - Market Strategist

**Top-down economic analysis & regime identification**

**What Macro Lens Does**:
- 🔄 **Economic Cycles**: 4-phase regime analysis (early/mid/late expansion, recession)
- 📈 **Yield Curve**: Interpretation and recession signal detection
- 🏭 **Sector Allocation**: Macro-driven positioning guidance
- 📊 **Factor Recommendations**: Value vs growth, size, volatility tilts
- 📉 **Macro Tracking**: Inflation, GDP, employment, Fed policy
- 💹 **Interest Rates**: Fed funds, treasury rates, credit spreads

**Example Output**: Regime assessment with sector allocation matrix, factor positioning, and macro risk scenarios.

### 🗞️ News Sentry - Real-Time Event Monitor

**Material event detection & breaking news alerts**

**What News Sentry Does**:
- 📋 **8-K Monitoring**: Material corporate events (M&A, management changes)
- 📝 **Form 4 Tracking**: Insider buying/selling by officers
- 📰 **Breaking News**: Real-time company-specific news with sentiment
- 📊 **Analyst Actions**: Rating changes, price target updates
- 🎯 **Event Prioritization**: CRITICAL/HIGH/MEDIUM/LOW urgency scoring
- ⚡ **Rapid Response**: Detect market-moving events as they happen

**Example Output**: Prioritized event list with urgency levels, event details, and recommended actions.

### 🛡️ Risk Shield - Portfolio Risk Manager

**Comprehensive risk analysis & exposure monitoring**

**What Risk Shield Does**:
- 📊 **Concentration Analysis**: Sector, geographic, single-stock exposures
- 📉 **Drawdown Metrics**: Historical drawdowns, peak-to-trough, recovery
- 💹 **VAR Calculations**: Value at Risk (95%, 99% confidence levels)
- 🎲 **Scenario Testing**: Stress tests against historical crises (2008, 2020)
- 🔗 **Correlation Analysis**: Diversification quality, correlation matrices
- 📈 **Volatility Metrics**: Portfolio vol, beta, Sharpe, Sortino ratios
- ⚠️ **Limit Breach Detection**: Position size, sector concentration thresholds
- 🛠️ **Risk Mitigation**: Hedging strategies, rebalancing recommendations

**Example Output**: Risk scorecard (1-10 scale), concentration analysis, VAR metrics, stress test results, and mitigation recommendations.

### 💰 Tax Scout - Tax Optimization Specialist

**Tax-loss harvesting & wash-sale compliance**

**What Tax Scout Does**:
- 💸 **Tax-Loss Harvesting**: Identify positions with unrealized losses
- ⏰ **Wash-Sale Compliance**: 30-day rule monitoring (IRS Section 1091)
- 🔄 **Replacement Candidates**: Find substantially different securities
- 📊 **Capital Gains Analysis**: Short-term vs long-term tracking
- 📅 **Year-End Planning**: Strategic positioning before Dec 31
- ⚖️ **Tax-Efficient Rebalancing**: Minimize gains during portfolio adjustments
- 📋 **Lot-Level Analysis**: FIFO, LIFO, specific lot identification

**Example Output**: TLH opportunities table with tax savings estimates, wash-sale violations, replacement candidates, and year-end action plan.

### 🎯 Hedge Smith - Options Strategist

**Options strategies for portfolio protection & yield enhancement**

**What Hedge Smith Does**:
- 🛡️ **Protective Collars**: Simultaneous put purchase + call sale for downside protection
- 💰 **Covered Calls**: Sell calls against holdings for premium income
- 📉 **Protective Puts**: Portfolio insurance with cost/benefit optimization
- 💵 **Cash-Secured Puts**: Generate income while waiting to acquire stock
- 🎯 **Strike Selection**: Optimal strike selection (5-10% OTM protection, 10-20% income)
- 📅 **Expiration Optimization**: 30-45 days for theta decay, 60-90 days for protection
- 📊 **Options Greeks**: Delta, gamma, theta, vega, IV percentile analysis
- ⚖️ **Risk/Reward Profiling**: Max profit, max loss, breakeven, probability estimates

**Example Output**: Complete strategy specification with specific strikes, premiums, Greeks, risk/reward analysis, and exit strategy.

</details>

---

## 🔀 Multi-Agent Workflows

**Agents collaborate in sophisticated workflows for institutional-quality analysis:**

### `/analyze` - Comprehensive Investment Analysis (5 Agents)

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

### `/discover` - Systematic Idea Generation (3 Agents)

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

### `/optimize-tax` - Tax-Loss Harvesting (2 Agents)

```bash
/optimize-tax I hold GOOGL at $150, now $120 and ETHUSD at $2500, now $1800

# 1. Tax Scout identifies tax-loss harvesting opportunities
#    → Unrealized losses >5%, wash-sale compliance, tax savings
# 2. Hedge Smith designs replacement strategies
#    → Sector ETF substitutes, synthetic long options
# 3. Final synthesis provides actionable tax plan
#    → Immediate actions, year-end optimization, compliance checklist
```

### `/protect` - Portfolio Hedging (2 Agents)

```bash
/protect I hold 1000 NVDA shares at $120 average cost, currently $500

# 1. Risk Shield analyzes portfolio exposures
#    → Concentration risk, drawdown analysis, VAR, correlation
# 2. Hedge Smith designs protective strategies
#    → Protective puts, collars, index hedges, tail risk protection
# 3. Final synthesis provides hedging plan
#    → Strategy selection, cost-benefit analysis, implementation steps
```

---

## 💡 Example Workflows

<details>
<summary><b>📊 Comprehensive MSFT Analysis (click to expand)</b></summary>

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

<details>
<summary><b>💰 Tax Optimization for GOOGL + ETHUSD (click to expand)</b></summary>

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

Option 2: Synthetic Long (Options)
- Buy 1 call @ $120 strike, 60-day expiration
- Sell 1 put @ $120 strike, 60-day expiration
- Net cost: ~$2.50 per share ($250 per contract)
- Delta: ~1.0 (matches stock exposure)

**REPLACEMENT STRATEGY: ETHUSD**

Option 1: Execute sell + immediate rebuy (RECOMMENDED)
- Crypto exempt from wash-sale rules (IRS Notice 2014-21)
- Harvest loss: -$700 tax deduction
- Rebuy immediately: Maintain same exposure with zero gap

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
- Net tax benefit: $6,259

**COMPLIANCE CHECKLIST**:
- [ ] Confirm no GOOGL purchases in last 30 days
- [ ] Select replacement security (XLK or 31-day cash hold)
- [ ] Document cost basis and trade dates for tax reporting
- [ ] Set 31-day calendar reminder

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Report saved to: reports/report_tax_optimization_20251014_123710.md
```

</details>

---

## 📊 Data Sources

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

---

## 🗺️ Roadmap

### Current Release: v0.1.42 (October 2025)

**Latest in v0.1.41**:
- ✅ **API Caching Layer**: DuckDB-based caching with 42 cached tools
- ✅ **Cache Warming**: `/cache warm` (23 common queries)
- ✅ **Performance Boost**: Up to 75% hit rates on repeated queries

**v0.1.40**:
- ✅ **`/protect` Workflow**: Portfolio hedging (Risk Shield + Hedge Smith)

**v0.1.39**:
- ✅ **`/optimize-tax` Workflow**: Tax-loss harvesting with replacement strategies

**v0.1.38**:
- ✅ **ESC Cancellation**: Cancel long operations anytime
- ✅ **Non-blocking TUI**: Scroll while agents work

**v0.1.37**:
- ✅ **Extended `/analyze`**: 5-agent comprehensive analysis
- ✅ **`/discover` Workflow**: Systematic idea generation

**v0.1.36**:
- ✅ **Automatic Intent Routing**: No more manual agent switching

### Planned Features

**v0.1.43+** (Q4 2025):
- [ ] **Workflow Progress Visualization**: Enhanced TUI with status indicators
- [ ] **Async Tool Execution**: Parallel tool calls for faster responses
- [ ] **Cache Analytics**: Hit rate optimization and size management

**v0.2.0+** (Q1 2026):
- [ ] **Backtesting Engine**: Test strategies on historical data
- [ ] **Web UI**: Browser-based interface (in addition to TUI)
- [ ] **State Persistence**: PostgreSQL checkpointer for cross-session memory
- [ ] **Cloud Deployment**: LangGraph Cloud integration
- [ ] **Custom Agents**: User-defined agent templates
- [ ] **Python SDK**: Programmatic API for integrations

---

## 📚 Documentation

### User Guides
- 🚀 [Getting Started](docs/user-guide/getting-started.md) - Installation, setup, first queries
- ❓ [FAQ](docs/faq.md) - 100+ answered questions
- 🤖 [Agents Guide](docs/user-guide/agents.md) - Complete agent reference
- 🔀 [Multi-Agent Workflows](docs/user-guide/multi-agent-workflows.md) - Collaboration patterns
- 🛠️ [API Tools](docs/user-guide/api-tools.md) - Data sources and capabilities

### Developer Resources
- 📦 [PyPI Package](https://pypi.org/project/navam-invest/) - Releases and changelog
- 🔧 [GitHub Repository](https://github.com/navam-io/navam-invest) - Source code, issues
- 🏗️ [Architecture](docs/architecture/about.md) - System design overview
- 📖 [LangGraph Guide](refer/langgraph/) - Multi-agent patterns

---

## 🤝 Contributing

We welcome contributions! Built by retail investors, for retail investors.

### Ways to Contribute
- 🐛 [Report Bugs](https://github.com/navam-io/navam-invest/issues)
- 💡 [Suggest Features](https://github.com/navam-io/navam-invest/issues)
- 📝 [Improve Docs](https://github.com/navam-io/navam-invest/pulls)
- 🔧 [Submit PRs](https://github.com/navam-io/navam-invest/pulls)

### Development Workflow

```bash
# Fork and clone
git clone https://github.com/your-username/navam-invest.git
cd navam-invest

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Make changes and run quality checks
black src/ tests/        # Format
ruff check src/ tests/   # Lint
mypy src/                # Type check
pytest                   # Test

# Commit and push
git checkout -b feature/amazing-feature
git commit -m "feat: Add amazing feature"
git push origin feature/amazing-feature
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

**MIT License** - Free for personal and commercial use. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

### Core Technologies
- **[Anthropic](https://www.anthropic.com/)** - Claude AI (Sonnet 4.5)
- **[LangChain](https://www.langchain.com/)** - LangGraph agent framework
- **[Textual](https://textual.textualize.io/)** - Modern terminal UI

### Data Providers
- **[Yahoo Finance](https://finance.yahoo.com/)** - Real-time market data
- **[SEC EDGAR](https://www.sec.gov/edgar)** - Corporate filings
- **[U.S. Treasury](https://home.treasury.gov/)** - Yield curves, rates
- **[Alpha Vantage](https://www.alphavantage.co/)** - Stock data
- **[Tiingo](https://www.tiingo.com/)** - Historical fundamentals
- **[Finnhub](https://finnhub.io/)** - Alternative data
- **[FRED](https://fred.stlouisfed.org/)** - Economic indicators
- **[NewsAPI](https://newsapi.org/)** - Market news

---

<div align="center">

**Built with ❤️ for retail investors**

[![Star on GitHub](https://img.shields.io/github/stars/navam-io/navam-invest?style=social)](https://github.com/navam-io/navam-invest)
[![Follow on Twitter](https://img.shields.io/twitter/follow/navam_io?style=social)](https://twitter.com/navam_io)

[⬆ Back to Top](#-navam-invest)

</div>
