import numpy as np
from data_service import get_ticker_df
from pattern_analysis import find_extrema
from pattern_analysis import is_gartley
from pattern_analysis import apply_technical_analysis
from notification_service import send_notification
from plotter_service import get_plot
from blob_service import upload_chart

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

    df = get_ticker_df(interval, yf_interval, floor)
    
    df = apply_technical_analysis(df)

    for ticker in df.index.get_level_values(1).unique():
        data = df.xs(ticker, level=1).drop_duplicates().tail(65)
        maxima, minima = find_extrema(data, order)
        extrema_indices = np.sort(np.concatenate((maxima, minima, [len(data) - 1])))
        prices = data["adj close"].values

        avg_vol = data.loc[:, "volume"].mean()
        if avg_vol < 50000:
            continue

        # Select only the last 5 extrema points
        last_five_extrema = extrema_indices[-5:]

        if len(last_five_extrema) < 5:
            continue

        X = last_five_extrema[0]
        A = last_five_extrema[1]
        B = last_five_extrema[2]
        C = last_five_extrema[3]
        D = last_five_extrema[4]

        XA = prices[A] - prices[X]
        AB = prices[B] - prices[A]
        BC = prices[C] - prices[B]
        CD = prices[D] - prices[C]

        bullish = XA > 0 and AB < 0 and BC > 0 and CD < 0
        bearish = XA < 0 and AB > 0 and BC < 0 and CD > 0

        if not bullish and not bearish:
            continue

        zigzag = [XA, AB, BC, CD]
        sentiment = "Bullish" if bullish else "Bearish"

        if is_gartley(zigzag, fuzz_factor):
            D_data = data.index[D]
            X_data = data.index[X]
            print(D_data, X_data)
            plot_and_path = get_plot(
                data,
                minima,
                maxima,
                last_five_extrema,
                "Gartley",
                sentiment,
                yf_interval,
                ticker,
            )
            chart_path = plot_and_path[1]
            chart_url = upload_chart(chart_path)
            send_notification(
                ticker, sentiment, "Gartley", yf_interval, X_data, D_data, chart_url
            )


for i in range(len(iterations)):
    identify_patterns(iterations[i][0], iterations[i][1], iterations[i][2])
