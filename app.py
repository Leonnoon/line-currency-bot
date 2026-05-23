from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import requests
import os

app = Flask(__name__)

# 修改點：改從環境變數讀取，不要寫死在程式碼裡
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的token")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的secret")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Error', 400  # 加上錯誤狀態碼

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip().upper()
    parts = text.split()
    
    if len(parts) != 2:
        return

    currency = parts[0]
    amount_str = parts[1]

    if currency not in ["USD", "JPY", "AUD"]:
        return

    try:
        amount = float(amount_str)
    except ValueError:
        return

    try:
        url = "https://api.exchangerate-api.com/v4/latest/TWD"
        res = requests.get(url, timeout=5)
        data = res.json()

        rate = data["rates"][currency]
        twd_amount = amount / rate

        flag = {
            "USD": "💵 美元", 
            "JPY": "🇯🇵 日圓", 
            "AUD": "🇦🇺 澳幣"
        }.get(currency, currency)

        reply = f"💰 匯率換算結果：\n\n{flag} {amount:,} 元\n👉 折合台幣約：{twd_amount:.2f} 元"

    except Exception as e:
        reply = "目前無法取得即時匯率，請稍後再試！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )
