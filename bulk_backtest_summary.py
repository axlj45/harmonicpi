import pandas as pd

def produce_bt_summary(results_location: str):
    results = pd.read_csv(results_location)
    data = {}
    traded_bts = results[results['# Trades']>1]
    traded_bts = traded_bts[traded_bts['Return (Ann.) [%]'] != 0]
    data['Losing Trades'] = len(traded_bts[traded_bts["Return (Ann.) [%]"] < 0])
    data['totalTrades'] = traded_bts['# Trades'].sum()
    data['positiveTrades'] = len(traded_bts[traded_bts["Return [%]"]>0])
    data['Incomplete Trades'] = len(results[results['# Trades']==1])
    data['totalCapital'] = len(traded_bts) * 1000
    data['Return [$]'] = round(traded_bts['Equity Final [$]'].sum())
    data['Return [%]'] = round(traded_bts['Return [%]'].mean(),2)
    data['Return (Ann.) [%]'] = round(traded_bts['Return (Ann.) [%]'].mean(),2)
    data['Avg Win [%]'] = round(traded_bts["Win Rate [%]"].mean(),2)
    data['conversionRate'] = round(data['positiveTrades']/len(traded_bts),2)
    data['drawdownCorrelation'] = round(traded_bts['Return [%]'].corr(traded_bts['Win Rate [%]']),2)

    return data