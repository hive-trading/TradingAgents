"""Polygon.io stock data fetching functions.

Drop-in alternative to yfinance/alpha_vantage for the ``core_stock_apis``
category.  Uses the Polygon REST API v2 via ``requests``.
Requires the ``POLYGON_API_KEY`` environment variable.
"""

import os
from datetime import datetime
from typing import Annotated

import requests


def get_stock_data(
    symbol: Annotated[str, "ticker symbol"],
    start_date: Annotated[str, "Start date YYYY-MM-DD"],
    end_date: Annotated[str, "End date YYYY-MM-DD"],
) -> str:
    """Retrieve daily OHLCV data from Polygon.io.

    Args:
        symbol: Stock ticker symbol (e.g. "AAPL").
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        CSV-like formatted string of daily price data for the LLM to read.
    """
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        return "Error: POLYGON_API_KEY not set"

    ticker = symbol.upper()
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}"
        f"/range/1/day/{start_date}/{end_date}"
    )
    params = {
        "apiKey": api_key,
        "adjusted": "true",
        "sort": "asc",
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return f"Error fetching data: {e}"

    results = data.get("results")
    if not results:
        status = data.get("status", "unknown")
        message = data.get("message", data.get("error", "no results"))
        return (
            f"No data found for symbol '{ticker}' between {start_date} and {end_date} "
            f"(status={status}, message={message})"
        )

    # Build CSV output matching the yfinance style
    header = f"# Stock data for {ticker} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(results)}\n"
    header += f"# Source: Polygon.io\n\n"

    rows = ["Date,Open,High,Low,Close,Volume"]
    for bar in results:
        # Polygon returns timestamps in milliseconds
        ts_ms = bar.get("t", 0)
        try:
            date_str = datetime.utcfromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")
        except (OSError, ValueError, TypeError):
            date_str = "N/A"

        o = round(bar.get("o", 0), 2)
        h = round(bar.get("h", 0), 2)
        l = round(bar.get("l", 0), 2)  # noqa: E741
        c = round(bar.get("c", 0), 2)
        v = bar.get("v", 0)

        rows.append(f"{date_str},{o},{h},{l},{c},{v}")

    return header + "\n".join(rows) + "\n"
