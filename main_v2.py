from data_service import get_ticker_df
from pattern_analysis import is_gartley
from pattern_analysis import detect_structure
from notification_service import send_notification
from plotter_service import create_plotly
from blob_service import upload_chart
import pandas_ta
import pandas as pd
import pathlib

fuzz_factor = 7.0 / 100

levels = {
    1: [1, "1m", "1t"],
    2: [5, "5m", "5t"],
    3: [15, "15m", "15t"],
    4: [30, "30m", "30t"],
    5: [60, "1h", "60t"],
    6: [480, "1d", "480t"],
}

iterations = [
    [2, fuzz_factor, 3],
    [3, fuzz_factor, 5],
    [4, fuzz_factor, 7],
    [5, fuzz_factor, 10],
    [6, fuzz_factor, 10],
]


def identify_patterns(lvl, fuzz_factor, order):
    level = levels[lvl]
    interval = level[0]
    yf_interval = level[1]
    floor = level[2]

    df = get_ticker_df(
        interval,
        yf_interval,
        floor,
        ["QQQ", "SPY", "MSFT", "SLV", "NVDA", "NUGT", "VLTO", "AMZN"],
    )

    for ticker in df.index.get_level_values(1).unique():
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

        avg_vol = data.loc[:, "volume"].mean()
        if avg_vol < 100000:
            continue

        if data.iloc[-2]["harmonic"] != 0:
            latestSignal = signal.iloc[-2]
            x = latestSignal[1].date
            d = latestSignal[5].date
            xabcd = latestSignal[-5:]
            sentiment = "Bullish" if data.iloc[-2]["harmonic"] == 1 else "Bearish"
            chart_html, chart_png = create_plotly(
                data, ticker, sentiment, "Gartley", yf_interval, xabcd
            )
            chart_png_url = upload_chart(chart_png)
            chart_url = upload_chart(chart_html)
            send_notification(
                ticker,
                sentiment,
                "Gartley",
                yf_interval,
                x,
                d,
                chart_png_url,
                chart_url,
            )
            pathlib.Path.unlink(chart_html)
            pathlib.Path.unlink(chart_png)


# def signal(sentiment, signalType, signalSubType, metadata):

for i in range(len(iterations)):
    identify_patterns(iterations[i][0], iterations[i][1], iterations[i][2])
