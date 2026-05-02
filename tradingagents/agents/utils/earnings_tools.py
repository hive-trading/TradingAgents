from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_earnings_calendar(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """
    Retrieve upcoming and recent earnings dates with EPS/revenue estimates.
    Args:
        ticker (str): Ticker symbol of the company
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing earnings calendar data
    """
    return route_to_vendor("get_earnings_calendar", ticker, curr_date)


@tool
def get_earnings_history(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """
    Retrieve historical quarterly earnings with actual vs estimated EPS and revenue.
    Args:
        ticker (str): Ticker symbol of the company
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing historical earnings data
    """
    return route_to_vendor("get_earnings_history", ticker, curr_date)


@tool
def get_earnings_surprises(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve earnings surprise data showing how much actual EPS beat or missed estimates.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A formatted report containing earnings surprise data
    """
    return route_to_vendor("get_earnings_surprises", ticker)


@tool
def get_eps_revisions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve analyst EPS revision trends (changes in estimates over 7d/30d/60d/90d).
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A formatted report containing EPS revision trends
    """
    return route_to_vendor("get_eps_revisions", ticker)
