from flask import Flask, request, abort
from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import yfinance as yf
import datetime

# 從 Render 環境變數讀取憑證與用戶 ID
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
USER_ID = os.environ.get("USER_ID")

# 初始化 Flask 與 LINE Bot
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 主頁測試
@app.route("/", methods=["GET"])
def index():
    return "LINE Bot 已啟動", 200

# Webhook 接收訊息
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.lower()

    if user_msg == "/test":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 機器人正常運作中"))
        return

    if user_msg == "/start":
        quick = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="市場摘要", text="市場摘要")),
            QuickReplyButton(action=MessageAction(label="佩羅西持股", text="佩羅西持股")),
            QuickReplyButton(action=MessageAction(label="便宜股推薦", text="便宜股推薦")),
            QuickReplyButton(action=MessageAction(label="查詢個股", text="NVDA"))
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請選擇快速指令：", quick_reply=quick))
        return

    if user_msg in ["市場摘要", "market"]:
        msg = """📊 每日市場摘要

🟢 道瓊指數：+0.34%
🔴 納指指數：-0.12%
🟡 費半指數：+0.25%

💬 今日主題：
機構買盤集中科技、AI晶片、再生能源，短期仍以財報與利率預期為主。

📌 熱門標的：
NVDA、TSLA、AAPL、PLTR 等。"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return

    if user_msg in ["佩羅西持股", "pelosi"]:
        msg = """👩‍⚖️ 佩羅西持股更新：

近期持續加碼：
- NVDA (輝達)
- AAPL (蘋果)
- AMZN (亞馬遜)

觀察重點：
以長期持有、基本面穩健、AI 概念為主軸"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return

    if user_msg in ["便宜股推薦", "低估股"]:
        msg = """📉 近期被低估且法人持續佈局的標的：

- PLTR：AI 軍工題材
- SOFI：高成長金融科技
- INTC：AI 與國防製造佈局
- BAC：大型銀行穩健轉強"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return

    if user_msg.isalpha() and len(user_msg) <= 5:
        stock = yf.Ticker(user_msg.upper())
        try:
            info = stock.info
            price = info["regularMarketPrice"]
            name = info.get("shortName", user_msg.upper())
            msg = f"📈 {name}（{user_msg.upper()}）\n目前股價：${price}"
        except Exception:
            msg = f"⚠️ 查無 {user_msg.upper()} 的股價資訊"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❓ 指令無法識別，請輸入 /start 查看快速選單。"))

# 每日中午推播市場摘要
def send_daily_summary():
    try:
        message = TextSendMessage(text=f"""📊 每日市場摘要（{datetime.datetime.now().strftime('%Y/%m/%d')}）

🔔 目前市場多空交錯
🟢 關注 AI 晶片與科技股走勢
🛡️ 防禦型資產穩定上漲

📌 熱門觀察：
NVDA、MSFT、AVGO、PLTR""")
        line_bot_api.push_message(USER_ID, message)
    except Exception as e:
        print("推播失敗：", e)

# 啟動 APScheduler 每日 12:00 自動推播
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_summary, "cron", hour=12, minute=0)
scheduler.start()

# 啟動 Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))




