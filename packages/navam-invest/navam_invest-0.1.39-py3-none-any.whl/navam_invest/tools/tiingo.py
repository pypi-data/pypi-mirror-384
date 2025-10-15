"""Tiingo API tools for historical fundamentals and quarterly tracking."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from langchain_core.tools import tool


async def _fetch_tiingo(
    endpoint: str, api_key: str, **params: Any
) -> Dict[str, Any] | List[Dict[str, Any]]:
    """Fetch data from Tiingo API.

    Args:
        endpoint: API endpoint path (e.g., 'tiingo/fundamentals/aapl/daily')
        api_key: Tiingo API key
        **params: Query parameters

    Returns:
        JSON response data
    """
    async with httpx.AsyncClient() as client:
        url = f"https://api.tiingo.com/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {api_key}",
        }
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 403:
                raise Exception(
                    "Tiingo API access denied. Free tier may not have access to fundamentals. "
                    "Please check your API key and subscription level."
                )
            elif status_code == 401:
                raise Exception(
                    "Tiingo API authentication failed. Please verify your API key."
                )
            elif status_code == 429:
                raise Exception(
                    "Tiingo API rate limit exceeded. Free tier: 50 symbols/hour, 1000 requests/day."
                )
            elif status_code == 404:
                raise Exception(
                    "Tiingo API endpoint not found. This endpoint may require a paid subscription."
                )
            else:
                raise Exception(f"Tiingo API error: HTTP {status_code} - {e.response.text}")


@tool
async def get_fundamentals_definitions(api_key: str, ticker: Optional[str] = None) -> str:
    """Get definitions for fundamental data fields.

    Retrieves metadata about available fundamental metrics including field names,
    descriptions, and data types.

    Args:
        api_key: Tiingo API key
        ticker: Optional stock ticker to get ticker-specific definitions

    Returns:
        Formatted string with fundamental field definitions
    """
    try:
        endpoint = "tiingo/fundamentals/definitions"
        params = {}
        if ticker:
            params["ticker"] = ticker.upper()

        data = await _fetch_tiingo(endpoint, api_key, **params)

        if not data:
            return "No fundamental definitions found"

        result = ["**Tiingo Fundamentals - Field Definitions**\n"]

        # Handle different response formats
        if isinstance(data, dict):
            # If response is a dict of field definitions
            result.append(f"Total Fields: {len(data)}\n")

            # Show sample of key fields
            key_fields = ["marketCap", "enterpriseVal", "peRatio", "pbRatio",
                         "revenue", "netIncome", "freeCashFlow", "totalDebt"]

            result.append("**Key Financial Metrics:**")
            for field in key_fields:
                if field in data:
                    field_info = data[field]
                    if isinstance(field_info, dict):
                        desc = field_info.get("description", "No description")
                        result.append(f"- {field}: {desc}")
                    else:
                        result.append(f"- {field}: Available")
        elif isinstance(data, list):
            result.append(f"Available fields: {len(data)}\n")
            for field in data[:20]:  # Show first 20
                if isinstance(field, dict):
                    name = field.get("name", "N/A")
                    desc = field.get("description", "No description")
                    result.append(f"- {name}: {desc}")
                else:
                    result.append(f"- {field}")

        result.append(f"\n*Use these field names when querying daily or statement data*")

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching fundamental definitions: {str(e)}"


@tool
async def get_fundamentals_daily(
    ticker: str,
    api_key: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """Get daily-updated fundamental metrics.

    Retrieves fundamentals that update daily like market cap, PE ratio, and shares outstanding.
    Free tier provides 5 years of historical data.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        api_key: Tiingo API key
        start_date: Start date in YYYY-MM-DD format (default: 90 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)

    Returns:
        Formatted string with daily fundamental metrics
    """
    try:
        ticker = ticker.upper()

        # Default to last 90 days if not specified
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            ninety_days_ago = datetime.now() - timedelta(days=90)
            start_date = ninety_days_ago.strftime("%Y-%m-%d")

        endpoint = f"tiingo/fundamentals/{ticker}/daily"
        params = {
            "startDate": start_date,
            "endDate": end_date,
        }

        data = await _fetch_tiingo(endpoint, api_key, **params)

        if not data:
            return f"No daily fundamental data found for {ticker}"

        # Convert to list if single dict
        data_list = data if isinstance(data, list) else [data]

        if not data_list:
            return f"No daily fundamental data for {ticker} between {start_date} and {end_date}"

        result = [f"**{ticker} - Daily Fundamentals** ({start_date} to {end_date})\n"]

        # Get most recent data point
        latest = data_list[0] if isinstance(data_list[0], dict) else {}
        date = latest.get("date", "N/A")

        result.append(f"**Most Recent Data ({date}):**\n")

        # Key metrics that update daily
        market_cap = latest.get("marketCap")
        enterprise_val = latest.get("enterpriseVal")
        pe_ratio = latest.get("peRatio")
        pb_ratio = latest.get("pbRatio")

        if market_cap:
            result.append(f"Market Cap: ${market_cap:,.0f}")
        if enterprise_val:
            result.append(f"Enterprise Value: ${enterprise_val:,.0f}")
        if pe_ratio:
            result.append(f"P/E Ratio: {pe_ratio:.2f}")
        if pb_ratio:
            result.append(f"P/B Ratio: {pb_ratio:.2f}")

        # Show historical trend if multiple data points
        if len(data_list) > 1:
            result.append(f"\n**Historical Trend ({len(data_list)} data points):**")

            # Calculate market cap trend
            if market_cap and data_list[-1].get("marketCap"):
                oldest_mc = data_list[-1]["marketCap"]
                mc_change_pct = ((market_cap - oldest_mc) / oldest_mc) * 100
                trend = "📈" if mc_change_pct > 0 else "📉"
                result.append(f"Market Cap Change: {trend} {mc_change_pct:+.2f}%")

        result.append(f"\n*Data retrieved: {len(data_list)} daily observations*")
        result.append(f"*Free tier: 5 years of historical data available*")

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching daily fundamentals for {ticker}: {str(e)}"


@tool
async def get_fundamentals_statements(
    ticker: str,
    api_key: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    as_reported: bool = True
) -> str:
    """Get fundamental data from quarterly financial statements.

    Retrieves income statement, balance sheet, and cash flow metrics from quarterly
    filings. Free tier provides 5 years of historical statements.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        api_key: Tiingo API key
        start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        as_reported: If True, get data exactly as reported to SEC. If False, get corrected data.

    Returns:
        Formatted string with quarterly statement data
    """
    try:
        ticker = ticker.upper()

        # Default to last 1 year if not specified
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            one_year_ago = datetime.now() - timedelta(days=365)
            start_date = one_year_ago.strftime("%Y-%m-%d")

        endpoint = f"tiingo/fundamentals/{ticker}/statements"
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "asReported": str(as_reported).lower(),
        }

        data = await _fetch_tiingo(endpoint, api_key, **params)

        if not data:
            return f"No quarterly statement data found for {ticker}"

        # Convert to list if single dict
        data_list = data if isinstance(data, list) else [data]

        if not data_list:
            return f"No statement data for {ticker} between {start_date} and {end_date}"

        result = [
            f"**{ticker} - Quarterly Financial Statements** ({start_date} to {end_date})\n",
            f"*Data mode: {'As Reported to SEC' if as_reported else 'With Corrections'}*\n"
        ]

        # Process latest quarters (limit to 4 most recent)
        recent_quarters = data_list[:4]

        for i, quarter in enumerate(recent_quarters, 1):
            if not isinstance(quarter, dict):
                continue

            # Extract quarter info
            quarter_date = quarter.get("date", quarter.get("quarter", "N/A"))
            year = quarter.get("year", "N/A")
            quarter_num = quarter.get("quarter", "N/A")

            result.append(f"\n**Quarter {i}: Q{quarter_num} {year}** ({quarter_date})")

            # Income Statement metrics
            revenue = quarter.get("revenue") or quarter.get("totalRevenue")
            net_income = quarter.get("netIncome") or quarter.get("netIncomeAvailToCommon")
            gross_profit = quarter.get("grossProfit")
            operating_income = quarter.get("operatingIncome")

            if revenue or net_income or gross_profit or operating_income:
                result.append("  Income Statement:")
                if revenue:
                    result.append(f"    Revenue: ${revenue:,.0f}")
                if gross_profit:
                    result.append(f"    Gross Profit: ${gross_profit:,.0f}")
                if operating_income:
                    result.append(f"    Operating Income: ${operating_income:,.0f}")
                if net_income:
                    result.append(f"    Net Income: ${net_income:,.0f}")

            # Balance Sheet metrics
            total_assets = quarter.get("totalAssets")
            total_debt = quarter.get("totalDebt")
            cash = quarter.get("cash") or quarter.get("cashAndCashEquivalents")
            stockholders_equity = quarter.get("totalEquity") or quarter.get("stockholdersEquity")

            if total_assets or total_debt or cash or stockholders_equity:
                result.append("  Balance Sheet:")
                if total_assets:
                    result.append(f"    Total Assets: ${total_assets:,.0f}")
                if cash:
                    result.append(f"    Cash: ${cash:,.0f}")
                if total_debt:
                    result.append(f"    Total Debt: ${total_debt:,.0f}")
                if stockholders_equity:
                    result.append(f"    Stockholders' Equity: ${stockholders_equity:,.0f}")

            # Cash Flow metrics
            operating_cf = quarter.get("operatingCashFlow") or quarter.get("cashFromOperations")
            capex = quarter.get("capex") or quarter.get("capitalExpenditures")
            free_cf = quarter.get("freeCashFlow")

            if operating_cf or capex or free_cf:
                result.append("  Cash Flow:")
                if operating_cf:
                    result.append(f"    Operating Cash Flow: ${operating_cf:,.0f}")
                if capex:
                    result.append(f"    CapEx: ${capex:,.0f}")
                if free_cf:
                    result.append(f"    Free Cash Flow: ${free_cf:,.0f}")

        result.append(f"\n*Retrieved {len(data_list)} quarterly statements*")
        result.append(f"*Free tier: 5 years of historical statements available*")

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching quarterly statements for {ticker}: {str(e)}"


@tool
async def get_historical_fundamentals(
    ticker: str,
    api_key: str,
    years: int = 5
) -> str:
    """Get multi-year historical fundamental trends.

    Retrieves and analyzes fundamental trends over multiple years for long-term
    investment analysis. Combines both daily metrics and quarterly statements.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        api_key: Tiingo API key
        years: Number of years of history to retrieve (max 5 on free tier)

    Returns:
        Formatted string with historical fundamental analysis
    """
    try:
        ticker = ticker.upper()

        # Limit to 5 years on free tier
        years = min(years, 5)

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=years*365)).strftime("%Y-%m-%d")

        # Fetch quarterly statements for trend analysis
        endpoint = f"tiingo/fundamentals/{ticker}/statements"
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "asReported": "false",  # Use corrected data for trend analysis
        }

        data = await _fetch_tiingo(endpoint, api_key, **params)

        if not data:
            return f"No historical fundamental data found for {ticker}"

        data_list = data if isinstance(data, list) else [data]

        if len(data_list) < 2:
            return f"Insufficient historical data for {ticker} (need at least 2 quarters)"

        result = [f"**{ticker} - {years}-Year Fundamental Trends**\n"]

        # Extract revenue trend
        revenues = []
        net_incomes = []
        quarters = []

        for quarter in data_list:
            if not isinstance(quarter, dict):
                continue

            quarter_label = f"Q{quarter.get('quarter', '?')} {quarter.get('year', '?')}"
            quarters.append(quarter_label)

            revenue = quarter.get("revenue") or quarter.get("totalRevenue") or 0
            net_income = quarter.get("netIncome") or quarter.get("netIncomeAvailToCommon") or 0

            revenues.append(revenue)
            net_incomes.append(net_income)

        # Calculate trends
        if revenues and revenues[0] and revenues[-1]:
            latest_revenue = revenues[0]
            oldest_revenue = revenues[-1]
            revenue_cagr = (((latest_revenue / oldest_revenue) ** (1/years)) - 1) * 100

            result.append(f"**Revenue Growth:**")
            result.append(f"Latest (Q{data_list[0].get('quarter')} {data_list[0].get('year')}): ${latest_revenue:,.0f}")
            result.append(f"Oldest (Q{data_list[-1].get('quarter')} {data_list[-1].get('year')}): ${oldest_revenue:,.0f}")
            result.append(f"{years}-Year CAGR: {revenue_cagr:+.2f}%\n")

        if net_incomes and net_incomes[0] and net_incomes[-1]:
            latest_ni = net_incomes[0]
            oldest_ni = net_incomes[-1]

            result.append(f"**Profitability Trend:**")
            result.append(f"Latest Net Income: ${latest_ni:,.0f}")
            result.append(f"Oldest Net Income: ${oldest_ni:,.0f}")

            if oldest_ni != 0:
                ni_change_pct = ((latest_ni - oldest_ni) / abs(oldest_ni)) * 100
                result.append(f"Net Income Change: {ni_change_pct:+.2f}%\n")

        # Show quarterly progression (last 8 quarters)
        result.append(f"**Recent Quarterly Performance (Last 8 Quarters):**")
        for i in range(min(8, len(data_list))):
            quarter = data_list[i]
            q_label = f"Q{quarter.get('quarter', '?')} {quarter.get('year', '?')}"
            q_revenue = quarter.get("revenue") or quarter.get("totalRevenue") or 0
            q_ni = quarter.get("netIncome") or quarter.get("netIncomeAvailToCommon") or 0

            result.append(f"{q_label}: Revenue ${q_revenue:,.0f}, Net Income ${q_ni:,.0f}")

        result.append(f"\n*Analyzed {len(data_list)} quarters over {years} years*")
        result.append(f"*CAGR = Compound Annual Growth Rate*")

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching historical fundamentals for {ticker}: {str(e)}"
