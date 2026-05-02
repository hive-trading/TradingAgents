import os
from typing import Annotated
from datetime import datetime

import requests


FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def _get_fred_api_key() -> str | None:
    return os.environ.get("FRED_API_KEY")


def _fetch_latest_observation(series_id: str, api_key: str, curr_date: str) -> dict | None:
    """Fetch the most recent observation for a FRED series on or before curr_date."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
        "observation_end": curr_date,
    }
    try:
        resp = requests.get(FRED_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        observations = data.get("observations", [])
        if observations:
            obs = observations[0]
            return {"date": obs["date"], "value": obs["value"]}
        return None
    except Exception as e:
        return {"error": str(e)}


def get_macro_indicators(
    curr_date: Annotated[str, "current date YYYY-MM-DD"],
) -> str:
    """Fetch key macro indicators from FRED (GDP, CPI, unemployment, fed funds, 10Y yield, VIX)."""
    api_key = _get_fred_api_key()
    if not api_key:
        return "Error: FRED_API_KEY not set"

    series = {
        "FEDFUNDS": "Fed Funds Rate",
        "DGS10": "10-Year Treasury Yield",
        "DGS2": "2-Year Treasury Yield",
        "CPIAUCSL": "CPI (All Urban Consumers)",
        "UNRATE": "Unemployment Rate",
        "GDP": "Gross Domestic Product",
        "VIXCLS": "VIX (Volatility Index)",
    }

    lines = [
        f"# Macro Economic Indicators Report",
        f"# As of: {curr_date}",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"{'Indicator':<30} {'Value':>12} {'Obs. Date':>12}",
        "-" * 58,
    ]

    for series_id, label in series.items():
        result = _fetch_latest_observation(series_id, api_key, curr_date)
        if result is None:
            lines.append(f"{label:<30} {'N/A':>12} {'N/A':>12}")
        elif "error" in result:
            lines.append(f"{label:<30} {'ERR':>12} {'':>12}  ({result['error']})")
        else:
            lines.append(f"{label:<30} {result['value']:>12} {result['date']:>12}")

    return "\n".join(lines)


def get_yield_curve(
    curr_date: Annotated[str, "current date YYYY-MM-DD"],
) -> str:
    """Fetch Treasury yield curve data (1M, 3M, 6M, 1Y, 2Y, 5Y, 10Y, 30Y) and compute spread."""
    api_key = _get_fred_api_key()
    if not api_key:
        return "Error: FRED_API_KEY not set"

    maturities = {
        "DGS1MO": "1 Month",
        "DGS3MO": "3 Month",
        "DGS6MO": "6 Month",
        "DGS1": "1 Year",
        "DGS2": "2 Year",
        "DGS5": "5 Year",
        "DGS10": "10 Year",
        "DGS30": "30 Year",
    }

    lines = [
        f"# U.S. Treasury Yield Curve",
        f"# As of: {curr_date}",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"{'Maturity':<12} {'Yield (%)':>10} {'Obs. Date':>12}",
        "-" * 38,
    ]

    yields = {}
    for series_id, label in maturities.items():
        result = _fetch_latest_observation(series_id, api_key, curr_date)
        if result is None:
            lines.append(f"{label:<12} {'N/A':>10} {'N/A':>12}")
        elif "error" in result:
            lines.append(f"{label:<12} {'ERR':>10} {'':>12}")
        else:
            lines.append(f"{label:<12} {result['value']:>10} {result['date']:>12}")
            try:
                yields[series_id] = float(result["value"])
            except (ValueError, TypeError):
                pass

    # Compute 10Y-2Y spread
    lines.append("")
    ten_y = yields.get("DGS10")
    two_y = yields.get("DGS2")
    if ten_y is not None and two_y is not None:
        spread = ten_y - two_y
        spread_str = f"{spread:+.2f}%"
        inverted_note = " ** INVERTED **" if spread < 0 else ""
        lines.append(f"10Y-2Y Spread: {spread_str}{inverted_note}")
        if spread < 0:
            lines.append(
                "Note: An inverted yield curve has historically been a leading "
                "indicator of economic recession."
            )
    else:
        lines.append("10Y-2Y Spread: Unable to compute (missing data)")

    return "\n".join(lines)
