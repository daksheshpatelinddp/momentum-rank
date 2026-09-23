"""Vectorised technical indicators for backtest2.py's optional entry/exit filters.
Each function takes a DataFrame (index=date, columns=symbol) and returns one of the same shape.
"""
import numpy as np
import pandas as pd


def rsi(close, period=14):
    """Wilder's RSI. First `period` values are NaN (not enough data yet)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.where(avg_loss != 0, 100.0).where(avg_gain.notna())


def macd(close, fast=12, slow=26, signal=9):
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast = close.ewm(span=fast, min_periods=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, min_periods=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, min_periods=signal, adjust=False).mean()
    return line, sig, line - sig


def volume_surge(volume, short=20, long=100):
    """Ratio of recent average volume to a longer-run average volume."""
    s = volume.rolling(short, min_periods=max(5, short // 2)).mean()
    l = volume.rolling(long, min_periods=max(20, long // 2)).mean()
    return s / l.replace(0, np.nan)
