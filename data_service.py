import yfinance as yf
from joblib import Memory
import pandas as pd
import numpy as np

cachedir = "./yfinance_cache"
memory = Memory(cachedir, verbose=0)


@memory.cache
def cached_yf_download(*args, **kwargs):
    return yf.download(*args, **kwargs)


@memory.cache
def cached_tickers(dt):
    sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
    sp500["Symbol"] = sp500["Symbol"].str.replace(".", "-")
    symbols_list = sp500["Symbol"].unique().tolist()

    QQQ = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100#Components")[4]
    QQQ["Ticker"] = QQQ["Ticker"].str.replace(".", "-")
    nasdaq_symbols_list = QQQ["Ticker"].unique().tolist()

    symbols_list.extend(nasdaq_symbols_list)
    symbols_list.extend(list(["SPY", "QQQ"]))
    symbols_list = list(set(symbols_list))

    return symbols_list


def get_ticker_df(interval, yf_interval, floor, bars=65):
    minsPerDay = 8 * 60
    totalMins = max(bars, 100) * interval * 1.2
    totalDays = np.ceil(totalMins / minsPerDay)
    end_date = pd.Timestamp.now().ceil(floor)

    start_date = pd.to_datetime(end_date) - pd.DateOffset(totalDays)

    symbols_list = cached_tickers("2023-11-21.0")

    df = cached_yf_download(
        tickers=symbols_list, start=start_date, end=end_date, interval=yf_interval
    ).stack()

    df.index.names = ["date", "ticker"]

    df.columns = df.columns.str.lower()

    print([interval, yf_interval, floor])

    return df
