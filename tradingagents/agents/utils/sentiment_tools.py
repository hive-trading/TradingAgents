from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_options_flow(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Fetch recent unusual options activity and put/call ratios.
    Uses the configured sentiment vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A formatted string containing options flow data
    """
    return route_to_vendor("get_options_flow", ticker)


@tool
def get_dark_pool(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Fetch dark pool trading activity and volume analysis.
    Uses the configured sentiment vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A formatted string containing dark pool activity data
    """
    return route_to_vendor("get_dark_pool", ticker)


@tool
def get_congress_trades(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Fetch recent congressional trading activity.
    Uses the configured sentiment vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A formatted string containing congressional trading data
    """
    return route_to_vendor("get_congress_trades", ticker)


@tool
def get_lobbying(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Fetch lobbying activity related to a company.
    Uses the configured sentiment vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A formatted string containing lobbying activity data
    """
    return route_to_vendor("get_lobbying", ticker)


@tool
def get_social_mentions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve Reddit social mention data for a ticker (WSB, r/stocks).
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: Reddit mention counts, upvotes, and rank trends
    """
    return route_to_vendor("get_social_mentions", ticker)
