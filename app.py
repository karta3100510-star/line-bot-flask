from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import yfinance as yf
import os

app = Flask(__name__)

# 使用環境變數讀取 LINE 機器人金鑰
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot is running."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip().lower()

    # /test 指令
    if msg == "/test":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅ Bot 運作正常，連線成功")
        )
        return

    # /start 快捷選單
    if msg == "/start":
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="市場摘要", text="市場摘要")),
            QuickReplyButton(action=MessageAction(label="佩羅西持股", text="佩羅西")),
            QuickReplyButton(action=MessageAction(label="便宜股推薦", text="便宜股")),
            QuickReplyButton(action=MessageAction(label="查詢個股", text="查詢個股"))
        ])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請選擇功能：", quick_reply=quick_reply)
        )
        return

    # 關鍵字回應
    if "市場摘要" in msg:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="📈 今日市場摘要功能測試中，稍後將提供完整資訊。")
        )
        return

    if "佩羅西" in msg:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="👩‍⚖️ 正在查詢佩羅西近期持股紀錄...功能測試中。")
        )
        return

    if "便宜股" in msg:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="📉 正在分析低估股票推薦...功能測試中。")
        )
        return

    if "查詢個股" in msg:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請直接輸入股票代碼（如：AAPL、NVDA）")
        )
        return

    # 股票代碼查詢
    try:
        stock = yf.Ticker(msg.upper())
        info = stock.info
        price = info.get("regularMarketPrice")
        name = info.get("shortName") or info.get("longName")
        if price and name:
            summary = f"📊 {name}（{msg.upper()}）\n目前價格：${price}\n\n*更多資訊與評級分析功能將持續更新*"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=summary)
            )
            return
    except Exception as e:
        print("yfinance error:", e)

    # 預設回應（echo）
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"你說的是：{event.message.text}")
    )

if __name__ == "__main__":
    app.run()

