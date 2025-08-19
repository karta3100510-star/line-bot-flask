import os
import json
import yfinance as yf
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from utils.social_crawler import crawl_social_data
from utils.analyzer import analyze_data
from utils.notifier import get_latest_summary
from utils.stock import get_stock_quote

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/")
def home():
    return "LINE Bot is running."

@app.route("/healthz")
def health_check():
    return "OK"

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
    text = event.message.text.strip().lower()
    if text == "/start":
        reply = "請輸入以下指令：\n/social 抓取社群\n/summary 推薦摘要\n/quote TICKER 查詢股價"
    elif text == "/social":
        crawl_social_data()
        analyze_data()
        reply = "社群資料抓取與分析完成。"
    elif text == "/summary":
        reply = get_latest_summary()
    elif text.startswith("/quote"):
        ticker = text.replace("/quote", "").strip().upper()
        reply = get_stock_quote(ticker)
    else:
        reply = f"You said: {event.message.text}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run()
