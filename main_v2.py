from data_service import get_ticker_df
from pattern_analysis import is_gartley, detect_structure, apply_technical_analysis
from notification_service import send_notification
from plotter_service import create_plotly
from blob_service import upload_chart
import pandas_ta
import pandas as pd
import pathlib

fuzz_factor = 5.0 / 100

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

    old_tickers = [
        "QQQ",
        "SPY",
        "MSFT",
        "SLV",
        "NVDA",
        "NUGT",
        "VLTO",
        "AMZN",
        "IAUM",
        "ESS",
    ]

    input_tickers = [
        "DDOG",
        "ANET",
        "DHR",
        "SPGI",
        "GS",
        "SPY",
        "F",
        "NOW",
        "ON",
        "TMO",
        "LRCX",
        "DXCM",
        "NEM",
        "NKE",
        "ORCL",
        "ADI",
        "INTU",
        "RCL",
        "INTC",
        "UPS",
        "CRWD",
        "CMCSA",
        "QQQ",
        "CMG",
        "ACN",
        "AMD",
        "MA",
        "V",
        "PANW",
        "AMD",
        "SLV",
        "NUGT",
        "NVDA",
    ]

    date_str = "2023-11-16 11:00:00"
    end_date = None  # pd.to_datetime(date_str)

    #  end_date = pd.Timestamp.now().ceil(yf_interval.replace("m", "T"))

    df = get_ticker_df(interval, yf_interval, tickers=input_tickers, end_date=end_date)
    apply_technical_analysis(df)

    avg_dvol = df.groupby(level=1, group_keys=False)["dollar_volume"].mean()

    filtered_tickers = avg_dvol[avg_dvol > 30]

    # Filter the original DataFrame to include only the tickers of interest
    filtered_df = df.loc[
        df.index.get_level_values("ticker").isin(filtered_tickers.index)
    ]

    for ticker in filtered_df.index.get_level_values(1).unique():
        data = filtered_df.xs(ticker, level=1).drop_duplicates()
        data = data.reset_index().rename(columns={"index": "original_index"})
        data = data[data["volume"] > 0]

        signal = data.apply(
            lambda row: detect_structure(
                data, row.name, 65, is_gartley, fuzz_factor, 0
            ),
            axis=1,
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

            result = parse_signal(latestSignal, data.iloc[-2])
            print(result)
            if result is None:
                continue

            chart_html, chart_png = create_plotly(
                data, ticker, sentiment, "Gartley", yf_interval, xabcd, result
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


def parse_signal(signal, current_candle):
    sl_pct = 0.025
    tp_pct = 0.35

    direction = signal[0]
    x = signal[1]
    a = signal[2]
    d = signal[5]

    tpv = abs((a["close"] - x["close"]) * tp_pct)

    if direction == 1:
        sl1 = current_candle.close - current_candle.close * sl_pct
        tp1 = d.close + tpv
        print("buy_signal:" + current_candle)
        if tp1 > sl1 and tp1 > current_candle.close and sl1 < current_candle.close:
            return ("BUY", current_candle.close, sl1, tp1)

    elif direction == -1:
        sl1 = current_candle.close + current_candle.close * sl_pct
        tp1 = d.close - tpv
        print("sell_signal:" + current_candle)
        if tp1 < sl1 and tp1 < current_candle.close and sl1 > current_candle.close:
            return ("SELL", current_candle.close, sl1, tp1)

    return None


for i in range(len(iterations)):
    identify_patterns(iterations[i][0], iterations[i][1], iterations[i][2])
