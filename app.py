import os
from flask import Flask, request, abort, jsonify
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from apscheduler.schedulers.background import BackgroundScheduler
from utils.social_crawler import crawl_social_data
from utils.scheduler import schedule_jobs

# --- 讀取環境變數 ---
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
USER_ID = os.getenv("USER_ID")

if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, USER_ID]):
    raise RuntimeError("請先在 .env 裡設定 LINE_CHANNEL_ACCESS_TOKEN、LINE_CHANNEL_SECRET、USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

# 健康檢查
@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200

# LINE Webhook callback
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK", 200

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text.strip().lower()
    if text == "市場摘要":
        # 這邊自己加上市場摘要的邏輯或呼叫 utils 裡的方法
        reply = "這是今天的市場摘要：…"
    else:
        reply = f"收到：{event.message.text}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    # 啟動排程任務（例如社群爬蟲、定時推播等等）
    scheduler = BackgroundScheduler()
    schedule_jobs(scheduler, line_bot_api, USER_ID)
    scheduler.start()

    # 啟動 Flask
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
