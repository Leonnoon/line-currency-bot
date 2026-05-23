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
    # 將輸入的文字前後去空白，並將英文字母全部轉為大寫（這樣輸入 usd 或 USD 都通）
    text = event.message.text.strip().upper()

    # 拆開字串，例如 "USD 100" 會被拆成 ["USD", "100"]
    parts = text.split()
    
    # 檢查格式是不是「外幣名稱 + 數字」兩部分，如果不是，代表群組在聊天，直接裝死
    if len(parts) != 2:
        return

    currency = parts[0]  # 外幣名稱 (例如: USD)
    amount_str = parts[1] # 數字部分 (例如: 100)

    # 檢查支援的外幣，如果不符合，一樣裝死不洗版
    if currency not in ["USD", "JPY", "THB"]:
        return

    # 檢查第二個部分是不是真的數字
    try:
        amount = float(amount_str)
    except ValueError:
        return

    # 開始抓取匯率並計算
    try:
        # 這裡依然以 TWD 為基準，因為這個免費 API 用 TWD 當基準最穩定
        url = "https://api.exchangerate-api.com/v4/latest/TWD"
        res = requests.get(url, timeout=5)
        data = res.json()

        # 這裡的邏輯是反過來：台幣金額 = 外幣金額 / 該外幣對台幣的匯率
        rate = data["rates"][currency]
        twd_amount = amount / rate

        # 根據不同貨幣給予不同國旗與文字
        flag = {"USD": "💵 美元", "JPY": "🇯🇵 日圓", "THB": "🇹🇭 泰銖"}.get(currency, currency)

        reply = f"💰 匯率換算結果：\n\n{flag} {amount:,} 元\n👉 💸 折合台幣約：{twd_amount:.2f} 元"

    except Exception as e:
        reply = "目前無法取得即時匯率，請稍後再試！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )
