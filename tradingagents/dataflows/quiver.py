import os
from typing import Annotated
from datetime import datetime

import requests


QUIVER_BASE_URL = "https://api.quiverquant.com/beta"


def _get_quiver_headers() -> dict | None:
    api_key = os.environ.get("QUIVER_API_KEY")
    if not api_key:
        return None
    return {"Authorization": f"Bearer {api_key}"}


def get_congress_trades(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """Fetch recent congressional trading activity for a ticker."""
    headers = _get_quiver_headers()
    if headers is None:
        return "Error: QUIVER_API_KEY not set"

    url = f"{QUIVER_BASE_URL}/historical/congresstrading/{ticker.upper()}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data: HTTP {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"

    if not isinstance(data, list):
        data = data.get("data", []) if isinstance(data, dict) else []

    # Limit to most recent 20 entries
    data = data[:20]

    lines = [
        f"# Congressional Trading Activity: {ticker.upper()}",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Showing up to 20 most recent trades",
        "",
    ]

    if not data:
        lines.append("No congressional trading data available for this ticker.")
        return "\n".join(lines)

    lines.append(
        f"{'Representative':<25} {'Date':<12} {'Type':<8} {'Amount':<20} {'Party':<8}"
    )
    lines.append("-" * 77)

    for entry in data:
        representative = str(entry.get("Representative", entry.get("representative", "N/A")))
        if len(representative) > 24:
            representative = representative[:22] + ".."

        tx_date = str(entry.get("TransactionDate", entry.get("transaction_date", entry.get("Date", "N/A"))))
        if len(tx_date) > 10:
            tx_date = tx_date[:10]

        tx_type = str(entry.get("Transaction", entry.get("transaction", entry.get("Type", "N/A"))))
        if len(tx_type) > 7:
            tx_type = tx_type[:7]

        amount = str(entry.get("Amount", entry.get("amount", entry.get("Range", "N/A"))))
        if len(amount) > 19:
            amount = amount[:17] + ".."

        party = str(entry.get("Party", entry.get("party", "N/A")))

        lines.append(
            f"{representative:<25} {tx_date:<12} {tx_type:<8} {amount:<20} {party:<8}"
        )

    lines.append("")
    lines.append(f"Total trades shown: {len(data)}")

    return "\n".join(lines)


def get_lobbying(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """Fetch lobbying activity related to a ticker."""
    headers = _get_quiver_headers()
    if headers is None:
        return "Error: QUIVER_API_KEY not set"

    url = f"{QUIVER_BASE_URL}/historical/lobbying/{ticker.upper()}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data: HTTP {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"

    if not isinstance(data, list):
        data = data.get("data", []) if isinstance(data, dict) else []

    # Limit to most recent 20 entries
    data = data[:20]

    lines = [
        f"# Lobbying Activity: {ticker.upper()}",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Showing up to 20 most recent entries",
        "",
    ]

    if not data:
        lines.append("No lobbying data available for this ticker.")
        return "\n".join(lines)

    lines.append(
        f"{'Registrant':<30} {'Issue':<25} {'Amount':>14} {'Date':<12}"
    )
    lines.append("-" * 85)

    total_amount = 0
    for entry in data:
        registrant = str(entry.get("Registrant", entry.get("registrant", entry.get("Client", "N/A"))))
        if len(registrant) > 29:
            registrant = registrant[:27] + ".."

        issue = str(entry.get("Issue", entry.get("issue", entry.get("SpecificIssue", "N/A"))))
        if len(issue) > 24:
            issue = issue[:22] + ".."

        raw_amount = entry.get("Amount", entry.get("amount", 0))
        try:
            amount_val = float(raw_amount)
            total_amount += amount_val
            amount_str = f"${amount_val:>12,.0f}"
        except (ValueError, TypeError):
            amount_str = str(raw_amount)[:14]

        date = str(entry.get("Date", entry.get("date", entry.get("Period", "N/A"))))
        if len(date) > 10:
            date = date[:10]

        lines.append(
            f"{registrant:<30} {issue:<25} {amount_str:>14} {date:<12}"
        )

    lines.append("")
    lines.append(f"Entries shown: {len(data)}")
    if total_amount > 0:
        lines.append(f"Total lobbying amount (shown): ${total_amount:,.0f}")

    return "\n".join(lines)
