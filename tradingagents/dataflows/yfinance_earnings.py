"""Yahoo Finance earnings data fetching functions.

Provides EPS revision trends and historical earnings dates via ``yfinance``.
Follows the same patterns as ``y_finance.py``.
"""

from typing import Annotated
from datetime import datetime

import yfinance as yf

from .stockstats_utils import yf_retry


def get_eps_revisions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """Retrieve EPS revision trends from Yahoo Finance.

    Shows how analyst EPS estimates have changed over recent periods
    (current, 7 days ago, 30 days ago, 60 days ago, 90 days ago).

    Args:
        ticker: Stock ticker symbol (e.g. ``"AAPL"``).

    Returns:
        Formatted EPS revisions string, or an error message.
    """
    try:
        t = yf.Ticker(ticker.upper())
        revisions = yf_retry(lambda: t.eps_revisions)
    except Exception as e:
        return f"Error fetching EPS revisions for {ticker}: {e}"

    if revisions is None or (hasattr(revisions, "empty") and revisions.empty):
        return f"No EPS revision data found for {ticker}"

    lines = [
        f"# EPS Revisions for {ticker.upper()}",
        f"# Source: Yahoo Finance\n",
    ]

    try:
        for col in revisions.columns:
            lines.append(f"--- {col} ---")
            for idx, value in revisions[col].items():
                display_val = value if value is not None else "N/A"
                lines.append(f"  {idx}: {display_val}")
            lines.append("")
    except Exception as e:
        return f"Error formatting EPS revisions for {ticker}: {e}"

    return "\n".join(lines)


def get_earnings_dates(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date YYYY-MM-DD"],
) -> str:
    """Retrieve historical earnings dates and results from Yahoo Finance.

    Shows reported EPS, estimates, and surprise percentages for earnings
    dates on or before *curr_date*.

    Args:
        ticker: Stock ticker symbol.
        curr_date: Only include earnings on or before this date.

    Returns:
        Formatted earnings dates string, or an error message.
    """
    try:
        ref = datetime.strptime(curr_date, "%Y-%m-%d")
    except ValueError:
        return f"Error: invalid date format '{curr_date}', expected YYYY-MM-DD"

    try:
        t = yf.Ticker(ticker.upper())
        dates_df = yf_retry(lambda: t.earnings_dates)
    except Exception as e:
        return f"Error fetching earnings dates for {ticker}: {e}"

    if dates_df is None or (hasattr(dates_df, "empty") and dates_df.empty):
        return f"No earnings dates data found for {ticker}"

    # Filter to dates on or before curr_date
    try:
        # The index is typically a DatetimeIndex (may be tz-aware)
        idx = dates_df.index
        if hasattr(idx, "tz") and idx.tz is not None:
            idx = idx.tz_localize(None)
        dates_df = dates_df[idx <= ref]
    except Exception:
        pass  # if filtering fails, show all data

    if dates_df.empty:
        return f"No earnings dates data found for {ticker} on or before {curr_date}"

    lines = [
        f"# Earnings Dates for {ticker.upper()}",
        f"# Source: Yahoo Finance\n",
    ]

    for dt_idx, row in dates_df.iterrows():
        # Format the date from the index
        try:
            date_str = dt_idx.strftime("%Y-%m-%d")
        except Exception:
            date_str = str(dt_idx)

        eps_est = row.get("EPS Estimate", None)
        eps_rep = row.get("Reported EPS", None)
        surprise_pct = row.get("Surprise(%)", None)

        lines.append(f"Date: {date_str}")
        lines.append(f"  EPS Estimate: {eps_est if eps_est is not None else 'N/A'}")
        lines.append(f"  Reported EPS: {eps_rep if eps_rep is not None else 'N/A'}")
        lines.append(f"  Surprise (%): {surprise_pct if surprise_pct is not None else 'N/A'}")
        lines.append("")

    lines.append(f"Total earnings dates: {len(dates_df)}")
    return "\n".join(lines)
