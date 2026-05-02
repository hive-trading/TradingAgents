"""Finnhub-based news data fetching functions.

Drop-in alternative to yfinance/alpha_vantage for the ``news_data`` category.
Requires the ``finnhub-python`` package and the ``FINNHUB_API_KEY`` env var.
"""

import os
from datetime import datetime, timedelta
from typing import Annotated


def _get_client():
    """Return a configured finnhub client, or *None* when the key is missing."""
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        return None
    import finnhub
    return finnhub.Client(api_key=api_key)


def _format_ts(unix_ts: int) -> str:
    """Convert a UNIX timestamp to a readable datetime string."""
    try:
        return datetime.utcfromtimestamp(unix_ts).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, ValueError, TypeError):
        return "N/A"


def get_news(
    ticker: Annotated[str, "ticker symbol"],
    start_date: Annotated[str, "Start date YYYY-MM-DD"],
    end_date: Annotated[str, "End date YYYY-MM-DD"],
) -> str:
    """Retrieve company-specific news from Finnhub.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        Formatted string containing news articles for the LLM to read.
    """
    client = _get_client()
    if client is None:
        return "Error: FINNHUB_API_KEY not set"

    try:
        articles = client.company_news(ticker.upper(), _from=start_date, to=end_date)
    except Exception as e:
        return f"Error fetching data: {e}"

    if not articles:
        return f"No news found for {ticker} between {start_date} and {end_date}"

    lines = [f"## {ticker.upper()} News, from {start_date} to {end_date}\n"]

    for idx, article in enumerate(articles, start=1):
        headline = article.get("headline", "No headline")
        source = article.get("source", "Unknown")
        dt_str = _format_ts(article.get("datetime", 0))
        summary = article.get("summary", "")
        url = article.get("url", "")

        lines.append(f"{idx}. **{headline}**")
        lines.append(f"   Source: {source} | Date: {dt_str}")
        if summary:
            lines.append(f"   {summary}")
        if url:
            lines.append(f"   Link: {url}")
        lines.append("")

    lines.append(f"Total articles: {len(articles)}")
    return "\n".join(lines)


def get_global_news(
    curr_date: Annotated[str, "current date YYYY-MM-DD"],
    look_back_days: Annotated[int, "days to look back"] = 7,
    limit: Annotated[int, "max articles"] = 20,
) -> str:
    """Retrieve general market news from Finnhub.

    Args:
        curr_date: Current date in YYYY-MM-DD format.
        look_back_days: Number of days to look back.
        limit: Maximum number of articles to return.

    Returns:
        Formatted string containing global news articles for the LLM to read.
    """
    client = _get_client()
    if client is None:
        return "Error: FINNHUB_API_KEY not set"

    try:
        articles = client.general_news("general", min_id=0)
    except Exception as e:
        return f"Error fetching data: {e}"

    if not articles:
        return f"No global news found for {curr_date}"

    # Compute the date-range boundaries for filtering
    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = curr_dt - timedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    # Filter articles within the look-back window
    filtered: list[dict] = []
    for article in articles:
        ts = article.get("datetime", 0)
        try:
            article_dt = datetime.utcfromtimestamp(ts)
        except (OSError, ValueError, TypeError):
            continue
        if start_dt <= article_dt <= curr_dt + timedelta(days=1):
            filtered.append(article)
        if len(filtered) >= limit:
            break

    if not filtered:
        return f"No global news found between {start_date} and {curr_date}"

    lines = [f"## Global Market News, from {start_date} to {curr_date}\n"]

    for idx, article in enumerate(filtered, start=1):
        headline = article.get("headline", "No headline")
        source = article.get("source", "Unknown")
        dt_str = _format_ts(article.get("datetime", 0))
        summary = article.get("summary", "")
        url = article.get("url", "")

        lines.append(f"{idx}. **{headline}**")
        lines.append(f"   Source: {source} | Date: {dt_str}")
        if summary:
            lines.append(f"   {summary}")
        if url:
            lines.append(f"   Link: {url}")
        lines.append("")

    lines.append(f"Total articles: {len(filtered)}")
    return "\n".join(lines)
