"""Financial Modeling Prep (FMP) fundamental data fetching functions.

Drop-in alternative to yfinance/alpha_vantage for the ``fundamental_data``
category.  Uses the FMP REST API v3 via ``requests``.
Requires the ``FMP_API_KEY`` environment variable.
"""

import os
from datetime import datetime
from typing import Annotated

import requests

_BASE_URL = "https://financialmodelingprep.com/api/v3"


def _api_key() -> str | None:
    return os.environ.get("FMP_API_KEY")


def _get_json(endpoint: str, params: dict | None = None) -> list | dict | str:
    """Perform a GET request against FMP and return the parsed JSON.

    Returns a descriptive error string on failure.
    """
    key = _api_key()
    if not key:
        return "Error: FMP_API_KEY not set"

    url = f"{_BASE_URL}/{endpoint}"
    query: dict = {"apikey": key}
    if params:
        query.update(params)

    try:
        resp = requests.get(url, params=query, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return f"Error fetching data: {e}"


def _filter_by_date(items: list[dict], curr_date: str | None, date_key: str = "date") -> list[dict]:
    """Return only items whose *date_key* value is on or before *curr_date*."""
    if not curr_date or not isinstance(items, list):
        return items if isinstance(items, list) else []
    return [item for item in items if item.get(date_key, "") <= curr_date]


def _format_profile(data: dict) -> str:
    """Format a single company profile dict as human-readable text."""
    fields = [
        ("Name", "companyName"),
        ("Symbol", "symbol"),
        ("Exchange", "exchange"),
        ("Sector", "sector"),
        ("Industry", "industry"),
        ("Market Cap", "mktCap"),
        ("Price", "price"),
        ("Beta", "beta"),
        ("Volume Avg", "volAvg"),
        ("Last Dividend", "lastDiv"),
        ("52 Week Range", "range"),
        ("PE Ratio (TTM)", "pe"),  # some endpoints use "pe"
        ("EPS", "eps"),
        ("Revenue (TTM)", "revenue"),
        ("Net Income", "netIncome"),
        ("Profit Margin", "profitMargin"),
        ("Return on Equity", "roe"),
        ("Return on Assets", "roa"),
        ("Debt to Equity", "debtToEquity"),
        ("Current Ratio", "currentRatio"),
        ("Free Cash Flow", "freeCashFlow"),
        ("Description", "description"),
    ]

    lines: list[str] = []
    for label, key in fields:
        value = data.get(key)
        if value is not None and value != "":
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def _format_financial_statement(items: list[dict], title: str) -> str:
    """Format a list of financial statement dicts into readable text."""
    if not items:
        return f"No {title} data available."

    # Keys to skip (metadata / noise)
    skip = {"link", "finalLink", "cik", "acceptedDate", "fillingDate"}
    parts: list[str] = []

    for item in items:
        period_label = item.get("date", "Unknown date")
        period = item.get("period", "")
        header = f"--- {period_label}"
        if period:
            header += f" ({period})"
        header += " ---"
        parts.append(header)

        for key, value in item.items():
            if key in skip or key in ("date", "period", "symbol", "reportedCurrency", "calendarYear"):
                continue
            if value is None:
                continue
            # Pretty-print the key
            label = key.replace("_", " ").title()
            parts.append(f"  {label}: {value}")
        parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API -- signatures match the ``fundamental_data`` category contract
# ---------------------------------------------------------------------------

def get_fundamentals(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date"] = None,
) -> str:
    """Retrieve company profile / fundamentals from FMP.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        curr_date: Not directly used for profile; kept for API compatibility.

    Returns:
        Formatted string of company fundamentals.
    """
    data = _get_json(f"profile/{ticker.upper()}")
    if isinstance(data, str):
        return data  # error string

    if not data:
        return f"No fundamentals data found for {ticker}"

    profile = data[0] if isinstance(data, list) else data

    header = f"# Company Fundamentals for {ticker.upper()}\n"
    header += f"# Source: Financial Modeling Prep\n\n"
    return header + _format_profile(profile)


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "annual or quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date YYYY-MM-DD"] = None,
) -> str:
    """Retrieve balance sheet statements from FMP.

    Args:
        ticker: Stock ticker symbol.
        freq: ``"annual"`` or ``"quarterly"``.
        curr_date: If provided, only statements on or before this date.

    Returns:
        Formatted balance sheet text.
    """
    params = {"period": freq.lower()}
    data = _get_json(f"balance-sheet-statement/{ticker.upper()}", params)
    if isinstance(data, str):
        return data

    if not data:
        return f"No balance sheet data found for {ticker}"

    data = _filter_by_date(data, curr_date)

    header = f"# Balance Sheet for {ticker.upper()} ({freq})\n"
    header += f"# Source: Financial Modeling Prep\n\n"
    return header + _format_financial_statement(data, "balance sheet")


def get_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "annual or quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date YYYY-MM-DD"] = None,
) -> str:
    """Retrieve cash flow statements from FMP.

    Args:
        ticker: Stock ticker symbol.
        freq: ``"annual"`` or ``"quarterly"``.
        curr_date: If provided, only statements on or before this date.

    Returns:
        Formatted cash flow text.
    """
    params = {"period": freq.lower()}
    data = _get_json(f"cash-flow-statement/{ticker.upper()}", params)
    if isinstance(data, str):
        return data

    if not data:
        return f"No cash flow data found for {ticker}"

    data = _filter_by_date(data, curr_date)

    header = f"# Cash Flow Statement for {ticker.upper()} ({freq})\n"
    header += f"# Source: Financial Modeling Prep\n\n"
    return header + _format_financial_statement(data, "cash flow")


def get_income_statement(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "annual or quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date YYYY-MM-DD"] = None,
) -> str:
    """Retrieve income statements from FMP.

    Args:
        ticker: Stock ticker symbol.
        freq: ``"annual"`` or ``"quarterly"``.
        curr_date: If provided, only statements on or before this date.

    Returns:
        Formatted income statement text.
    """
    params = {"period": freq.lower()}
    data = _get_json(f"income-statement/{ticker.upper()}", params)
    if isinstance(data, str):
        return data

    if not data:
        return f"No income statement data found for {ticker}"

    data = _filter_by_date(data, curr_date)

    header = f"# Income Statement for {ticker.upper()} ({freq})\n"
    header += f"# Source: Financial Modeling Prep\n\n"
    return header + _format_financial_statement(data, "income statement")


def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """Retrieve insider trading transactions from FMP.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Formatted insider transactions text.
    """
    data = _get_json("insider-trading", {"symbol": ticker.upper()})
    if isinstance(data, str):
        return data

    if not data:
        return f"No insider transactions data found for {ticker}"

    lines = [
        f"# Insider Transactions for {ticker.upper()}",
        f"# Source: Financial Modeling Prep\n",
    ]

    for idx, txn in enumerate(data, start=1):
        insider = txn.get("reportingName", txn.get("reportingCik", "Unknown"))
        txn_type = txn.get("transactionType", "N/A")
        shares = txn.get("securitiesTransacted", "N/A")
        price = txn.get("price", "N/A")
        date = txn.get("transactionDate", "N/A")
        filing = txn.get("filingDate", "")

        lines.append(f"{idx}. {insider}")
        lines.append(f"   Type: {txn_type} | Shares: {shares} | Price: {price}")
        lines.append(f"   Transaction Date: {date}" + (f" | Filing Date: {filing}" if filing else ""))
        lines.append("")

    lines.append(f"Total transactions: {len(data)}")
    return "\n".join(lines)
