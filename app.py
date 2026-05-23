from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import requests
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "你的token"
CHANNEL_SECRET = "你的secret"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Error'

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text

    try:
        amount = float(text)

        url = "https://api.exchangerate-api.com/v4/latest/TWD"
        data = requests.get(url).json()

        usd = amount * data["rates"]["USD"]
        jpy = amount * data["rates"]["JPY"]
        thb = amount * data["rates"]["THB"]

        reply = f"""
{amount} TWD

USD：{usd:.2f}
JPY：{jpy:.2f}
THB：{thb:.2f}
"""

    except:
        reply = "請輸入數字，例如：1000"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


if __name__ == "__main__":
    app.run()
