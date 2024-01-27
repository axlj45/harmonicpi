from ib_insync import IB, util, Future

ib = IB()
ib.connect('localhost', 7496, clientId=6)

es = Future(symbol='ES')
contract_details = ib.reqContractDetails(es)
expirations = [cd.contract.lastTradeDateOrContractMonth for cd in contract_details]
exchanges = set(cd.contract.exchange for cd in contract_details)

print(expirations)
print(exchanges)

es = Future(symbol='ES', exchange='CME', currency='USD', lastTradeDateOrContractMonth='20240315')

bars = ib.reqHistoricalData(
    es,
    endDateTime='',
    durationStr='1 Y',
    barSizeSetting='15 mins',
    whatToShow='TRADES',
    useRTH=True,
    formatDate=1
)

df = util.df(bars).to_csv("es_raw.csv")

print(df)

ib.disconnect()

# 1 secs, 5 secs, 10 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 10 mins, 15 mins, 20 mins, 30 mins, 1 hour, 2 hours, 3 hours, 4 hours, 8 hours, 1 day, 1W, 1M,