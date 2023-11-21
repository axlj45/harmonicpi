from httplib2 import Http
from json import dumps

def send_chat(message):
    url = "https://chat.googleapis.com/v1/spaces/AAAAI8NwXQk/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=WC_2ErrFImw4fDFW7D9yBBVHtg81RAU4jzvNXx0g-Jw"
    app_message = {"text": message}
    message_headers = {"Content-Type": "application/json; charset=UTF-8"}
    http_obj = Http()
    response = http_obj.request(
        uri=url,
        method="POST",
        headers=message_headers,
        body=dumps(app_message),
    )