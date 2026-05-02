"""Financial Modeling Prep (FMP) earnings data fetching functions.

Provides earnings calendar, historical earnings, and earnings surprise data
via the FMP REST API v3.  Reuses helpers from the base ``fmp`` module.
Requires the ``FMP_API_KEY`` environment variable.
"""

from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta

from .fmp import _api_key, _get_json, _filter_by_date


def get_earnings_calendar(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date YYYY-MM-DD"],
) -> str:
    """Retrieve upcoming and recent earnings dates from FMP.

    Fetches the earnings calendar for a 60-day window centred on *curr_date*
    and filters to the requested ticker.

    Args:
        ticker: Stock ticker symbol (e.g. ``"AAPL"``).
        curr_date: Reference date in ``YYYY-MM-DD`` format.

    Returns:
        Formatted earnings calendar string, or an error message.
    """
    try:
        ref = datetime.strptime(curr_date, "%Y-%m-%d")
    except ValueError:
        return f"Error: invalid date format '{curr_date}', expected YYYY-MM-DD"

    from_date = (ref - relativedelta(days=30)).strftime("%Y-%m-%d")
    to_date = (ref + relativedelta(days=30)).strftime("%Y-%m-%d")

    data = _get_json("earning_calendar", {"from": from_date, "to": to_date})
    if isinstance(data, str):
        return data  # error string

    if not isinstance(data, list):
        return f"Unexpected response format for earnings calendar"

    # The endpoint returns all companies — filter to the requested ticker
    symbol = ticker.upper()
    filtered = [item for item in data if item.get("symbol", "").upper() == symbol]

    if not filtered:
        return f"No earnings calendar data found for {ticker} between {from_date} and {to_date}"

    lines = [
        f"# Earnings Calendar for {symbol}",
        f"# Window: {from_date} to {to_date}",
        f"# Source: Financial Modeling Prep\n",
    ]

    for item in filtered:
        date = item.get("date", "N/A")
        eps_est = item.get("epsEstimated", "N/A")
        eps_act = item.get("eps", "N/A")
        rev_est = item.get("revenueEstimated", "N/A")
        rev_act = item.get("revenue", "N/A")

        lines.append(f"Date: {date}")
        lines.append(f"  EPS Estimate: {eps_est}")
        lines.append(f"  EPS Actual: {eps_act}")
        lines.append(f"  Revenue Estimate: {rev_est}")
        lines.append(f"  Revenue Actual: {rev_act}")
        lines.append("")

    return "\n".join(lines)


def get_earnings_history(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date YYYY-MM-DD"],
) -> str:
    """Retrieve historical quarterly earnings for a ticker from FMP.

    Returns up to 12 quarters of earnings data on or before *curr_date*,
    including surprise percentages where estimates are available.

    Args:
        ticker: Stock ticker symbol.
        curr_date: Only include earnings on or before this date.

    Returns:
        Formatted earnings history string, or an error message.
    """
    symbol = ticker.upper()
    data = _get_json(f"historical/earning_calendar/{symbol}", {"limit": "12"})
    if isinstance(data, str):
        return data

    if not isinstance(data, list) or not data:
        return f"No earnings history data found for {ticker}"

    data = _filter_by_date(data, curr_date)

    if not data:
        return f"No earnings history data found for {ticker} on or before {curr_date}"

    lines = [
        f"# Earnings History for {symbol}",
        f"# Source: Financial Modeling Prep\n",
    ]

    for item in data:
        date = item.get("date", "N/A")
        eps_act = item.get("eps", None)
        eps_est = item.get("epsEstimated", None)
        rev_act = item.get("revenue", None)
        rev_est = item.get("revenueEstimated", None)

        lines.append(f"Date: {date}")
        lines.append(f"  EPS Actual: {eps_act if eps_act is not None else 'N/A'}")
        lines.append(f"  EPS Estimated: {eps_est if eps_est is not None else 'N/A'}")

        if eps_act is not None and eps_est is not None and eps_est != 0:
            surprise_pct = (eps_act - eps_est) / abs(eps_est) * 100
            lines.append(f"  EPS Surprise: {surprise_pct:+.2f}%")

        lines.append(f"  Revenue Actual: {rev_act if rev_act is not None else 'N/A'}")
        lines.append(f"  Revenue Estimated: {rev_est if rev_est is not None else 'N/A'}")

        if rev_act is not None and rev_est is not None and rev_est != 0:
            rev_surprise_pct = (rev_act - rev_est) / abs(rev_est) * 100
            lines.append(f"  Revenue Surprise: {rev_surprise_pct:+.2f}%")

        lines.append("")

    return "\n".join(lines)


def get_earnings_surprises(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """Retrieve earnings surprise data for a ticker from FMP.

    Shows the difference between actual and estimated EPS for recent quarters.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Formatted earnings surprises string, or an error message.
    """
    symbol = ticker.upper()
    data = _get_json(f"earnings-surprises/{symbol}")
    if isinstance(data, str):
        return data

    if not isinstance(data, list) or not data:
        return f"No earnings surprise data found for {ticker}"

    lines = [
        f"# Earnings Surprises for {symbol}",
        f"# Source: Financial Modeling Prep\n",
    ]

    for item in data:
        date = item.get("date", "N/A")
        actual = item.get("actualEarningResult", None)
        estimated = item.get("estimatedEarning", None)

        lines.append(f"Date: {date}")
        lines.append(f"  Actual EPS: {actual if actual is not None else 'N/A'}")
        lines.append(f"  Estimated EPS: {estimated if estimated is not None else 'N/A'}")

        if actual is not None and estimated is not None:
            surprise_abs = actual - estimated
            lines.append(f"  Surprise (absolute): {surprise_abs:+.4f}")
            if estimated != 0:
                surprise_pct = (actual - estimated) / abs(estimated) * 100
                lines.append(f"  Surprise (%): {surprise_pct:+.2f}%")

        lines.append("")

    lines.append(f"Total quarters: {len(data)}")
    return "\n".join(lines)
