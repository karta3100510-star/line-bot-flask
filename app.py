# app.py
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
import yfinance as yf

import config
from utils.scheduler import setup_scheduler
from utils.social_crawler import fetch_social_metrics

app = Flask(__name__)

# LINE API
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler      = WebhookHandler(config.LINE_CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def index():
    return "LINE Bot 已啟動", 200

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body      = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip().lower()

    if text == "/test":
        reply = "✅ 機器人正常運作中"
    elif text == "/start":
        quick = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="市場摘要", text="市場摘要")),
            QuickReplyButton(action=MessageAction(label="社群數據", text="社群數據")),
            QuickReplyButton(action=MessageAction(label="查詢個股", text="NVDA"))
        ])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請選擇快速指令：", quick_reply=quick)
        )
        return
    elif text in ["市場摘要", "market"]:
        # 範例硬編碼摘要
        reply = (
            "📊 每日市場摘要\n\n"
            "🟢 道瓊 +0.34%\n"
            "🔴 納指 -0.12%\n"
            "🟡 費半 +0.25%\n\n"
            "📌 熱門標的：NVDA, TSLA, AAPL, PLTR"
        )
    elif text in ["社群數據"]:
        metrics = fetch_social_metrics()
        reply = f"💬 Telegram 人數：{metrics.get('telegram_count', 'N/A')}"
    elif text.isalpha() and len(text) <= 5:
        ticker = text.upper()
        try:
            stock = yf.Ticker(ticker)
            price = stock.info.get("regularMarketPrice")
            name  = stock.info.get("shortName", ticker)
            reply = f"📈 {name} ({ticker})\n目前股價：${price}"
        except Exception:
            reply = f"⚠️ 查無 {ticker} 的股價資訊"
    else:
        reply = "❓ 指令無法識別，請輸入 /start 查看快速選單。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    # 啟動排程
    sched = setup_scheduler(line_bot_api)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
