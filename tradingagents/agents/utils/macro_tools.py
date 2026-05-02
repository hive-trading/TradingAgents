from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_macro_indicators(
    curr_date: Annotated[str, "current date YYYY-MM-DD"],
) -> str:
    """
    Fetch key macro indicators (GDP, CPI, unemployment, fed funds rate, treasury yields, VIX).
    Uses the configured macro vendor.
    Args:
        curr_date (str): Current date in YYYY-MM-DD format
    Returns:
        str: A formatted string containing key macroeconomic indicators
    """
    return route_to_vendor("get_macro_indicators", curr_date)


@tool
def get_yield_curve(
    curr_date: Annotated[str, "current date YYYY-MM-DD"],
) -> str:
    """
    Fetch current Treasury yield curve and spread analysis.
    Uses the configured macro vendor.
    Args:
        curr_date (str): Current date in YYYY-MM-DD format
    Returns:
        str: A formatted string containing yield curve data and spread analysis
    """
    return route_to_vendor("get_yield_curve", curr_date)
