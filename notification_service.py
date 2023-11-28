from httplib2 import Http
from json import dumps
from joblib import Memory
from config import get_config

cachedir = "./yfinance_cache"
memory = Memory(cachedir, verbose=0)
cfg = get_config()


def send_chat(message):
    url = cfg["google_chat_webhook"]
    message_headers = {"Content-Type": "application/json; charset=UTF-8"}
    http_obj = Http()
    response = http_obj.request(
        uri=url,
        method="POST",
        headers=message_headers,
        body=dumps(message),
    )
    return response


@memory.cache
def send_notification(
    ticker, sentiment, pattern, interval, start, stop, chart_png_url, chart_url
):
    try:
        message = f"{sentiment} {pattern} identified for {ticker} on the {interval} chart. X: {start} D: {stop}"
        send_chat(build_message(message, chart_png_url, chart_url))
    except Exception as e:
        print(f"Failed to send google chat notification: {e}")


def build_message(message, chart_png_url, chart_url):
    if chart_png_url is None:
        return {"text": message}

    message_with_chart = {
        "cards": [
            {
                "sections": [
                    {
                        "widgets": [
                            {"textParagraph": {"text": message}},
                            {
                                "image": {
                                    "imageUrl": chart_png_url,
                                    "onClick": {"openLink": {"url": chart_url}},
                                }
                            },
                        ]
                    }
                ]
            }
        ]
    }
    
    return message_with_chart
