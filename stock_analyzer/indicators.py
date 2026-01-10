import pandas as pd
import numpy as np

def moving_average(series: pd.Series, window: int) -> pd.Series:
    """
    Calculates Simple Moving Average (SMA).
    """
    return series.rolling(window=window).mean()

def ema(series: pd.Series, span: int) -> pd.Series:
    """
    Calculates Exponential Moving Average (EMA).
    """
    return series.ewm(span=span, adjust=False).mean()

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    """
    Calculates MACD, Signal line, and Histogram.
    Returns: macd_line, signal_line, histogram
    """
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def rsi(series: pd.Series, period=14) -> pd.Series:
    """
    Calculates Relative Strength Index (RSI).
    """
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    ma_up = up.rolling(window=period).mean()
    ma_down = down.rolling(window=period).mean()
    
    # Handle division by zero if needed, though pandas usually handles it by returning NaN or inf
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi
