import matplotlib.pyplot as plt
import plotly.graph_objects as go


def get_plot(
    data,
    minima,
    maxima,
    last_five_extrema,
    pattern_name,
    sentiment,
    yf_interval,
    ticker,
):
    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data["adj close"], label="Adj Close", color="gray")
    stacked_emas = [8, 21, 34, 55, 89]
    for i in range(len(stacked_emas)):
        length = stacked_emas[i]
        plt.plot(data.index, data[f"EMA{length}"], label=f"EMA/{length}")

    # Plot highs in green and lows in red
    plt.scatter(
        data.iloc[maxima].index,
        data.iloc[maxima]["adj close"],
        color="green",
        label="Highs",
    )
    plt.scatter(
        data.iloc[minima].index,
        data.iloc[minima]["adj close"],
        color="red",
        label="Lows",
    )

    # Draw lines between the last 5 extrema
    for i in range(len(last_five_extrema) - 1):
        xy1 = [
            data.index[last_five_extrema[i]],
            data["adj close"][last_five_extrema[i]],
        ]
        xy2 = [
            data.index[last_five_extrema[i + 1]],
            data["adj close"][last_five_extrema[i + 1]],
        ]

        plt.plot([xy1[0], xy2[0]], [xy1[1], xy2[1]], color="black", linestyle="--")

    plt.title(f"{sentiment} {pattern_name} for {yf_interval} {ticker}")
    plt.xlabel("Date")
    plt.ylabel("Adjusted Close")
    plt.legend()

    start = data.index[last_five_extrema[0]].strftime("%Y%m%d-%H%M%S")
    end = data.index[last_five_extrema[-1]].strftime("%Y%m%d-%H%M%S")

    path = f"candidates/{ticker}_{pattern_name}_{sentiment}_{yf_interval}_{start}_{end}.png"
    print(path)
    plt.savefig(path, bbox_inches="tight")

    return [plt, path]


def create_plotly(data, ticker, sentiment, pattern_name, yf_interval):
    chart_data = data.round(2)
    chart_data = chart_data.tail(100)
    hm = chart_data[chart_data["harmonic"] != 0]
    hm_bull = hm[hm["harmonic"] == 1]
    hm_bear = hm[hm["harmonic"] == -1]

    chart_data["Formatted_Date"] = chart_data["date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    hover_text = chart_data.apply(
        lambda row: f'Date: {row["Formatted_Date"]}<br>Open: {row["open"]}<br>High: {row["high"]}<br>'
        f'Low: {row["low"]}<br>Close: {row["close"]}<br>Volume: {row["volume"]}',
        axis=1,
    )

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=chart_data.index,
                open=chart_data["open"],
                high=chart_data["high"],
                low=chart_data["low"],
                close=chart_data["adj close"],
                text=hover_text,  # Set custom hover text
                hoverinfo="text",
            )
        ]
    )

    fig.add_scatter(
        x=hm_bull.index,
        y=hm_bull["low"] - (hm_bull["low"] * 0.0001),
        mode="markers",
        marker=dict(size=5, color="yellow"),
        name="Bull Signal",
    )

    fig.add_scatter(
        x=hm_bear.index,
        y=hm_bear["high"] + (hm_bear["high"] * 0.0001),
        mode="markers",
        marker=dict(size=5, color="blue"),
        name="Bear Signal",
    )

    fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data["ema"], mode="lines", name="EMA"))

    start = data["date"].min().strftime("%Y-%m-%d_%H%M%S")
    end = data["date"].max().strftime("%Y-%m-%d_%H%M%S")

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        title=f"{ticker}: {sentiment} {pattern_name} on {yf_interval} ",
    )

    path = f"candidates/{ticker}_{pattern_name}_{sentiment}_{yf_interval}_{start}_{end}"

    fig.write_html(f"{path}.html")
    fig.write_image(f"{path}.png")

    return (f"{path}.html", f"{path}.png")
