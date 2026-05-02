from typing import Annotated
from datetime import datetime

import requests


FINRA_ATS_URL = "https://api.finra.org/data/group/otcMarket/name/weeklySummary"

FINRA_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

WEEKLY_FIELDS = [
    "issueSymbolIdentifier",
    "totalWeeklyShareQuantity",
    "totalWeeklyTradeCount",
    "lastUpdateDate",
]


def get_dark_pool_volume(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str | None, "optional date (YYYY-MM-DD) to filter results on/before"] = None,
) -> str:
    """Fetch weekly dark pool (ATS) volume data for a ticker from FINRA.

    Returns up to 8 weeks of weekly volume and trade count data,
    sorted by most recent week first.
    """
    ticker = ticker.upper()

    payload = {
        "fields": WEEKLY_FIELDS,
        "compareFilters": [
            {
                "fieldName": "issueSymbolIdentifier",
                "fieldValue": ticker,
                "compareType": "EQUAL",
            }
        ],
        "limit": 8,
        "sortFields": ["-lastUpdateDate"],
    }

    try:
        resp = requests.post(FINRA_ATS_URL, json=payload, headers=FINRA_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data: HTTP {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"

    if not isinstance(data, list):
        data = []

    # Optionally filter to on/before curr_date
    if curr_date and data:
        data = [
            entry for entry in data
            if entry.get("lastUpdateDate", "") <= curr_date
        ]

    lines = [
        f"# FINRA Dark Pool (ATS) Volume: {ticker}",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    if not data:
        lines.append(f"No dark pool volume data available for {ticker}.")
        return "\n".join(lines)

    total_shares = 0
    total_trades = 0
    for entry in data:
        total_shares += _safe_int(entry.get("totalWeeklyShareQuantity", 0))
        total_trades += _safe_int(entry.get("totalWeeklyTradeCount", 0))

    lines.append(f"Total Shares ({len(data)} weeks):  {total_shares:,}")
    lines.append(f"Total Trades ({len(data)} weeks):  {total_trades:,}")
    lines.append("")

    lines.append("Weekly Volume Trend:")
    lines.append(f"{'Week Ending':<14} {'Shares':>16} {'Trades':>12}")
    lines.append("-" * 44)

    for entry in data:
        date = str(entry.get("lastUpdateDate", "N/A"))
        if len(date) > 10:
            date = date[:10]
        shares = _safe_int(entry.get("totalWeeklyShareQuantity", 0))
        trades = _safe_int(entry.get("totalWeeklyTradeCount", 0))
        lines.append(f"{date:<14} {shares:>16,} {trades:>12,}")

    return "\n".join(lines)


def get_dark_pool_summary(
    curr_date: Annotated[str | None, "optional date (YYYY-MM-DD) to filter results on/before"] = None,
) -> str:
    """Fetch the top 20 most-traded stocks in dark pools from FINRA ATS data.

    Returns a ranked list sorted by total weekly share quantity (descending).
    """
    payload = {
        "fields": WEEKLY_FIELDS,
        "limit": 20,
        "sortFields": ["-totalWeeklyShareQuantity"],
    }

    try:
        resp = requests.post(FINRA_ATS_URL, json=payload, headers=FINRA_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data: HTTP {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"

    if not isinstance(data, list):
        data = []

    # Optionally filter to on/before curr_date
    if curr_date and data:
        data = [
            entry for entry in data
            if entry.get("lastUpdateDate", "") <= curr_date
        ]

    lines = [
        f"# FINRA Dark Pool (ATS) Summary — Top {len(data)} by Volume",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    if not data:
        lines.append("No dark pool summary data available.")
        return "\n".join(lines)

    lines.append(
        f"{'Rank':<6} {'Ticker':<10} {'Weekly Shares':>18} {'Weekly Trades':>14} {'Week Ending':<12}"
    )
    lines.append("-" * 64)

    for idx, entry in enumerate(data, start=1):
        ticker = entry.get("issueSymbolIdentifier", "N/A")
        shares = _safe_int(entry.get("totalWeeklyShareQuantity", 0))
        trades = _safe_int(entry.get("totalWeeklyTradeCount", 0))
        date = str(entry.get("lastUpdateDate", "N/A"))
        if len(date) > 10:
            date = date[:10]

        lines.append(
            f"#{idx:<5} {ticker:<10} {shares:>18,} {trades:>14,} {date:<12}"
        )

    return "\n".join(lines)


def _safe_int(val) -> int:
    """Safely convert a value to int, returning 0 on failure."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
