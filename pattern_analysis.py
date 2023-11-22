from scipy.signal import argrelextrema
import numpy as np
import pandas_ta


def find_extrema(data, order=7):
    adj_close = data["adj close"]
    maxima = argrelextrema(adj_close.values, np.greater, order=order)[0]
    minima = argrelextrema(adj_close.values, np.less, order=order)[0]
    return maxima, minima


def is_between(needle, haystack):
    return abs(needle) > haystack[0] and abs(needle) < haystack[1]


def apply_technical_analysis(df):
    df["macd"] = df.groupby(level=1, group_keys=False)["adj close"].apply(compute_macd)
    df["rsi"] = df.groupby(level=1)["adj close"].transform(
        lambda x: pandas_ta.rsi(close=x, length=20)
    )
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
    XA = zigzag[0]
    AB = zigzag[1]
    BC = zigzag[2]
    CD = zigzag[3]

    AB_range = [(0.618 - fuzz_factor) * abs(XA), (0.618 + fuzz_factor) * abs(XA)]
    BC_range = [(0.382 - fuzz_factor) * abs(AB), (0.886 + fuzz_factor) * abs(AB)]
    CD_range = [(1.27 - fuzz_factor) * abs(BC), (1.618 + fuzz_factor) * abs(BC)]

    result = (
        is_between(AB, AB_range)
        and is_between(BC, BC_range)
        and is_between(CD, CD_range)
    )

    return result


def is_custom(zigzag, fuzz_factor):
    XA = zigzag[0]
    AB = zigzag[1]
    BC = zigzag[2]
    CD = zigzag[3]

    AB_range = [(0.618 - fuzz_factor) * abs(XA), (0.618 + fuzz_factor) * abs(XA)]
    BC_range = [(0.382 - fuzz_factor) * abs(AB), (0.886 + fuzz_factor) * abs(AB)]
    CD_range = [(1.27 - fuzz_factor) * abs(BC), (1.618 + fuzz_factor) * abs(BC)]

    result = (
        is_between(AB, AB_range)
        and is_between(BC, BC_range)
        and is_between(CD, CD_range)
    )

    return result
