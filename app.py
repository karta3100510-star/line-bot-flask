from flask import Flask, request, abort
from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import yfinance as yf

# 設定你的 LINE Bot 金鑰
LINE_CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
LINE_CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'
USER_ID = 'YOUR_USER_ID'  # 你的 LINE 使用者 ID，用於推播測試

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 主頁測試用
@app.route("/", methods=["GET"])
def index():
    return "LINE Bot 已啟動", 200

# ✅ 健康檢查用
@app.route("/healthz", methods=["GET"])
def health_check():
    return "OK", 200

# 接收 LINE 訊息
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 處理訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.lower()

    if text == "/test":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 機器人正常運作中"))
    elif text == "/start":
        quick = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="市場摘要", text="市場摘要")),
            QuickReplyButton(action=MessageAction(label="佩羅西持股", text="佩羅西持股")),
            QuickReplyButton(action=MessageAction(label="便宜股推薦", text="便宜股推薦")),
            QuickReplyButton(action=MessageAction(label="查詢個股", text="NVDA"))
        ])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請選擇快速指令：", quick_reply=quick)
        )
    elif text in ["市場摘要", "market"]:
        msg = f"""📊 每日市場摘要

🟢 道瓊指數：+0.34%
🔴 納指指數：-0.12%
🟡 費半指數：+0.25%

💬 今日主題：
機構買盤集中科技、AI晶片、再生能源，短期仍以財報與利率預期為主。

📌 熱門標的：
NVDA、TSLA、AAPL、PLTR 等。"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
    elif text in ["佩羅西持股", "pelosi"]:
        msg = """👩‍⚖️ 佩羅西持股更新：

近期持續加碼：
- NVDA (輝達)
- AAPL (蘋果)
- AMZN (亞馬遜)

觀察重點：
以長期持有、基本面穩健、AI 概念為主軸"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
    elif text in ["便宜股推薦", "低估股"]:
        msg = """📉 近期被低估且法人持續佈局的標的：

- PLTR：AI 軍工題材
- SOFI：高成長金融科技
- INTC：AI 與國防製造佈局
- BAC：大型銀行穩健轉強"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
    elif text.isalpha() and len(text) <= 5:
        stock = yf.Ticker(text.upper())
        try:
            info = stock.info
            price = info["regularMarketPrice"]
            name = info.get("shortName", text.upper())
            msg = f"📈 {name}（{text.upper()}）\n目前股價：${price}"
        except Exception:
            msg = f"⚠️ 查無 {text.upper()} 的股價資訊"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❓ 指令無法識別，請輸入 /start 查看快速選單。"))

# 每日推播任務（中午12點）
def daily_push():
    message = TextSendMessage(text="""📊 每日市場摘要

🔔 目前市場多空交錯
🟢 關注 AI 晶片與科技股走勢
🛡️ 防禦型資產穩定上漲

📌 熱門觀察：
NVDA、MSFT、AVGO、PLTR""")
    try:
        line_bot_api.push_message(USER_ID, message)
    except Exception as e:
        print("推播失敗：", e)

# 啟動排程
scheduler = BackgroundScheduler()
scheduler.add_job(daily_push, "cron", hour=12, minute=0)
scheduler.start()

# 運行應用
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))




