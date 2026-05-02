import os
from typing import Annotated
from datetime import datetime

import requests


# Mapping from human-readable filter keys to Finviz filter parameters
FILTER_MAP = {
    # Sector
    "sector:technology": "sec_technology",
    "sector:healthcare": "sec_healthcare",
    "sector:financial": "sec_financial",
    "sector:energy": "sec_energy",
    "sector:consumer_cyclical": "sec_consumercyclical",
    "sector:consumer_defensive": "sec_consumerdefensive",
    "sector:industrials": "sec_industrials",
    "sector:utilities": "sec_utilities",
    "sector:realestate": "sec_realestate",
    "sector:basicmaterials": "sec_basicmaterials",
    "sector:communicationservices": "sec_communicationservices",
    # Market cap
    "marketcap:mega": "cap_mega",
    "marketcap:large": "cap_large",
    "marketcap:mid": "cap_mid",
    "marketcap:small": "cap_small",
    "marketcap:micro": "cap_micro",
    "marketcap:nano": "cap_nano",
    # Signal
    "signal:topgainers": "ta_topgainers",
    "signal:toplosers": "ta_toplosers",
    "signal:newhigh": "ta_newhigh",
    "signal:newlow": "ta_newlow",
    "signal:mostvolatile": "ta_mostvolatile",
    "signal:mostactive": "ta_mostactive",
    "signal:unusualvolume": "ta_unusualvolume",
    "signal:overbought": "ta_overbought",
    "signal:oversold": "ta_oversold",
    "signal:upgrades": "n_upgrades",
    "signal:downgrades": "n_downgrades",
    "signal:earningsbefore": "n_earningsbefore",
    "signal:earningsafter": "n_earningsafter",
}


def _try_finvizfinance(filters: dict) -> str | None:
    """Try using the finvizfinance package. Returns formatted string or None if unavailable."""
    try:
        from finvizfinance.screener.overview import Overview
    except ImportError:
        return None

    try:
        foverview = Overview()
        filter_dict = {}
        signal = None

        for key, value in filters.items():
            key_lower = key.lower()
            if key_lower == "sector":
                filter_dict["Sector"] = value.replace("_", " ").title()
            elif key_lower == "marketcap":
                cap_map = {
                    "mega": "Mega ($200bln and more)",
                    "large": "Large ($10bln to $200bln)",
                    "mid": "Mid ($2bln to $10bln)",
                    "small": "Small ($300mln to $2bln)",
                    "micro": "Micro ($50mln to $300mln)",
                    "nano": "Nano (under $50mln)",
                }
                cap_val = cap_map.get(value.lower())
                if cap_val:
                    filter_dict["Market Cap."] = cap_val
            elif key_lower == "signal":
                signal_map = {
                    "topgainers": "Top Gainers",
                    "toplosers": "Top Losers",
                    "newhigh": "New High",
                    "newlow": "New Low",
                    "mostvolatile": "Most Volatile",
                    "mostactive": "Most Active",
                    "unusualvolume": "Unusual Volume",
                    "overbought": "Overbought",
                    "oversold": "Oversold",
                }
                signal = signal_map.get(value.lower())

        if filter_dict:
            foverview.set_filter(filters_dict=filter_dict)
        if signal:
            foverview.set_filter(signal=signal)

        df = foverview.screener_view()
        if df is None or df.empty:
            return "No results found for the given filters."

        # Limit results
        df = df.head(25)

        # Select relevant columns (they may vary by finvizfinance version)
        desired_cols = ["Ticker", "Price", "Change", "Volume", "Market Cap", "P/E", "Sector"]
        available_cols = [c for c in desired_cols if c in df.columns]
        if not available_cols:
            available_cols = list(df.columns)[:7]

        return _format_dataframe(df[available_cols])

    except Exception as e:
        return f"Error using finvizfinance: {str(e)}"


def _try_requests_scrape(filters: dict) -> str:
    """Fall back to scraping Finviz via requests."""
    api_key = os.environ.get("FINVIZ_API_KEY")

    # Build filter string for Finviz URL
    filter_tokens = []
    signal_token = None
    for key, value in filters.items():
        lookup = f"{key.lower()}:{value.lower()}"
        mapped = FILTER_MAP.get(lookup)
        if mapped:
            if mapped.startswith("ta_") or mapped.startswith("n_"):
                signal_token = mapped
            else:
                filter_tokens.append(mapped)

    filter_str = ",".join(filter_tokens) if filter_tokens else ""

    if api_key:
        # Elite API endpoint
        base_url = "https://elite.finviz.com/screener.ashx"
    else:
        base_url = "https://finviz.com/screener.ashx"

    params = {"v": "111"}  # overview view
    if filter_str:
        params["f"] = filter_str
    if signal_token:
        params["s"] = signal_token

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.get(base_url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data: HTTP {e.response.status_code}"
    except Exception as e:
        return f"Error fetching data: {str(e)}"

    return _parse_screener_html(html)


def _parse_screener_html(html: str) -> str:
    """Parse Finviz screener HTML to extract table data."""
    # Look for the screener results table
    # Finviz uses a table with class "screener-body-table-nw" or similar
    rows = []

    try:
        # Simple HTML parsing without BeautifulSoup dependency
        # Find table rows that contain ticker data
        import re

        # Extract table data - look for the results table
        # Finviz tickers appear in links like <a href="quote.ashx?t=AAPL" ...>AAPL</a>
        ticker_pattern = re.compile(
            r'<a[^>]+href="quote\.ashx\?t=([A-Z.]+)"[^>]*>\1</a>'
        )
        tickers_found = ticker_pattern.findall(html)

        if not tickers_found:
            return "No screener results could be parsed. The page may require authentication or the format has changed."

        # Try to extract table rows more carefully
        # Look for the screener table rows
        row_pattern = re.compile(
            r'<tr[^>]*>\s*<td[^>]*>\s*\d+\s*</td>(.*?)</tr>', re.DOTALL
        )
        cell_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL)
        link_text_pattern = re.compile(r'<a[^>]*>([^<]*)</a>')

        table_rows = row_pattern.findall(html)

        header = f"{'Ticker':<8} {'Price':>8} {'Change':>8} {'Volume':>12} {'Mkt Cap':>10} {'P/E':>8} {'Sector':<20}"
        lines = [header, "-" * 78]

        for row_html in table_rows[:25]:
            cells = cell_pattern.findall(row_html)
            # Clean cell content
            clean_cells = []
            for cell in cells:
                # Extract text from links if present
                link_match = link_text_pattern.search(cell)
                if link_match:
                    clean_cells.append(link_match.group(1).strip())
                else:
                    # Remove HTML tags
                    clean_text = re.sub(r'<[^>]+>', '', cell).strip()
                    clean_cells.append(clean_text)

            if len(clean_cells) >= 10:
                # Standard Finviz overview columns:
                # 0=No, 1=Ticker, 2=Company, 3=Sector, 4=Industry, 5=Country,
                # 6=Market Cap, 7=P/E, 8=Price, 9=Change, 10=Volume
                ticker = clean_cells[1] if len(clean_cells) > 1 else "N/A"
                sector = clean_cells[3] if len(clean_cells) > 3 else "N/A"
                mkt_cap = clean_cells[6] if len(clean_cells) > 6 else "N/A"
                pe = clean_cells[7] if len(clean_cells) > 7 else "N/A"
                price = clean_cells[8] if len(clean_cells) > 8 else "N/A"
                change = clean_cells[9] if len(clean_cells) > 9 else "N/A"
                volume = clean_cells[10] if len(clean_cells) > 10 else "N/A"

                if len(sector) > 19:
                    sector = sector[:17] + ".."

                lines.append(
                    f"{ticker:<8} {price:>8} {change:>8} {volume:>12} {mkt_cap:>10} {pe:>8} {sector:<20}"
                )

        if len(lines) <= 2:
            # Fallback: just list the tickers found
            lines = [f"Found {len(tickers_found)} tickers (detailed parsing unavailable):"]
            lines.append(", ".join(tickers_found[:50]))

        return "\n".join(lines)

    except Exception as e:
        if tickers_found:
            return f"Found {len(tickers_found)} tickers (parsing error: {e}):\n" + ", ".join(tickers_found[:50])
        return f"Error parsing screener results: {str(e)}"


def _format_dataframe(df) -> str:
    """Format a pandas DataFrame as an aligned text table."""
    lines = []

    # Header
    header_parts = []
    col_widths = {}
    for col in df.columns:
        width = max(len(str(col)), df[col].astype(str).str.len().max(), 6)
        width = min(width, 20)  # cap column width
        col_widths[col] = width
        header_parts.append(str(col).ljust(width))

    lines.append("  ".join(header_parts))
    lines.append("-" * len(lines[0]))

    # Rows
    for _, row in df.iterrows():
        row_parts = []
        for col in df.columns:
            val = str(row[col]) if row[col] is not None else "N/A"
            if len(val) > col_widths[col]:
                val = val[: col_widths[col] - 2] + ".."
            row_parts.append(val.ljust(col_widths[col]))
        lines.append("  ".join(row_parts))

    return "\n".join(lines)


def get_screener_results(
    query: Annotated[
        str,
        "screener filter query, e.g. 'sector:technology marketcap:mega signal:topgainers'",
    ],
) -> str:
    """Run a Finviz stock screener query and return matching tickers with key stats."""

    # Parse query string into filter key:value pairs
    filters = {}
    for token in query.strip().split():
        if ":" in token:
            key, value = token.split(":", 1)
            filters[key.strip()] = value.strip()
        else:
            # Treat bare tokens as signal filters
            filters["signal"] = token.strip()

    if not filters:
        return "Error: No valid filters provided. Use format like 'sector:technology marketcap:mega signal:topgainers'"

    lines = [
        f"# Finviz Screener Results",
        f"# Query: {query}",
        f"# Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # Try finvizfinance package first
    result = _try_finvizfinance(filters)
    if result is not None:
        lines.append(result)
        return "\n".join(lines)

    # Fall back to requests-based scraping
    result = _try_requests_scrape(filters)
    lines.append(result)

    return "\n".join(lines)
