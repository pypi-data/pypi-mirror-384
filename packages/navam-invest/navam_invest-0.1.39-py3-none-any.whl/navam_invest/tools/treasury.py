"""U.S. Treasury Fiscal Data API tools for yield curves and treasury data."""

from typing import Any, Dict, List, Optional

import httpx
from langchain_core.tools import tool


async def _fetch_treasury(
    endpoint: str, **params: Any
) -> Dict[str, Any] | List[Dict[str, Any]]:
    """Fetch data from U.S. Treasury Fiscal Data API (no API key required)."""
    async with httpx.AsyncClient() as client:
        url = f"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/{endpoint}"
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()


@tool
async def get_treasury_yield_curve() -> str:
    """Get current U.S. Treasury yield curve (1M to 30Y).

    Returns:
        Formatted string with current treasury yields across all maturities
    """
    try:
        # Fetch latest daily treasury yield curve rates
        data = await _fetch_treasury(
            "v2/accounting/od/avg_interest_rates",
            fields="record_date,security_desc,avg_interest_rate_amt",
            filter="security_type_desc:eq:Treasury",
            sort="-record_date",
            page_size=20,
        )

        if "data" not in data or not data["data"]:
            return "No treasury yield data available"

        rates = data["data"]

        # Group by most recent date
        latest_date = rates[0]["record_date"] if rates else "N/A"

        # Parse yields
        yield_map = {}
        for rate in rates:
            if rate["record_date"] == latest_date:
                desc = rate["security_desc"]
                yield_val = rate["avg_interest_rate_amt"]

                # Map to standard maturities
                if "1-Month" in desc or "4-Week" in desc:
                    yield_map["1M"] = yield_val
                elif "3-Month" in desc:
                    yield_map["3M"] = yield_val
                elif "6-Month" in desc:
                    yield_map["6M"] = yield_val
                elif "1-Year" in desc:
                    yield_map["1Y"] = yield_val
                elif "2-Year" in desc:
                    yield_map["2Y"] = yield_val
                elif "5-Year" in desc:
                    yield_map["5Y"] = yield_val
                elif "10-Year" in desc:
                    yield_map["10Y"] = yield_val
                elif "30-Year" in desc:
                    yield_map["30Y"] = yield_val

        result = [f"**U.S. Treasury Yield Curve**\n", f"Date: {latest_date}\n"]

        # Display in order
        maturities = ["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "30Y"]
        for maturity in maturities:
            if maturity in yield_map:
                result.append(f"{maturity}: {yield_map[maturity]}%")

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching treasury yield curve: {str(e)}"


@tool
async def get_treasury_rate(maturity: str) -> str:
    """Get current yield for specific treasury maturity.

    Args:
        maturity: Treasury maturity (e.g., '10Y', '2Y', '30Y')

    Returns:
        Current yield for specified maturity
    """
    try:
        # Map user input to API security descriptions
        maturity_map = {
            "1M": "Treasury Bills (4-Week)",
            "3M": "Treasury Bills (3-Month)",
            "6M": "Treasury Bills (6-Month)",
            "1Y": "Treasury Notes (1-Year)",
            "2Y": "Treasury Notes (2-Year)",
            "5Y": "Treasury Notes (5-Year)",
            "10Y": "Treasury Notes (10-Year)",
            "30Y": "Treasury Bonds (30-Year)",
        }

        maturity_upper = maturity.upper()
        if maturity_upper not in maturity_map:
            return f"Invalid maturity: {maturity}. Valid options: {', '.join(maturity_map.keys())}"

        # Fetch latest rates
        data = await _fetch_treasury(
            "v2/accounting/od/avg_interest_rates",
            fields="record_date,security_desc,avg_interest_rate_amt",
            filter="security_type_desc:eq:Treasury",
            sort="-record_date",
            page_size=20,
        )

        if "data" not in data or not data["data"]:
            return f"No yield data available for {maturity}"

        # Find matching maturity
        for rate in data["data"]:
            desc = rate["security_desc"]
            if any(
                term in desc for term in maturity_map[maturity_upper].split("(")[1:]
            ):
                yield_val = rate["avg_interest_rate_amt"]
                date = rate["record_date"]
                return (
                    f"**{maturity_upper} Treasury Yield**\n"
                    f"Rate: {yield_val}%\n"
                    f"Date: {date}"
                )

        return f"No data found for {maturity} treasury"
    except Exception as e:
        return f"Error fetching {maturity} treasury rate: {str(e)}"


@tool
async def get_treasury_yield_spread(short_maturity: str, long_maturity: str) -> str:
    """Calculate yield spread between two treasury maturities.

    Args:
        short_maturity: Shorter maturity (e.g., '2Y')
        long_maturity: Longer maturity (e.g., '10Y')

    Returns:
        Yield spread and interpretation
    """
    try:
        # Fetch latest rates
        data = await _fetch_treasury(
            "v2/accounting/od/avg_interest_rates",
            fields="record_date,security_desc,avg_interest_rate_amt",
            filter="security_type_desc:eq:Treasury",
            sort="-record_date",
            page_size=20,
        )

        if "data" not in data or not data["data"]:
            return "No treasury yield data available"

        rates = data["data"]
        latest_date = rates[0]["record_date"] if rates else "N/A"

        # Extract yields
        maturity_patterns = {
            "1M": ["4-Week", "1-Month"],
            "3M": ["3-Month"],
            "6M": ["6-Month"],
            "1Y": ["1-Year"],
            "2Y": ["2-Year"],
            "5Y": ["5-Year"],
            "10Y": ["10-Year"],
            "30Y": ["30-Year"],
        }

        short_yield = None
        long_yield = None

        short_upper = short_maturity.upper()
        long_upper = long_maturity.upper()

        for rate in rates:
            if rate["record_date"] == latest_date:
                desc = rate["security_desc"]

                # Check short maturity
                if short_upper in maturity_patterns:
                    if any(p in desc for p in maturity_patterns[short_upper]):
                        short_yield = float(rate["avg_interest_rate_amt"])

                # Check long maturity
                if long_upper in maturity_patterns:
                    if any(p in desc for p in maturity_patterns[long_upper]):
                        long_yield = float(rate["avg_interest_rate_amt"])

        if short_yield is None or long_yield is None:
            return f"Could not find yields for {short_maturity} and/or {long_maturity}"

        spread = long_yield - short_yield

        # Interpret spread
        if spread > 0:
            interpretation = "Normal (upward sloping curve - economic expansion expected)"
        elif spread < 0:
            interpretation = "Inverted (recession signal - higher short-term rates)"
        else:
            interpretation = "Flat (transition period or uncertainty)"

        return (
            f"**Treasury Yield Spread: {short_upper} - {long_upper}**\n\n"
            f"{short_upper} Yield: {short_yield}%\n"
            f"{long_upper} Yield: {long_yield}%\n"
            f"Spread: {spread:.2f}%\n\n"
            f"**Interpretation:** {interpretation}\n"
            f"Date: {latest_date}"
        )
    except Exception as e:
        return f"Error calculating yield spread: {str(e)}"


@tool
async def get_debt_to_gdp() -> str:
    """Get current U.S. debt-to-GDP ratio.

    Returns:
        Latest debt-to-GDP ratio and trend
    """
    try:
        # Fetch federal debt data
        data = await _fetch_treasury(
            "v2/accounting/od/debt_to_penny",
            fields="record_date,tot_pub_debt_out_amt",
            sort="-record_date",
            page_size=1,
        )

        if "data" not in data or not data["data"]:
            return "No federal debt data available"

        debt_data = data["data"][0]
        debt = float(debt_data["tot_pub_debt_out_amt"])
        date = debt_data["record_date"]

        # Note: GDP data would need to come from FRED or another source
        # For now, just return debt amount
        return (
            f"**U.S. Federal Debt**\n\n"
            f"Total Public Debt: ${debt:,.0f}\n"
            f"Date: {date}\n\n"
            f"*Note: For debt-to-GDP ratio, combine with GDP data from FRED*"
        )
    except Exception as e:
        return f"Error fetching debt data: {str(e)}"
