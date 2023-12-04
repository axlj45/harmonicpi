from scipy.signal import argrelextrema
import numpy as np
import pandas_ta
# from zigzag import *


def find_extrema(data, order=7):
    adj_close = data["adj close"]

    maxima = argrelextrema(adj_close.values, np.greater, order=order)[0]
    minima = argrelextrema(adj_close.values, np.less, order=order)[0]
    return maxima, minima


def isPivot(data, candle, window):
    """
    function that detects if a candle is a pivot/fractal point
    args: candle index, window before and after candle to test if pivot
    returns: 1 if pivot high, 2 if pivot low, 3 if both and 0 default
    """
    idx = data.get_loc(candle)
    if idx - window < 0 or idx + window >= len(data):
        return 0

    pivotHigh = 1
    pivotLow = -1
    for i in range(candle - window, candle + window + 1):
        if data.iloc[idx].low > data.iloc[i].low:
            pivotLow = 0
        if data.iloc[idx].high < data.iloc[i].high:
            pivotHigh = 0
    if pivotHigh and pivotLow:
        return 0
    elif pivotHigh:
        return pivotHigh
    elif pivotLow:
        return pivotLow
    else:
        return 0


def is_between(needle, haystack):
    return abs(needle) > haystack[0] and abs(needle) < haystack[1]


def computer_relative_atr(stock_data):
    relative = abs(stock_data["atr"] - (stock_data["adj close"])) / stock_data["atr"]
    return relative * 1000


def compute_atr(stock_data):
    atr = pandas_ta.atr(
        high=stock_data["high"],
        low=stock_data["low"],
        close=stock_data["close"],
        length=14,
    )
    return atr


def apply_technical_analysis(df):
    # df["macd"] = df.groupby(level=1, group_keys=False)["adj close"].apply(compute_macd)
    # df["rsi"] = df.groupby(level=1)["adj close"].transform(
    #     lambda x: pandas_ta.rsi(close=x, length=20)
    # )
    stacked_emas = [8, 21, 34, 55, 89]
    for i in range(len(stacked_emas)):
        length = stacked_emas[i]
        df[f"EMA{length}"] = df.groupby(level=1)["adj close"].transform(
            lambda x: pandas_ta.ema(close=x, length=length)
        )

    df["atr"] = df.groupby(level=1, group_keys=False).apply(compute_atr)
    df["relative_atr"] = df.groupby(level=1, group_keys=False).apply(
        computer_relative_atr
    )
    df["dollar_volume"] = (df["adj close"] * df["volume"]) / 1e6
    return df


def compute_macd(close):
    macd = pandas_ta.macd(close=close, length=20).iloc[:, 0]
    return macd


def is_gartley(zigzag, fuzz_factor):
    if len(zigzag) != 5:
        return 0
    XA = zigzag[1]["adj close"] - zigzag[0]["adj close"]
    AB = zigzag[2]["adj close"] - zigzag[1]["adj close"]
    BC = zigzag[3]["adj close"] - zigzag[2]["adj close"]
    CD = zigzag[4]["adj close"] - zigzag[3]["adj close"]

    AB_range = [(0.618 - fuzz_factor) * abs(XA), (0.618 + fuzz_factor) * abs(XA)]
    BC_range = [(0.382 - fuzz_factor) * abs(AB), (0.886 + fuzz_factor) * abs(AB)]
    CD_range = [(1.27 - fuzz_factor) * abs(BC), (1.618 + fuzz_factor) * abs(BC)]

    has_structure = (
        is_between(AB, AB_range)
        and is_between(BC, BC_range)
        and is_between(CD, CD_range)
    )

    bullish = XA > 0 and AB < 0 and BC > 0 and CD < 0
    bearish = XA < 0 and AB > 0 and BC < 0 and CD > 0

    if has_structure and bullish:
        return 1
    elif has_structure and bearish:
        return -1
    else:
        return 0


def apply_extrema(df, order, lowColumn="close", highColumn="close"):
    highs = argrelextrema(df[highColumn].values, np.greater, order=order)[0]
    lows = argrelextrema(df[lowColumn].values, np.less, order=order)[0]

    df["pivot"] = 0  # Initialize with "no signal"

    # Assign 1 to maxima and -1 to minima
    df.loc[highs, "pivot"] = 1
    df.loc[lows, "pivot"] = -1

    return highs, lows


# def apply_zigzag(df, lowColumn="close", threshold=0.01, mode=0):
#     df["pivot"] = 0  # Initialize with "no signal"

#     # mode = 1 for peaks, -1 for valleys, and 0 for both
#     pivots = peak_valley_pivots(df["close"].values, threshold, -threshold)
#     df["pivot"] = pivots

#     return pivots


def detect_structure(data, candle, backcandles, harmonic_fn, fuzz_factor=5, window=0):
    no_result = (0, np.nan, np.nan, np.nan, np.nan, np.nan)

    if (candle <= (backcandles + window)) or (candle + window + 1 >= len(data)):
        return no_result

    localdf = data.iloc[candle - backcandles - window : candle - window]

    localdf.reset_index(drop=True, inplace=True)

    localdf["harmonic"] = 0

    localdf["ema_local"] = pandas_ta.ema(localdf["close"], length=21)

    # apply_zigzag(localdf)
    apply_extrema(localdf, 3)

    last_five_extrema = localdf[localdf["pivot"] != 0][-5:]

    if len(last_five_extrema) != 5:
        return no_result

    if last_five_extrema["harmonic"].sum() > 0:
        return no_result

    if abs(last_five_extrema["pivot"].sum()) != 1:
        return no_result

    X = last_five_extrema.iloc[0]
    A = last_five_extrema.iloc[1]
    B = last_five_extrema.iloc[2]
    C = last_five_extrema.iloc[3]
    D = last_five_extrema.iloc[4]

    X["hm_name"] = "X"
    A["hm_name"] = "A"
    B["hm_name"] = "B"
    C["hm_name"] = "C"
    D["hm_name"] = "D"

    current_candle = data.iloc[candle]
    current_candle_sentiment = (
        1 if ((current_candle["close"] - current_candle["open"]) > 0) else -1
    )

    pfn1 = backcandles - D.name

    # current_candle_dist = current_candle.name - D.name
    # print(len(localdf), current_candle.name, D, current_candle_dist, D['date'], current_candle['date'], pfn1, pfn2)
    if pfn1 > 2:
        return no_result

    hm_sentiment = last_five_extrema["pivot"].sum() * -1
    ema_signal = 1 if current_candle["close"] > current_candle["EMA34"] else -1
    signal = harmonic_fn([X, A, B, C, D], fuzz_factor)

    # When pivot is -1, that is a local low
    # harmonic signal = 1 is bullish
    pivot_and_signal_synced = signal + D["pivot"] == 0

    if (
        signal != 0
        and pivot_and_signal_synced
        and hm_sentiment == signal
        and ema_signal == hm_sentiment
        and current_candle_sentiment == signal
    ):
        current_candle["hm_name"] = "entry"
        current_candle["target"] = (
            current_candle["close"] - (A["close"] - X["close"]) / 3
        )
        # print(signal, X, A, B, C, D, current_candle)
        return (signal, X, A, B, C, D)

    return no_result
