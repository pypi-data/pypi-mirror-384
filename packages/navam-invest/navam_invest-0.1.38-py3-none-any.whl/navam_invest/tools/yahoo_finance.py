"""Yahoo Finance API tools for real-time market data and fundamentals.

Uses yfinance library (unofficial Yahoo Finance API wrapper).
No API key required - free and unlimited access.
"""

from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    yf = None
    pd = None


def _check_yfinance_available() -> Optional[str]:
    """Check if yfinance is installed."""
    if yf is None:
        return (
            "yfinance package not installed. "
            "Install with: pip install yfinance"
        )
    return None


@tool
def get_quote(symbol: str) -> str:
    """Get real-time stock quote with extended metrics.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        Real-time quote with price, volume, market cap, and key metrics
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Extract key metrics
        price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
        change = info.get("regularMarketChange", "N/A")
        change_pct = info.get("regularMarketChangePercent", "N/A")
        volume = info.get("volume", "N/A")
        avg_volume = info.get("averageVolume", "N/A")
        market_cap = info.get("marketCap", "N/A")
        pe_ratio = info.get("trailingPE", "N/A")
        forward_pe = info.get("forwardPE", "N/A")
        div_yield = info.get("dividendYield", "N/A")

        # Format market cap
        if isinstance(market_cap, (int, float)):
            if market_cap >= 1e12:
                market_cap_str = f"${market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                market_cap_str = f"${market_cap/1e9:.2f}B"
            elif market_cap >= 1e6:
                market_cap_str = f"${market_cap/1e6:.2f}M"
            else:
                market_cap_str = f"${market_cap:,.0f}"
        else:
            market_cap_str = str(market_cap)

        # Format dividend yield
        if isinstance(div_yield, float):
            div_yield = f"{div_yield*100:.2f}%"

        return (
            f"**{symbol} - {info.get('longName', 'N/A')}**\n\n"
            f"**Price:** ${price}\n"
            f"**Change:** {change} ({change_pct}%)\n"
            f"**Volume:** {volume:,} (Avg: {avg_volume:,})\n"
            f"**Market Cap:** {market_cap_str}\n"
            f"**P/E (TTM):** {pe_ratio}\n"
            f"**Forward P/E:** {forward_pe}\n"
            f"**Dividend Yield:** {div_yield}\n"
        )
    except Exception as e:
        return f"Error fetching quote for {symbol}: {str(e)}"


@tool
def get_historical_data(
    symbol: str, period: str = "1y", interval: str = "1d"
) -> str:
    """Get historical price data (OHLCV).

    Args:
        symbol: Stock ticker symbol
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

    Returns:
        Summary statistics of historical price data
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            return f"No historical data found for {symbol}"

        # Calculate summary statistics
        latest_close = hist["Close"].iloc[-1]
        period_start = hist["Close"].iloc[0]
        period_return = ((latest_close - period_start) / period_start) * 100

        high = hist["High"].max()
        low = hist["Low"].min()
        avg_volume = hist["Volume"].mean()

        return (
            f"**{symbol} Historical Data ({period}, {interval} bars)**\n\n"
            f"**Period:** {hist.index[0].date()} to {hist.index[-1].date()}\n"
            f"**Data Points:** {len(hist)}\n"
            f"**Latest Close:** ${latest_close:.2f}\n"
            f"**Period Return:** {period_return:+.2f}%\n"
            f"**Period High:** ${high:.2f}\n"
            f"**Period Low:** ${low:.2f}\n"
            f"**Avg Volume:** {avg_volume:,.0f}\n"
        )
    except Exception as e:
        return f"Error fetching historical data for {symbol}: {str(e)}"


@tool
def get_financials(symbol: str) -> str:
    """Get financial statements (income statement, balance sheet, cash flow).

    Args:
        symbol: Stock ticker symbol

    Returns:
        Summary of latest financial statements
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)

        # Get financials
        income_stmt = ticker.financials
        balance_sheet = ticker.balance_sheet
        cash_flow = ticker.cashflow

        if income_stmt.empty:
            return f"No financial data found for {symbol}"

        # Latest period (most recent column)
        latest_date = income_stmt.columns[0]

        # Income statement metrics
        revenue = income_stmt.loc["Total Revenue", latest_date] if "Total Revenue" in income_stmt.index else "N/A"
        gross_profit = income_stmt.loc["Gross Profit", latest_date] if "Gross Profit" in income_stmt.index else "N/A"
        operating_income = income_stmt.loc["Operating Income", latest_date] if "Operating Income" in income_stmt.index else "N/A"
        net_income = income_stmt.loc["Net Income", latest_date] if "Net Income" in income_stmt.index else "N/A"

        # Balance sheet metrics
        total_assets = balance_sheet.loc["Total Assets", latest_date] if "Total Assets" in balance_sheet.index else "N/A"
        total_debt = balance_sheet.loc["Total Debt", latest_date] if "Total Debt" in balance_sheet.index else "N/A"
        cash = balance_sheet.loc["Cash And Cash Equivalents", latest_date] if "Cash And Cash Equivalents" in balance_sheet.index else "N/A"

        # Cash flow metrics
        operating_cf = cash_flow.loc["Operating Cash Flow", latest_date] if "Operating Cash Flow" in cash_flow.index else "N/A"
        capex = cash_flow.loc["Capital Expenditure", latest_date] if "Capital Expenditure" in cash_flow.index else "N/A"
        free_cash_flow = cash_flow.loc["Free Cash Flow", latest_date] if "Free Cash Flow" in cash_flow.index else "N/A"

        # Format large numbers
        def format_number(val):
            if isinstance(val, (int, float)):
                if val >= 1e9:
                    return f"${val/1e9:.2f}B"
                elif val >= 1e6:
                    return f"${val/1e6:.2f}M"
                else:
                    return f"${val:,.0f}"
            return str(val)

        return (
            f"**{symbol} Financial Statements**\n"
            f"**Period Ending:** {latest_date.date()}\n\n"
            f"**Income Statement:**\n"
            f"  - Revenue: {format_number(revenue)}\n"
            f"  - Gross Profit: {format_number(gross_profit)}\n"
            f"  - Operating Income: {format_number(operating_income)}\n"
            f"  - Net Income: {format_number(net_income)}\n\n"
            f"**Balance Sheet:**\n"
            f"  - Total Assets: {format_number(total_assets)}\n"
            f"  - Total Debt: {format_number(total_debt)}\n"
            f"  - Cash: {format_number(cash)}\n\n"
            f"**Cash Flow:**\n"
            f"  - Operating CF: {format_number(operating_cf)}\n"
            f"  - CapEx: {format_number(capex)}\n"
            f"  - Free Cash Flow: {format_number(free_cash_flow)}\n"
        )
    except Exception as e:
        return f"Error fetching financials for {symbol}: {str(e)}"


@tool
def get_earnings_history(symbol: str) -> str:
    """Get historical earnings data with surprises.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Recent earnings history with EPS actual vs. estimate
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)
        earnings = ticker.earnings_dates

        if earnings is None or earnings.empty:
            return f"No earnings data found for {symbol}"

        # Get last 4 quarters
        recent_earnings = earnings.head(8)  # Get more in case some are estimates

        output = f"**{symbol} Earnings History**\n\n"

        for date, row in recent_earnings.iterrows():
            eps_actual = row.get("Reported EPS", "N/A")
            eps_estimate = row.get("EPS Estimate", "N/A")
            surprise = row.get("Surprise(%)", "N/A")

            if isinstance(eps_actual, float) and eps_actual != 0:  # Only reported earnings
                output += (
                    f"**{date.date()}**\n"
                    f"  EPS: ${eps_actual:.2f} (Est: ${eps_estimate:.2f})\n"
                    f"  Surprise: {surprise}%\n\n"
                )

        return output or f"No historical earnings data available for {symbol}"
    except Exception as e:
        return f"Error fetching earnings history for {symbol}: {str(e)}"


@tool
def get_earnings_calendar(symbol: str) -> str:
    """Get upcoming earnings date.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Next earnings announcement date and estimate
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        earnings_date = info.get("earningsDate")

        if earnings_date:
            # Format dates
            if isinstance(earnings_date, list):
                date_str = f"{earnings_date[0]} (range: {earnings_date[-1]})"
            else:
                date_str = str(earnings_date)
        else:
            date_str = "N/A"

        # Get earnings info
        calendar = ticker.calendar
        if calendar is not None and not calendar.empty:
            eps_estimate = calendar.get("Earnings Average", "N/A")
            eps_low = calendar.get("Earnings Low", "N/A")
            eps_high = calendar.get("Earnings High", "N/A")
            revenue_estimate = calendar.get("Revenue Average", "N/A")
        else:
            eps_estimate = eps_low = eps_high = revenue_estimate = "N/A"

        return (
            f"**{symbol} Upcoming Earnings**\n\n"
            f"**Earnings Date:** {date_str}\n"
            f"**EPS Estimate:** {eps_estimate} (Low: {eps_low}, High: {eps_high})\n"
            f"**Revenue Estimate:** {revenue_estimate}\n"
        )
    except Exception as e:
        return f"Error fetching earnings calendar for {symbol}: {str(e)}"


@tool
def get_analyst_recommendations(symbol: str) -> str:
    """Get analyst recommendations and price targets.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Analyst ratings distribution and price targets
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)
        recommendations = ticker.recommendations

        if recommendations is None or recommendations.empty:
            return f"No analyst recommendations found for {symbol}"

        # Get latest recommendations summary
        recent = recommendations.tail(10)

        # Count recommendation types
        buy_count = len(recent[recent["To Grade"].str.contains("Buy|Overweight", case=False, na=False)])
        hold_count = len(recent[recent["To Grade"].str.contains("Hold|Neutral", case=False, na=False)])
        sell_count = len(recent[recent["To Grade"].str.contains("Sell|Underweight", case=False, na=False)])

        # Get price targets
        info = ticker.info
        target_high = info.get("targetHighPrice", "N/A")
        target_low = info.get("targetLowPrice", "N/A")
        target_mean = info.get("targetMeanPrice", "N/A")
        target_median = info.get("targetMedianPrice", "N/A")
        num_analysts = info.get("numberOfAnalystOpinions", "N/A")

        output = (
            f"**{symbol} Analyst Recommendations**\n\n"
            f"**Latest 10 Ratings:**\n"
            f"  - Buy/Overweight: {buy_count}\n"
            f"  - Hold/Neutral: {hold_count}\n"
            f"  - Sell/Underweight: {sell_count}\n\n"
            f"**Price Targets:**\n"
            f"  - Mean: ${target_mean}\n"
            f"  - Median: ${target_median}\n"
            f"  - High: ${target_high}\n"
            f"  - Low: ${target_low}\n"
            f"  - Analysts: {num_analysts}\n\n"
            f"**Recent Changes:**\n"
        )

        # Add 3 most recent rating changes
        for _, row in recent.tail(3).iterrows():
            firm = row.get("Firm", "N/A")
            from_grade = row.get("From Grade", "N/A")
            to_grade = row.get("To Grade", "N/A")
            action = row.get("Action", "N/A")

            output += f"  - {firm}: {from_grade} → {to_grade} ({action})\n"

        return output
    except Exception as e:
        return f"Error fetching analyst recommendations for {symbol}: {str(e)}"


@tool
def get_institutional_holders(symbol: str) -> str:
    """Get top institutional holders.

    Args:
        symbol: Stock ticker symbol

    Returns:
        List of top institutional holders with positions
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)
        holders = ticker.institutional_holders

        if holders is None or holders.empty:
            return f"No institutional holder data found for {symbol}"

        output = f"**{symbol} Top Institutional Holders**\n\n"

        for idx, row in holders.head(10).iterrows():
            holder = row.get("Holder", "N/A")
            shares = row.get("Shares", 0)
            date_reported = row.get("Date Reported", "N/A")
            pct_out = row.get("% Out", "N/A")
            value = row.get("Value", 0)

            # Format large numbers
            if isinstance(shares, (int, float)):
                if shares >= 1e9:
                    shares_str = f"{shares/1e9:.2f}B"
                elif shares >= 1e6:
                    shares_str = f"{shares/1e6:.2f}M"
                else:
                    shares_str = f"{shares:,.0f}"
            else:
                shares_str = str(shares)

            output += (
                f"**{holder}**\n"
                f"  Shares: {shares_str} ({pct_out}% of outstanding)\n"
                f"  Value: ${value:,}\n"
                f"  Reported: {date_reported}\n\n"
            )

        return output
    except Exception as e:
        return f"Error fetching institutional holders for {symbol}: {str(e)}"


@tool
def get_company_info(symbol: str) -> str:
    """Get comprehensive company profile and business description.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Company profile with sector, industry, description, and key metrics
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        name = info.get("longName", "N/A")
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        website = info.get("website", "N/A")
        employees = info.get("fullTimeEmployees", "N/A")
        city = info.get("city", "N/A")
        state = info.get("state", "N/A")
        country = info.get("country", "N/A")

        description = info.get("longBusinessSummary", "")
        if description and len(description) > 500:
            description = description[:500] + "..."

        return (
            f"**{name} ({symbol})**\n\n"
            f"**Sector:** {sector}\n"
            f"**Industry:** {industry}\n"
            f"**Location:** {city}, {state}, {country}\n"
            f"**Employees:** {employees:,}\n"
            f"**Website:** {website}\n\n"
            f"**Business Description:**\n{description}\n"
        )
    except Exception as e:
        return f"Error fetching company info for {symbol}: {str(e)}"


@tool
def get_dividends(symbol: str, period: str = "5y") -> str:
    """Get dividend history.

    Args:
        symbol: Stock ticker symbol
        period: Historical period (1y, 2y, 5y, 10y, max)

    Returns:
        Dividend payment history and yield statistics
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)
        dividends = ticker.dividends

        if dividends is None or dividends.empty:
            return f"No dividend data found for {symbol}"

        # Filter by period
        if period != "max":
            years = int(period[:-1])
            dividends = dividends[dividends.index >= dividends.index[-1] - pd.Timedelta(days=365*years)]

        # Calculate statistics
        total_paid = dividends.sum()
        avg_dividend = dividends.mean()
        latest_dividend = dividends.iloc[-1]
        dividend_count = len(dividends)

        # Get current yield
        info = ticker.info
        dividend_yield = info.get("dividendYield", 0)
        if isinstance(dividend_yield, float):
            yield_str = f"{dividend_yield*100:.2f}%"
        else:
            yield_str = "N/A"

        output = (
            f"**{symbol} Dividend History ({period})**\n\n"
            f"**Total Payments:** {dividend_count}\n"
            f"**Total Amount:** ${total_paid:.2f}\n"
            f"**Average Dividend:** ${avg_dividend:.2f}\n"
            f"**Latest Dividend:** ${latest_dividend:.2f} ({dividends.index[-1].date()})\n"
            f"**Current Yield:** {yield_str}\n\n"
            f"**Recent Payments:**\n"
        )

        # Show last 5 payments
        for date, amount in dividends.tail(5).items():
            output += f"  - {date.date()}: ${amount:.2f}\n"

        return output
    except Exception as e:
        return f"Error fetching dividend data for {symbol}: {str(e)}"


@tool
def get_options_chain(symbol: str, expiration: Optional[str] = None) -> str:
    """Get options chain data (calls and puts).

    Args:
        symbol: Stock ticker symbol
        expiration: Expiration date (YYYY-MM-DD), defaults to nearest expiration

    Returns:
        Options chain summary with IV, volume, and open interest
    """
    if error := _check_yfinance_available():
        return error

    try:
        ticker = yf.Ticker(symbol)

        # Get available expiration dates
        expirations = ticker.options
        if not expirations:
            return f"No options data found for {symbol}"

        # Use provided or nearest expiration
        exp_date = expiration if expiration else expirations[0]

        if exp_date not in expirations:
            return (
                f"Expiration {exp_date} not available for {symbol}.\n"
                f"Available expirations: {', '.join(expirations[:5])}"
            )

        # Get options chain
        opt_chain = ticker.option_chain(exp_date)
        calls = opt_chain.calls
        puts = opt_chain.puts

        # Get ATM strike
        current_price = ticker.info.get("currentPrice", 0)

        # Filter for near-the-money options (within 10% of current price)
        if current_price:
            calls_atm = calls[
                (calls["strike"] >= current_price * 0.9) &
                (calls["strike"] <= current_price * 1.1)
            ]
            puts_atm = puts[
                (puts["strike"] >= current_price * 0.9) &
                (puts["strike"] <= current_price * 1.1)
            ]
        else:
            calls_atm = calls.head(5)
            puts_atm = puts.head(5)

        output = (
            f"**{symbol} Options Chain**\n"
            f"**Expiration:** {exp_date}\n"
            f"**Underlying Price:** ${current_price:.2f}\n\n"
            f"**Near-the-Money Calls:**\n"
        )

        for _, row in calls_atm.head(5).iterrows():
            strike = row["strike"]
            last = row.get("lastPrice", 0)
            bid = row.get("bid", 0)
            ask = row.get("ask", 0)
            volume = row.get("volume", 0)
            oi = row.get("openInterest", 0)
            iv = row.get("impliedVolatility", 0)

            output += (
                f"  Strike ${strike:.2f}: Last ${last:.2f}, "
                f"Bid/Ask ${bid:.2f}/${ask:.2f}, "
                f"Vol {volume:,}, OI {oi:,}, IV {iv*100:.1f}%\n"
            )

        output += "\n**Near-the-Money Puts:**\n"

        for _, row in puts_atm.head(5).iterrows():
            strike = row["strike"]
            last = row.get("lastPrice", 0)
            bid = row.get("bid", 0)
            ask = row.get("ask", 0)
            volume = row.get("volume", 0)
            oi = row.get("openInterest", 0)
            iv = row.get("impliedVolatility", 0)

            output += (
                f"  Strike ${strike:.2f}: Last ${last:.2f}, "
                f"Bid/Ask ${bid:.2f}/${ask:.2f}, "
                f"Vol {volume:,}, OI {oi:,}, IV {iv*100:.1f}%\n"
            )

        return output
    except Exception as e:
        return f"Error fetching options chain for {symbol}: {str(e)}"


@tool
def get_market_indices() -> str:
    """Get current prices for major market indices.

    Returns:
        Current prices and changes for S&P 500, Dow Jones, Nasdaq, and Russell 2000
    """
    if error := _check_yfinance_available():
        return error

    try:
        indices = {
            "S&P 500": "^GSPC",
            "Dow Jones": "^DJI",
            "Nasdaq": "^IXIC",
            "Russell 2000": "^RUT",
            "VIX": "^VIX"
        }

        output = "**Major Market Indices**\n\n"

        for name, symbol in indices.items():
            ticker = yf.Ticker(symbol)
            info = ticker.info

            price = info.get("regularMarketPrice", "N/A")
            change = info.get("regularMarketChange", "N/A")
            change_pct = info.get("regularMarketChangePercent", "N/A")

            if isinstance(change_pct, float):
                change_pct = f"{change_pct:+.2f}%"

            output += f"**{name}:** {price:.2f} ({change:+.2f}, {change_pct})\n"

        return output
    except Exception as e:
        return f"Error fetching market indices: {str(e)}"
