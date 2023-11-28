import pandas as pd
import pandas_ta
import warnings
from xabcd_backtest_strategy import XABCD
from backtesting import Backtest
from concurrent.futures import ProcessPoolExecutor
from data_service import get_ticker_df
from pattern_analysis import detect_structure, is_gartley
from plotter_service import create_plotly

warnings.filterwarnings("ignore")


def perform_backtest(inputs):
    ticker, df, strategy = inputs
    print(f"Backtest for {ticker} started")
    data = df.xs(ticker, level=1).drop_duplicates()
    data = data.reset_index().rename(columns={"index": "original_index"})
    data = data[data["volume"] > 0]
    data["ema"] = pandas_ta.ema(data["close"], length=8)

    signal = data.apply(
        lambda row: detect_structure(data, row.name, 65, is_gartley), axis=1
    )

    results_df = pd.DataFrame(signal.tolist(), index=data.index)
    results_df.columns = ["harmonic", "x", "a", "b", "c", "d"]
    data = pd.concat([data, results_df], axis=1)

    create_plotly(data, ticker, "Gartley", "backtest")
    print(signal.iloc[-2])

    bt_data = data.copy()
    bt_data.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        },
        inplace=True,
    )

    bt_data.set_index("date", inplace=True)
    bt_data.index = pd.to_datetime(bt_data.index, format="%d.%m.%Y %H:%M:%S.%f").floor(
        "S"
    )
    bt = Backtest(bt_data, strategy, cash=10000, margin=1 / 5)
    bt_result = bt.run()
    print(f"Backtest for {ticker} completed")
    return ticker, bt_result


if __name__ == "__main__":
    df = get_ticker_df(5, "5m", "5T", ["SPY", "AMZN"], 225)

    tickers = df.index.get_level_values(1).unique()
    tickers = [[ticker for ticker in tickers][0]]

    print(tickers)

    results = {}
    with ProcessPoolExecutor(max_workers=20) as executor:
        tasks = [[ticker, df.copy(), XABCD] for ticker in tickers]
        results_list = list(executor.map(perform_backtest, tasks))

    for result in results_list:
        results[result[0]] = result[1]

    results_df = pd.DataFrame(results).T  # Transpose to get strategies as rows
    results_df.drop(["_equity_curve", "_trades"], axis=1, inplace=True)
    results_df.to_csv("results.csv")
