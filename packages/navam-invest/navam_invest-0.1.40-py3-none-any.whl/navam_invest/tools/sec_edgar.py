"""SEC EDGAR API tools for corporate filings and regulatory data."""

from typing import Any, Dict, List, Optional

import httpx
from langchain_core.tools import tool


async def _fetch_sec(
    endpoint: str, headers: Optional[Dict[str, str]] = None, **params: Any
) -> Dict[str, Any] | List[Dict[str, Any]]:
    """Fetch data from SEC EDGAR API.

    Note: SEC requires User-Agent header with contact info.
    """
    default_headers = {
        "User-Agent": "navam-invest investment-advisor (contact@navam.io)",
        "Accept-Encoding": "gzip, deflate",
    }

    if headers:
        default_headers.update(headers)

    async with httpx.AsyncClient() as client:
        url = f"https://data.sec.gov/{endpoint}"
        response = await client.get(
            url, params=params, headers=default_headers, timeout=30.0
        )
        response.raise_for_status()
        return response.json()


@tool
async def get_company_filings(symbol: str, filing_type: str = "10-K", limit: int = 5) -> str:
    """Get recent SEC filings for a company.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        filing_type: Type of filing (e.g., '10-K', '10-Q', '8-K', '13F')
        limit: Number of recent filings to return (default: 5)

    Returns:
        List of recent filings with dates and links
    """
    try:
        # First, get company CIK from ticker
        # Note: SEC doesn't have direct ticker lookup, would need mapping
        # For now, return instructive message
        return (
            f"**SEC Filings for {symbol}**\n\n"
            f"To access SEC EDGAR filings:\n"
            f"1. Visit: https://www.sec.gov/cgi-bin/browse-edgar\n"
            f"2. Search for company: {symbol}\n"
            f"3. Filter by form type: {filing_type}\n\n"
            f"*Note: Direct SEC API access requires CIK mapping.*\n"
            f"*Future versions will include automated filing retrieval.*"
        )
    except Exception as e:
        return f"Error fetching SEC filings for {symbol}: {str(e)}"


@tool
async def get_latest_10k(cik: str) -> str:
    """Get latest 10-K annual report for a company.

    Args:
        cik: Central Index Key (CIK) for the company

    Returns:
        Summary of latest 10-K filing
    """
    try:
        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)

        # Fetch company submissions
        data = await _fetch_sec(f"submissions/CIK{cik_padded}.json")

        if "filings" not in data or "recent" not in data["filings"]:
            return f"No filings found for CIK {cik}"

        recent = data["filings"]["recent"]

        # Find latest 10-K
        for i, form in enumerate(recent["form"]):
            if form == "10-K":
                filing_date = recent["filingDate"][i]
                accession = recent["accessionNumber"][i].replace("-", "")
                primary_doc = recent["primaryDocument"][i]

                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik}/{accession}/{primary_doc}"
                )

                return (
                    f"**Latest 10-K Filing**\n\n"
                    f"CIK: {cik}\n"
                    f"Filing Date: {filing_date}\n"
                    f"Accession Number: {recent['accessionNumber'][i]}\n"
                    f"Document: {primary_doc}\n\n"
                    f"**Link:** {filing_url}\n\n"
                    f"*Note: Full XBRL parsing will be added in future versions*"
                )

        return f"No 10-K filings found for CIK {cik}"
    except Exception as e:
        return f"Error fetching 10-K for CIK {cik}: {str(e)}"


@tool
async def get_latest_10q(cik: str) -> str:
    """Get latest 10-Q quarterly report for a company.

    Args:
        cik: Central Index Key (CIK) for the company

    Returns:
        Summary of latest 10-Q filing
    """
    try:
        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)

        # Fetch company submissions
        data = await _fetch_sec(f"submissions/CIK{cik_padded}.json")

        if "filings" not in data or "recent" not in data["filings"]:
            return f"No filings found for CIK {cik}"

        recent = data["filings"]["recent"]

        # Find latest 10-Q
        for i, form in enumerate(recent["form"]):
            if form == "10-Q":
                filing_date = recent["filingDate"][i]
                accession = recent["accessionNumber"][i].replace("-", "")
                primary_doc = recent["primaryDocument"][i]

                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik}/{accession}/{primary_doc}"
                )

                return (
                    f"**Latest 10-Q Filing**\n\n"
                    f"CIK: {cik}\n"
                    f"Filing Date: {filing_date}\n"
                    f"Accession Number: {recent['accessionNumber'][i]}\n"
                    f"Document: {primary_doc}\n\n"
                    f"**Link:** {filing_url}\n\n"
                    f"*Note: Full XBRL parsing will be added in future versions*"
                )

        return f"No 10-Q filings found for CIK {cik}"
    except Exception as e:
        return f"Error fetching 10-Q for CIK {cik}: {str(e)}"


@tool
async def search_company_by_ticker(ticker: str) -> str:
    """Search for company information by ticker symbol.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Company name, CIK, and filing information
    """
    try:
        # Fetch company tickers mapping
        data = await _fetch_sec("files/company_tickers.json")

        # Search for ticker
        ticker_upper = ticker.upper()

        for cik, info in data.items():
            if info.get("ticker", "").upper() == ticker_upper:
                return (
                    f"**Company Information**\n\n"
                    f"Ticker: {info.get('ticker')}\n"
                    f"Name: {info.get('title')}\n"
                    f"CIK: {info.get('cik_str')}\n\n"
                    f"*Use CIK {info.get('cik_str')} to fetch specific filings*"
                )

        return f"No company found with ticker {ticker}"
    except Exception as e:
        return f"Error searching for ticker {ticker}: {str(e)}"


@tool
async def get_institutional_holdings(cik: str) -> str:
    """Get 13F institutional holdings for an investment company.

    Args:
        cik: Central Index Key (CIK) for the institutional investor

    Returns:
        Summary of latest 13F holdings
    """
    try:
        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)

        # Fetch company submissions
        data = await _fetch_sec(f"submissions/CIK{cik_padded}.json")

        if "filings" not in data or "recent" not in data["filings"]:
            return f"No filings found for CIK {cik}"

        recent = data["filings"]["recent"]

        # Find latest 13F
        for i, form in enumerate(recent["form"]):
            if form == "13F-HR":
                filing_date = recent["filingDate"][i]
                accession = recent["accessionNumber"][i].replace("-", "")
                primary_doc = recent["primaryDocument"][i]

                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik}/{accession}/{primary_doc}"
                )

                return (
                    f"**Latest 13F Holdings Report**\n\n"
                    f"Institution CIK: {cik}\n"
                    f"Filing Date: {filing_date}\n"
                    f"Accession Number: {recent['accessionNumber'][i]}\n\n"
                    f"**Link:** {filing_url}\n\n"
                    f"*Note: Detailed holdings parsing will be added in future versions*"
                )

        return f"No 13F filings found for CIK {cik}"
    except Exception as e:
        return f"Error fetching 13F for CIK {cik}: {str(e)}"


@tool
async def get_latest_8k(cik: str, limit: int = 5) -> str:
    """Get recent 8-K current reports (material events).

    8-K filings disclose material corporate events like earnings releases,
    management changes, acquisitions, bankruptcy, etc.

    Args:
        cik: Central Index Key (CIK) for the company
        limit: Number of recent 8-Ks to return (default: 5)

    Returns:
        List of recent 8-K filings with dates and links
    """
    try:
        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)

        # Fetch company submissions
        data = await _fetch_sec(f"submissions/CIK{cik_padded}.json")

        if "filings" not in data or "recent" not in data["filings"]:
            return f"No filings found for CIK {cik}"

        recent = data["filings"]["recent"]

        # Find recent 8-Ks
        eightks = []
        for i, form in enumerate(recent["form"]):
            if form == "8-K" and len(eightks) < limit:
                filing_date = recent["filingDate"][i]
                accession = recent["accessionNumber"][i].replace("-", "")
                primary_doc = recent["primaryDocument"][i]

                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik}/{accession}/{primary_doc}"
                )

                eightks.append({
                    "date": filing_date,
                    "accession": recent["accessionNumber"][i],
                    "url": filing_url
                })

        if not eightks:
            return f"No 8-K filings found for CIK {cik}"

        output = f"**Recent 8-K Filings (Material Events)**\n\n"
        for filing in eightks:
            output += (
                f"**{filing['date']}**\n"
                f"Accession: {filing['accession']}\n"
                f"Link: {filing['url']}\n\n"
            )

        return output
    except Exception as e:
        return f"Error fetching 8-K filings for CIK {cik}: {str(e)}"


@tool
async def get_company_facts(cik: str) -> str:
    """Get company facts (structured XBRL data) from SEC.

    Returns key financial metrics extracted from XBRL filings including
    assets, revenues, net income, EPS, and other standardized data points.

    Args:
        cik: Central Index Key (CIK) for the company

    Returns:
        Key financial facts and metrics
    """
    try:
        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)

        # Fetch company facts
        data = await _fetch_sec(f"api/xbrl/companyfacts/CIK{cik_padded}.json")

        if "facts" not in data:
            return f"No company facts found for CIK {cik}"

        company_name = data.get("entityName", "Unknown")
        facts = data["facts"]

        # Extract US-GAAP facts
        us_gaap = facts.get("us-gaap", {})

        # Common financial metrics
        metrics_of_interest = {
            "Assets": "Total Assets",
            "Liabilities": "Total Liabilities",
            "StockholdersEquity": "Stockholders Equity",
            "Revenues": "Total Revenues",
            "NetIncomeLoss": "Net Income",
            "EarningsPerShareBasic": "EPS (Basic)",
            "EarningsPerShareDiluted": "EPS (Diluted)",
            "OperatingIncomeLoss": "Operating Income",
            "CashAndCashEquivalentsAtCarryingValue": "Cash & Equivalents",
        }

        output = f"**{company_name} - Company Facts (XBRL)**\n\n"

        for metric_key, metric_label in metrics_of_interest.items():
            if metric_key in us_gaap:
                metric_data = us_gaap[metric_key]
                units = metric_data.get("units", {})

                # Get most recent value (usually in USD)
                if "USD" in units:
                    values = units["USD"]
                    if values:
                        # Sort by filing date and get most recent
                        sorted_values = sorted(
                            values,
                            key=lambda x: x.get("filed", ""),
                            reverse=True
                        )
                        latest = sorted_values[0]
                        value = latest.get("val", "N/A")
                        end_date = latest.get("end", "N/A")
                        form = latest.get("form", "N/A")

                        # Format large numbers
                        if isinstance(value, (int, float)):
                            if value >= 1e12:
                                value_str = f"${value/1e12:.2f}T"
                            elif value >= 1e9:
                                value_str = f"${value/1e9:.2f}B"
                            elif value >= 1e6:
                                value_str = f"${value/1e6:.2f}M"
                            else:
                                value_str = f"${value:,.2f}"
                        else:
                            value_str = str(value)

                        output += f"**{metric_label}:** {value_str} (as of {end_date}, {form})\n"

        return output
    except Exception as e:
        return f"Error fetching company facts for CIK {cik}: {str(e)}"


@tool
async def search_filings_by_form(cik: str, form_type: str, limit: int = 10) -> str:
    """Search for specific SEC filing types.

    Args:
        cik: Central Index Key (CIK) for the company
        form_type: SEC form type (e.g., '10-K', '10-Q', '8-K', 'DEF 14A', 'S-1', '4')
        limit: Maximum number of filings to return (default: 10)

    Returns:
        List of filings matching the form type
    """
    try:
        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)

        # Fetch company submissions
        data = await _fetch_sec(f"submissions/CIK{cik_padded}.json")

        if "filings" not in data or "recent" not in data["filings"]:
            return f"No filings found for CIK {cik}"

        company_name = data.get("name", "Unknown")
        recent = data["filings"]["recent"]

        # Find matching filings
        filings = []
        for i, form in enumerate(recent["form"]):
            if form == form_type and len(filings) < limit:
                filing_date = recent["filingDate"][i]
                accession = recent["accessionNumber"][i].replace("-", "")
                primary_doc = recent["primaryDocument"][i]
                report_date = recent.get("reportDate", ["N/A"] * len(recent["form"]))[i]

                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik}/{accession}/{primary_doc}"
                )

                filings.append({
                    "date": filing_date,
                    "report_date": report_date,
                    "accession": recent["accessionNumber"][i],
                    "url": filing_url
                })

        if not filings:
            return f"No {form_type} filings found for {company_name} (CIK {cik})"

        output = f"**{company_name} - {form_type} Filings**\n\n"
        for filing in filings:
            output += (
                f"**Filed:** {filing['date']} (Period: {filing['report_date']})\n"
                f"Accession: {filing['accession']}\n"
                f"Link: {filing['url']}\n\n"
            )

        return output
    except Exception as e:
        return f"Error searching {form_type} filings for CIK {cik}: {str(e)}"


@tool
async def get_insider_transactions(cik: str, limit: int = 10) -> str:
    """Get recent insider trading activity (Form 4 filings).

    Form 4 reports changes in beneficial ownership by company insiders
    (officers, directors, and >10% shareholders).

    Args:
        cik: Central Index Key (CIK) for the company
        limit: Maximum number of Form 4 filings to return (default: 10)

    Returns:
        Recent insider trading transactions
    """
    try:
        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)

        # Fetch company submissions
        data = await _fetch_sec(f"submissions/CIK{cik_padded}.json")

        if "filings" not in data or "recent" not in data["filings"]:
            return f"No filings found for CIK {cik}"

        company_name = data.get("name", "Unknown")
        recent = data["filings"]["recent"]

        # Find Form 4 filings
        form4s = []
        for i, form in enumerate(recent["form"]):
            if form == "4" and len(form4s) < limit:
                filing_date = recent["filingDate"][i]
                accession = recent["accessionNumber"][i].replace("-", "")
                primary_doc = recent["primaryDocument"][i]

                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik}/{accession}/{primary_doc}"
                )

                form4s.append({
                    "date": filing_date,
                    "accession": recent["accessionNumber"][i],
                    "url": filing_url
                })

        if not form4s:
            return f"No Form 4 (insider trading) filings found for {company_name}"

        output = f"**{company_name} - Recent Insider Transactions (Form 4)**\n\n"
        for filing in form4s:
            output += (
                f"**{filing['date']}**\n"
                f"Accession: {filing['accession']}\n"
                f"Link: {filing['url']}\n\n"
            )

        output += "*Note: Full transaction parsing (buy/sell amounts) will be added in future versions*\n"

        return output
    except Exception as e:
        return f"Error fetching insider transactions for CIK {cik}: {str(e)}"
