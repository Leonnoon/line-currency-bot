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
    text = event.message.text.strip()  # 去除前後空白

    # 修改點：檢查是不是純數字（或是帶小數點的數字）
    # 如果不是數字，代表群組在聊天，直接 return 裝死，不打擾大家
    try:
        amount = float(text)
    except ValueError:
        return 

    # 如果是數字，才開始抓匯率計算
    try:
        url = "https://api.exchangerate-api.com/v4/latest/TWD"
        res = requests.get(url, timeout=5)  # 加上 timeout 防止 API 卡死
        data = res.json()

        usd = amount * data["rates"]["USD"]
        jpy = amount * data["rates"]["JPY"]
        thb = amount * data["rates"]["THB"]

        reply = f"""💰 台幣 {amount:,} 元換算：

💵 USD 美元：{usd:.2f}
🇯🇵 JPY 日圓：{jpy:.2f}
🇹🇭 THB 泰銖：{thb:.2f}"""

    except Exception as e:
        reply = "目前無法取得即時匯率，請稍後再試！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


if __name__ == "__main__":
    # 修改點：這行是 Render 能成功啟動的關鍵！
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
