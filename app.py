from flask import Flask, request, abort
import requests
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN") or "YOUR_CHANNEL_ACCESS_TOKEN"
LINE_REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
}

def handle_stock_query(text):
    if text.lower() in ["pltr", "nvda", "aapl"]:
        return f"你查詢的是：{text}\n（暫為 echo 模式，稍後回覆股價與摘要）"
    return None

def handle_market_summary():
    return "市場摘要功能建構中，將於稍後啟用。"

@app.route("/callback", methods=['POST'])
def callback():
    try:
        body = request.get_json()
        for event in body['events']:
            if event['type'] != 'message':
                continue
            reply_token = event['replyToken']
            user_msg = event['message']['text'].strip()

            if user_msg == "/test":
                reply = "✅ LINE Bot 測試成功！"
            elif user_msg == "/start":
                reply = "請選擇操作：\n1️⃣ 查詢股票（輸入代碼）\n2️⃣ 市場摘要（輸入：市場摘要）"
            elif user_msg == "市場摘要":
                reply = handle_market_summary()
            else:
                stock_response = handle_stock_query(user_msg)
                reply = stock_response or f"你說的是：{user_msg}"

            data = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": reply}]
            }
            requests.post(LINE_REPLY_ENDPOINT, headers=HEADERS, json=data)

        return 'OK'
    except Exception as e:
        print("Error:", e)
        abort(400)

if __name__ == "__main__":
    app.run()
