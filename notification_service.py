from httplib2 import Http
from json import dumps

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