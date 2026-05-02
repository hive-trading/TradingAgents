from typing import Annotated

# Import from vendor-specific modules
from .y_finance import (
    get_YFin_data_online,
    get_stock_stats_indicators_window,
    get_fundamentals as get_yfinance_fundamentals,
    get_balance_sheet as get_yfinance_balance_sheet,
    get_cashflow as get_yfinance_cashflow,
    get_income_statement as get_yfinance_income_statement,
    get_insider_transactions as get_yfinance_insider_transactions,
)
from .yfinance_news import get_news_yfinance, get_global_news_yfinance
from .alpha_vantage import (
    get_stock as get_alpha_vantage_stock,
    get_indicator as get_alpha_vantage_indicator,
    get_fundamentals as get_alpha_vantage_fundamentals,
    get_balance_sheet as get_alpha_vantage_balance_sheet,
    get_cashflow as get_alpha_vantage_cashflow,
    get_income_statement as get_alpha_vantage_income_statement,
    get_insider_transactions as get_alpha_vantage_insider_transactions,
    get_news as get_alpha_vantage_news,
    get_global_news as get_alpha_vantage_global_news,
)
from .alpha_vantage_common import AlphaVantageRateLimitError
from .finnhub_news import (
    get_news as get_finnhub_news,
    get_global_news as get_finnhub_global_news,
)
from .fmp import (
    get_fundamentals as get_fmp_fundamentals,
    get_balance_sheet as get_fmp_balance_sheet,
    get_cashflow as get_fmp_cashflow,
    get_income_statement as get_fmp_income_statement,
    get_insider_transactions as get_fmp_insider_transactions,
)
from .fmp_earnings import (
    get_earnings_calendar as get_fmp_earnings_calendar,
    get_earnings_history as get_fmp_earnings_history,
    get_earnings_surprises as get_fmp_earnings_surprises,
)
from .yfinance_earnings import (
    get_eps_revisions as get_yfinance_eps_revisions,
    get_earnings_dates as get_yfinance_earnings_dates,
)
from .polygon_stock import get_stock_data as get_polygon_stock
from .fred import get_macro_indicators as get_fred_macro, get_yield_curve as get_fred_yield_curve
from .unusual_whales import get_options_flow as get_uw_options_flow, get_dark_pool as get_uw_dark_pool
from .quiver import get_congress_trades as get_quiver_congress, get_lobbying as get_quiver_lobbying
from .apewisdom import get_social_mentions as get_apewisdom_mentions, get_trending_stocks as get_apewisdom_trending
from .finra_ats import get_dark_pool_volume as get_finra_dark_pool, get_dark_pool_summary as get_finra_dark_pool_summary
from .finviz_screener import get_screener_results as get_finviz_screener

# Configuration and routing logic
from .config import get_config

# Tools organized by category
TOOLS_CATEGORIES = {
    "core_stock_apis": {
        "description": "OHLCV stock price data",
        "tools": [
            "get_stock_data"
        ]
    },
    "technical_indicators": {
        "description": "Technical analysis indicators",
        "tools": [
            "get_indicators"
        ]
    },
    "fundamental_data": {
        "description": "Company fundamentals",
        "tools": [
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement"
        ]
    },
    "news_data": {
        "description": "News and insider data",
        "tools": [
            "get_news",
            "get_global_news",
            "get_insider_transactions",
        ]
    },
    "earnings_data": {
        "description": "Earnings calendar, history, surprises, and revision signals",
        "tools": ["get_earnings_calendar", "get_earnings_history", "get_earnings_surprises", "get_eps_revisions"]
    },
    "macro_data": {
        "description": "Macroeconomic indicators and yield curve",
        "tools": ["get_macro_indicators", "get_yield_curve"]
    },
    "sentiment_data": {
        "description": "Options flow, dark pool, congressional trades, lobbying",
        "tools": ["get_options_flow", "get_dark_pool", "get_congress_trades", "get_lobbying", "get_social_mentions"]
    },
    "screener_data": {
        "description": "Stock screener queries",
        "tools": ["get_screener_results"]
    },
}

VENDOR_LIST = [
    "yfinance",
    "alpha_vantage",
    "finnhub",
    "fmp",
    "polygon",
    "fred",
    "unusual_whales",
    "quiver",
    "apewisdom",
    "finra",
    "finviz",
]

# Mapping of methods to their vendor-specific implementations
VENDOR_METHODS = {
    # core_stock_apis
    "get_stock_data": {
        "alpha_vantage": get_alpha_vantage_stock,
        "yfinance": get_YFin_data_online,
        "polygon": get_polygon_stock,
    },
    # technical_indicators
    "get_indicators": {
        "alpha_vantage": get_alpha_vantage_indicator,
        "yfinance": get_stock_stats_indicators_window,
    },
    # fundamental_data
    "get_fundamentals": {
        "alpha_vantage": get_alpha_vantage_fundamentals,
        "yfinance": get_yfinance_fundamentals,
        "fmp": get_fmp_fundamentals,
    },
    "get_balance_sheet": {
        "alpha_vantage": get_alpha_vantage_balance_sheet,
        "yfinance": get_yfinance_balance_sheet,
        "fmp": get_fmp_balance_sheet,
    },
    "get_cashflow": {
        "alpha_vantage": get_alpha_vantage_cashflow,
        "yfinance": get_yfinance_cashflow,
        "fmp": get_fmp_cashflow,
    },
    "get_income_statement": {
        "alpha_vantage": get_alpha_vantage_income_statement,
        "yfinance": get_yfinance_income_statement,
        "fmp": get_fmp_income_statement,
    },
    # news_data
    "get_news": {
        "alpha_vantage": get_alpha_vantage_news,
        "yfinance": get_news_yfinance,
        "finnhub": get_finnhub_news,
    },
    "get_global_news": {
        "yfinance": get_global_news_yfinance,
        "alpha_vantage": get_alpha_vantage_global_news,
        "finnhub": get_finnhub_global_news,
    },
    "get_insider_transactions": {
        "alpha_vantage": get_alpha_vantage_insider_transactions,
        "yfinance": get_yfinance_insider_transactions,
        "fmp": get_fmp_insider_transactions,
    },
    # earnings_data
    "get_earnings_calendar": {
        "fmp": get_fmp_earnings_calendar,
        "yfinance": get_yfinance_earnings_dates,
    },
    "get_earnings_history": {
        "fmp": get_fmp_earnings_history,
    },
    "get_earnings_surprises": {
        "fmp": get_fmp_earnings_surprises,
    },
    "get_eps_revisions": {
        "yfinance": get_yfinance_eps_revisions,
    },
    # macro_data
    "get_macro_indicators": {
        "fred": get_fred_macro,
    },
    "get_yield_curve": {
        "fred": get_fred_yield_curve,
    },
    # sentiment_data
    "get_options_flow": {
        "unusual_whales": get_uw_options_flow,
    },
    "get_dark_pool": {
        "unusual_whales": get_uw_dark_pool,
        "finra": get_finra_dark_pool,
    },
    "get_congress_trades": {
        "quiver": get_quiver_congress,
    },
    "get_lobbying": {
        "quiver": get_quiver_lobbying,
    },
    "get_social_mentions": {
        "apewisdom": get_apewisdom_mentions,
    },
    # screener_data
    "get_screener_results": {
        "finviz": get_finviz_screener,
    },
}

def get_category_for_method(method: str) -> str:
    """Get the category that contains the specified method."""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"Method '{method}' not found in any category")

def get_vendor(category: str, method: str = None) -> str:
    """Get the configured vendor for a data category or specific tool method.
    Tool-level configuration takes precedence over category-level.
    """
    config = get_config()

    # Check tool-level configuration first (if method provided)
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # Fall back to category-level configuration
    return config.get("data_vendors", {}).get(category, "default")

def route_to_vendor(method: str, *args, **kwargs):
    """Route method calls to appropriate vendor implementation with fallback support."""
    category = get_category_for_method(method)
    vendor_config = get_vendor(category, method)
    primary_vendors = [v.strip() for v in vendor_config.split(',')]

    if method not in VENDOR_METHODS:
        raise ValueError(f"Method '{method}' not supported")

    # Build fallback chain: primary vendors first, then remaining available vendors
    all_available_vendors = list(VENDOR_METHODS[method].keys())
    fallback_vendors = primary_vendors.copy()
    for vendor in all_available_vendors:
        if vendor not in fallback_vendors:
            fallback_vendors.append(vendor)

    for vendor in fallback_vendors:
        if vendor not in VENDOR_METHODS[method]:
            continue

        vendor_impl = VENDOR_METHODS[method][vendor]
        impl_func = vendor_impl[0] if isinstance(vendor_impl, list) else vendor_impl

        try:
            return impl_func(*args, **kwargs)
        except AlphaVantageRateLimitError:
            continue  # Only rate limits trigger fallback

    raise RuntimeError(f"No available vendor for '{method}'")