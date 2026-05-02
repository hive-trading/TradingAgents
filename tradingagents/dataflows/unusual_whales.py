import os
from typing import Annotated
from datetime import datetime

import requests


UW_BASE_URL = "https://api.unusualwhales.com/api"


def _get_uw_headers() -> dict | None:
    api_key = os.environ.get("UNUSUAL_WHALES_API_KEY")
    if not api_key:
        return None
    return {"Authorization": f"Bearer {api_key}"}


def get_options_flow(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """Fetch recent unusual options activity for a ticker."""
    headers = _get_uw_headers()
    if headers is None:
        return "Error: UNUSUAL_WHALES_API_KEY not set"

    url = f"{UW_BASE_URL}/stock/{ticker.upper()}/options-volume"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data: HTTP {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"

    # The response structure may vary; handle both list and dict formats
    records = data if isinstance(data, list) else data.get("data", data)

    lines = [
        f"# Options Flow Report: {ticker.upper()}",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    if isinstance(records, list) and len(records) > 0:
        total_call_vol = 0
        total_put_vol = 0
        notable_trades = []

        for entry in records:
            call_vol = _safe_int(entry.get("call_volume", 0))
            put_vol = _safe_int(entry.get("put_volume", 0))
            total_call_vol += call_vol
            total_put_vol += put_vol

            # Track entries with high volume as notable
            total_vol = call_vol + put_vol
            if total_vol > 0:
                notable_trades.append(entry)

        pc_ratio = (
            f"{total_put_vol / total_call_vol:.2f}"
            if total_call_vol > 0
            else "N/A"
        )

        lines.append(f"Total Call Volume: {total_call_vol:,}")
        lines.append(f"Total Put Volume:  {total_put_vol:,}")
        lines.append(f"Put/Call Ratio:    {pc_ratio}")
        lines.append("")

        # Show notable large trades (top 10 by volume)
        notable_trades.sort(
            key=lambda x: _safe_int(x.get("call_volume", 0)) + _safe_int(x.get("put_volume", 0)),
            reverse=True,
        )
        if notable_trades:
            lines.append("Notable Large Trades:")
            lines.append(f"{'Date':<12} {'Calls':>10} {'Puts':>10} {'Total':>10}")
            lines.append("-" * 46)
            for entry in notable_trades[:10]:
                date = entry.get("date", entry.get("timestamp", "N/A"))
                if isinstance(date, str) and len(date) > 10:
                    date = date[:10]
                cv = _safe_int(entry.get("call_volume", 0))
                pv = _safe_int(entry.get("put_volume", 0))
                lines.append(f"{str(date):<12} {cv:>10,} {pv:>10,} {cv + pv:>10,}")
    elif isinstance(records, dict):
        # Single summary response
        for key, value in records.items():
            lines.append(f"{key}: {value}")
    else:
        lines.append("No options flow data available.")

    return "\n".join(lines)


def get_dark_pool(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """Fetch recent dark pool activity for a ticker."""
    headers = _get_uw_headers()
    if headers is None:
        return "Error: UNUSUAL_WHALES_API_KEY not set"

    url = f"{UW_BASE_URL}/stock/{ticker.upper()}/dark-pool"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data: HTTP {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"

    records = data if isinstance(data, list) else data.get("data", data)

    lines = [
        f"# Dark Pool Activity Report: {ticker.upper()}",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    if isinstance(records, list) and len(records) > 0:
        total_dp_volume = 0
        total_volume = 0
        large_prints = []

        for entry in records:
            dp_vol = _safe_int(entry.get("dark_pool_volume", entry.get("volume", 0)))
            tot_vol = _safe_int(entry.get("total_volume", 0))
            total_dp_volume += dp_vol
            total_volume += tot_vol

            if dp_vol > 0:
                large_prints.append(entry)

        dp_pct = (
            f"{(total_dp_volume / total_volume) * 100:.1f}%"
            if total_volume > 0
            else "N/A"
        )

        lines.append(f"Total Dark Pool Volume: {total_dp_volume:,}")
        lines.append(f"Total Market Volume:    {total_volume:,}")
        lines.append(f"Dark Pool % of Total:   {dp_pct}")
        lines.append("")

        # Show recent large prints (top 10)
        large_prints.sort(
            key=lambda x: _safe_int(x.get("dark_pool_volume", x.get("volume", 0))),
            reverse=True,
        )
        if large_prints:
            lines.append("Recent Large Dark Pool Prints:")
            lines.append(f"{'Date':<12} {'DP Volume':>14} {'Total Vol':>14} {'DP %':>8}")
            lines.append("-" * 52)
            for entry in large_prints[:10]:
                date = entry.get("date", entry.get("timestamp", "N/A"))
                if isinstance(date, str) and len(date) > 10:
                    date = date[:10]
                dpv = _safe_int(entry.get("dark_pool_volume", entry.get("volume", 0)))
                tv = _safe_int(entry.get("total_volume", 0))
                pct = f"{(dpv / tv) * 100:.1f}%" if tv > 0 else "N/A"
                lines.append(f"{str(date):<12} {dpv:>14,} {tv:>14,} {pct:>8}")
    elif isinstance(records, dict):
        for key, value in records.items():
            lines.append(f"{key}: {value}")
    else:
        lines.append("No dark pool data available.")

    return "\n".join(lines)


def _safe_int(val) -> int:
    """Safely convert a value to int, returning 0 on failure."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
