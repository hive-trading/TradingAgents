from typing import Annotated
from datetime import datetime

import requests


APEWISDOM_BASE_URL = "https://apewisdom.io/api/v1.0/filter"


def get_social_mentions(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str | None, "date string (unused — data is always current)"] = None,
) -> str:
    """Fetch Reddit social mention data for a ticker from ApeWisdom.

    Searches across all-stocks (pages 1-3) and wallstreetbets for
    mention counts, upvotes, and rank changes.
    """
    ticker = ticker.upper()

    # Collect results from all-stocks pages 1-3
    all_stocks_entry = None
    for page in range(1, 4):
        url = f"{APEWISDOM_BASE_URL}/all-stocks/page/{page}"
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            return f"Error fetching data: HTTP {e.response.status_code} - {e.response.text[:200]}"
        except Exception as e:
            return f"Error fetching data: {str(e)}"

        for result in data.get("results", []):
            if result.get("ticker", "").upper() == ticker:
                all_stocks_entry = result
                break
        if all_stocks_entry is not None:
            break

    # Fetch WSB-specific data
    wsb_entry = None
    url = f"{APEWISDOM_BASE_URL}/wallstreetbets/page/1"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data: HTTP {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"

    for result in data.get("results", []):
        if result.get("ticker", "").upper() == ticker:
            wsb_entry = result
            break

    # Format output
    lines = [
        f"# Reddit Social Mentions: {ticker}",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    if all_stocks_entry is None and wsb_entry is None:
        lines.append(
            f"{ticker} was not found in the top trending stocks on Reddit "
            f"(searched all-stocks pages 1-3 and wallstreetbets)."
        )
        return "\n".join(lines)

    if all_stocks_entry is not None:
        rank = all_stocks_entry.get("rank", "N/A")
        mentions = _safe_int(all_stocks_entry.get("mentions", 0))
        upvotes = _safe_int(all_stocks_entry.get("upvotes", 0))
        rank_24h = all_stocks_entry.get("rank_24h_ago", None)
        mentions_24h = _safe_int(all_stocks_entry.get("mentions_24h_ago", 0))
        name = all_stocks_entry.get("name", ticker)

        rank_change = _format_rank_change(rank, rank_24h)
        mention_change = _format_mention_change(mentions, mentions_24h)

        lines.append(f"## All Stocks (r/stocks, r/investing, etc.)")
        lines.append(f"Name:            {name}")
        lines.append(f"Rank:            #{rank} {rank_change}")
        lines.append(f"Mentions (24h):  {mentions:,} {mention_change}")
        lines.append(f"Upvotes:         {upvotes:,}")
        lines.append("")

    if wsb_entry is not None:
        rank = wsb_entry.get("rank", "N/A")
        mentions = _safe_int(wsb_entry.get("mentions", 0))
        upvotes = _safe_int(wsb_entry.get("upvotes", 0))
        rank_24h = wsb_entry.get("rank_24h_ago", None)
        mentions_24h = _safe_int(wsb_entry.get("mentions_24h_ago", 0))

        rank_change = _format_rank_change(rank, rank_24h)
        mention_change = _format_mention_change(mentions, mentions_24h)

        lines.append(f"## WallStreetBets")
        lines.append(f"Rank:            #{rank} {rank_change}")
        lines.append(f"Mentions (24h):  {mentions:,} {mention_change}")
        lines.append(f"Upvotes:         {upvotes:,}")
    elif all_stocks_entry is not None:
        lines.append(f"{ticker} not found in top WallStreetBets mentions.")

    return "\n".join(lines)


def get_trending_stocks(
    limit: Annotated[int, "number of trending stocks to return"] = 20,
) -> str:
    """Fetch the top trending stocks on Reddit by mention count from ApeWisdom."""
    url = f"{APEWISDOM_BASE_URL}/all-stocks/page/1"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data: HTTP {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"

    results = data.get("results", [])
    if not results:
        return "No trending stock data available from ApeWisdom."

    results = results[:limit]

    lines = [
        f"# Reddit Trending Stocks (Top {len(results)})",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"{'Rank':<6} {'Ticker':<8} {'Mentions':>10} {'Upvotes':>10} {'Rank Change':>12}",
        "-" * 50,
    ]

    for entry in results:
        rank = entry.get("rank", "N/A")
        ticker = entry.get("ticker", "N/A")
        mentions = _safe_int(entry.get("mentions", 0))
        upvotes = _safe_int(entry.get("upvotes", 0))
        rank_24h = entry.get("rank_24h_ago", None)

        rank_change = _format_rank_change(rank, rank_24h)

        lines.append(
            f"#{str(rank):<5} {ticker:<8} {mentions:>10,} {upvotes:>10,} {rank_change:>12}"
        )

    return "\n".join(lines)


def _format_rank_change(current_rank, rank_24h_ago) -> str:
    """Format rank change as an arrow indicator."""
    if rank_24h_ago is None:
        return "(new)"
    try:
        current = int(current_rank)
        previous = int(rank_24h_ago)
    except (ValueError, TypeError):
        return ""
    diff = previous - current  # positive means rank improved (lower number = better)
    if diff > 0:
        return f"(+{diff})"
    elif diff < 0:
        return f"({diff})"
    return "(=)"


def _format_mention_change(current_mentions: int, mentions_24h_ago: int) -> str:
    """Format mention count change."""
    if mentions_24h_ago == 0:
        return ""
    diff = current_mentions - mentions_24h_ago
    if diff > 0:
        return f"(+{diff:,})"
    elif diff < 0:
        return f"({diff:,})"
    return "(=)"


def _safe_int(val) -> int:
    """Safely convert a value to int, returning 0 on failure."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
