from httplib2 import Http
from json import dumps
from joblib import Memory

cachedir = './yfinance_cache'  # Choose your cache directory
memory = Memory(cachedir, verbose=0)

def send_chat(message):
    url = ""
    app_message = {"text": message}
    message_headers = {"Content-Type": "application/json; charset=UTF-8"}
    http_obj = Http()
    response = http_obj.request(
        uri=url,
        method="POST",
        headers=message_headers,
        body=dumps(app_message),
    )

@memory.cache    
def send_notification(ticker, sentiment, pattern, interval, start, stop):
    send_chat(f"{sentiment} Gartley identified on {ticker} {interval} chart. X: {start} D: {stop}")
    
    