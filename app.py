from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os
from utils.scheduler import scheduler
from utils.social_crawler import crawl_social_data
from utils.notifier import send_daily_summary

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip().lower()
    if msg == "/healthz":
        reply = "LINE Bot 正常運作中"
    elif msg == "/social":
        crawl_social_data()
        reply = "已執行社群抓取分析"
    elif msg == "/summary":
        send_daily_summary()
        reply = "已發送摘要"
    else:
        reply = f"你說的是: {msg}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK"

# 啟動排程
scheduler.start()

if __name__ == "__main__":
    app.run()
