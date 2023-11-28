from scipy.signal import argrelextrema
import numpy as np
import pandas_ta


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


def apply_extrema(df, order=7, lowColumn="adj close", highColumn="adj close"):
    highs = argrelextrema(df[highColumn].values, np.greater, order=order)[0]
    lows = argrelextrema(df[lowColumn].values, np.less, order=order)[0]

    lowColumn = "adj close"
    df["pivot"] = 0  # Initialize with "no signal"

    # Assign 1 to maxima and -1 to minima
    df.loc[highs, "pivot"] = 1
    df.loc[lows, "pivot"] = -1

    return highs, lows


def detect_structure(data, candle, backcandles, harmonic_fn, window=0):
    no_result = (0, np.nan, np.nan, np.nan, np.nan, np.nan)

    if (candle <= (backcandles + window)) or (candle + window + 1 >= len(data)):
        return no_result

    localdf = data.iloc[candle - backcandles - window : candle - window]

    localdf.reset_index(drop=True, inplace=True)
    if "harmonic" not in data.columns:
        localdf["harmonic"] = 0

    localdf["ema8"] = pandas_ta.ema(localdf["adj close"], length=8)

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

    current_candle = data.iloc[candle]
    current_candle_sentiment = (
        1 if ((current_candle["adj close"] - current_candle["open"]) > 0) else -1
    )

    hm_sentiment = last_five_extrema["pivot"].sum() * -1
    ema_signal = 1 if current_candle["adj close"] > current_candle["ema"] else -1
    candle_sentiment = 1 if (D["adj close"] - D["open"]) > 0 else -1

    signal = harmonic_fn([X, A, B, C, D], 5)

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
        return (signal, X, A, B, C, D)

    return no_result
