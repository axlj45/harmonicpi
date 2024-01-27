import pandas as pd
import warnings
from bulk_backtest_summary import produce_bt_summary
from xabcd_backtest_strategy import XABCD
from backtesting import Backtest
from concurrent.futures import ProcessPoolExecutor
from data_service import get_ticker_df
from pattern_analysis import detect_structure, is_gartley, apply_technical_analysis, apply_filters
from plotter_service import create_plotly

warnings.filterwarnings("ignore")


def perform_backtest(inputs):
    ticker, df, strategy, fuzz_factor = inputs
    print(f"Backtest for {ticker} started")
    data = df.xs(ticker, level=1).drop_duplicates()
    data = data[data["volume"] > 0]
    # data = data.iloc[-100:]
    data = data.reset_index().rename(columns={"index": "original_index"})
    

    signal = data.apply(
        lambda row: detect_structure(data, row.name, 65, is_gartley, fuzz_factor, 3),
        axis=1,
    )

    results_df = pd.DataFrame(signal.tolist(), index=data.index)
    results_df.columns = ["harmonic", "x", "a", "b", "c", "d"]
    data = pd.concat([data, results_df], axis=1)

    # create_plotly(data, ticker, "Gartley", "backtest")
    # print(signal.iloc[-2])

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
    bt = Backtest(bt_data, strategy, cash=1000, margin=1 / 5)
    bt_result = bt.run()
    # bt.plot()
    print(f"Backtest for {ticker} completed")
    return ticker, bt_result


if __name__ == "__main__":
    interval = 60
    date_str = "2023-11-17 14:00:00"
    end_date = pd.to_datetime(date_str)

    # end_date = pd.Timestamp.now().ceil('30T')
    df = get_ticker_df(interval, f"1h", end_date=None, tickers=None, bars=500)
    old_tickers = df.index.get_level_values("ticker").unique().values
    filtered_tickers = apply_filters(df,2*interval)
    apply_technical_analysis(df)
    # Filter the original DataFrame to include only the tickers of interest
    filtered_df = df.loc[
        df.index.get_level_values("ticker").isin(filtered_tickers.index)
    ]

    new_tickers = filtered_df.index.get_level_values("ticker").unique().values

    print(len(new_tickers), len(old_tickers))

    fuzz_factor = 5
    tickers = [ticker for ticker in new_tickers]

    results = {}
    trades = {}
    with ProcessPoolExecutor(max_workers=20) as executor:
        tasks = [[ticker, df.copy(), XABCD, fuzz_factor] for ticker in tickers]
        results_list = list(executor.map(perform_backtest, tasks))

    for result in results_list:
        results[result[0]] = result[1]
        trades[result[0]] = result[1]._trades

 

    results_df = pd.DataFrame(results).T  # Transpose to get strategies as rows
    results_df.index.names = ["ticker"]
    results_df.drop(["_equity_curve", "_trades"], axis=1, inplace=True)
    results_df.to_csv("results.csv")
    len(results_df.index)
    summary = produce_bt_summary('results.csv')
    print(summary)
