import yfinance as yf
import pandas as pd

def get_ticker(ticker_symbol: str):
    """
    Returns a yfinance Ticker object.
    """
    return yf.Ticker(ticker_symbol)

def get_history(ticker_symbol: str, period="1y", interval="1d") -> pd.DataFrame:
    """
    Fetches historical data for a given ticker.
    Returns a DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits.
    """
    t = get_ticker(ticker_symbol)
    df = t.history(period=period, interval=interval)
    return df

def get_info(ticker_symbol: str) -> dict:
    """
    Fetches basic info for a given ticker.
    """
    t = get_ticker(ticker_symbol)
    return t.info
