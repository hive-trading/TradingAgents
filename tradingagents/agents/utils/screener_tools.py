from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_screener_results(
    query: Annotated[str, "screener filter query"],
) -> str:
    """
    Run a stock screener with filters and return matching tickers with key stats.
    Uses the configured screener vendor.
    Args:
        query (str): Screener filter query describing the criteria
    Returns:
        str: A formatted string containing matching tickers and their key statistics
    """
    return route_to_vendor("get_screener_results", query)
