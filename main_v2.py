from data_service import get_ticker_df
from pattern_analysis import apply_filters, is_gartley, detect_structure, apply_technical_analysis
from notification_service import send_notification
from plotter_service import create_plotly
from blob_service import upload_chart
import pandas as pd

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

    date_str = "2023-12-04 14:00:00"
    end_date = pd.to_datetime(date_str)
    end_date = pd.Timestamp.now().ceil('30T')

    df = get_ticker_df(interval, yf_interval, tickers=None, end_date=None)
    old_tickers = df.index.get_level_values("ticker").unique().values
    filtered_tickers = apply_filters(df, 1.25*interval)
    apply_technical_analysis(df)

    filtered_df = df.loc[
        df.index.get_level_values("ticker").isin(filtered_tickers.index)
    ]

    new_tickers = filtered_df.index.get_level_values("ticker").unique().values

    print(len(new_tickers), len(old_tickers))

    for ticker in filtered_df.index.get_level_values(1).unique():
        data = filtered_df.xs(ticker, level=1).drop_duplicates()
        data = data[data["volume"] > 0]
        data = data.iloc[-100:]
        data = data.reset_index().rename(columns={"index": "original_index"})
        
        signal = data.apply(
            lambda row: detect_structure(
                data, row.name, 65, is_gartley, fuzz_factor, 0
            ),
            axis=1,
        )

        results_df = pd.DataFrame(signal.tolist(), index=data.index)
        results_df.columns = ["harmonic", "x", "a", "b", "c", "d"]
        data = pd.concat([data, results_df], axis=1)

        latestSignal = None

        if len(data[data["harmonic"]!=0]) > 0:
            for i in range(3):
                location = 0-i
                print(f"Searching {ticker}, {yf_interval}", data.iloc[location]['harmonic'])
                if data.iloc[location]['harmonic'] != 0:
                    latestSignal = data.iloc[location]
                    break

        if latestSignal is None:
            continue

        x = latestSignal[1].date
        d = latestSignal[5].date
        xabcd = latestSignal[-5:]

        sentiment = "Bullish" if latestSignal["harmonic"] == 1 else "Bearish"

        result = parse_signal(latestSignal, latestSignal)
        
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
        # pathlib.Path.unlink(chart_html)
        # pathlib.Path.unlink(chart_png)


def parse_signal(signal, current_candle):
    sl_pct = 0.025
    tp_pct = 0.35

    direction = signal[0]
    x = signal[1]
    a = signal[2]
    d = signal[5]

    tpv = abs((a["close"] - x["close"]) * tp_pct)
    print(direction)
    if direction == 1:
        sl1 = current_candle.close - current_candle.close * sl_pct
        tp1 = d.close + tpv
        print("buy_signal:" + current_candle)
        if tp1 > sl1 and tp1 > current_candle.close and sl1 < current_candle.close:
            return ("BUY", current_candle.close, sl1, tp1)
        else:
            print ("BUY Signal dropped:\n----------\nClose: {current_candle.close}, TP: {tp1}, SL: {sl1}", {signal})

    elif direction == -1:
        sl1 = current_candle.close + current_candle.close * sl_pct
        tp1 = d.close - tpv
        print("sell_signal:" + current_candle)
        if tp1 < sl1 and tp1 < current_candle.close and sl1 > current_candle.close:
            return ("SELL", current_candle.close, sl1, tp1)
        

    return None


for i in range(len(iterations)):
    identify_patterns(iterations[i][0], iterations[i][1], iterations[i][2])
