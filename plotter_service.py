import matplotlib.pyplot as plt

def get_plot(data, minima, maxima, last_five_extrema, pattern_name, sentiment, yf_interval, ticker):

    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data['adj close'], label='Adj Close')

    # Plot highs in green and lows in red
    plt.scatter(data.iloc[maxima].index, data.iloc[maxima]['adj close'], color='green', label='Highs')
    plt.scatter(data.iloc[minima].index, data.iloc[minima]['adj close'], color='red', label='Lows')

    # Draw lines between the last 5 extrema
    for i in range(len(last_five_extrema) - 1):
        xy1 = [data.index[last_five_extrema[i]], data['adj close'][last_five_extrema[i]]]
        xy2 = [data.index[last_five_extrema[i+1]], data['adj close'][last_five_extrema[i+1]]]

        plt.plot([xy1[0], xy2[0]],
                    [xy1[1], xy2[1]],
                    color='black', linestyle='--')

    plt.title(f'{sentiment} {pattern_name} for {yf_interval} {ticker}')
    plt.xlabel('Date')
    plt.ylabel('Adjusted Close')
    plt.legend()

    start = data.index[last_five_extrema[0]].strftime("%Y%d%m-%H%M%S")
    end = data.index[last_five_extrema[-1]].strftime("%Y%d%m-%H%M%S")
    
    path = f"candidates/{ticker}_{pattern_name}_{sentiment}_{start}_{end}.png"
    print(path)
    plt.savefig(path, bbox_inches='tight')
    
    return [plt, path]