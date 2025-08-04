from flask import Flask, request, abort
from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import datetime, os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot v2 running with push scheduler."

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
    user_msg = event.message.text.strip()

    if user_msg.lower() == "/test":
        reply = "✅ 測試成功：/test"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    if user_msg.lower() == "/start":
        reply = TextSendMessage(
            text="請選擇功能：",
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="市場摘要", text="市場摘要")),
                QuickReplyButton(action=MessageAction(label="佩羅西", text="佩羅西")),
                QuickReplyButton(action=MessageAction(label="便宜股推薦", text="便宜股推薦")),
                QuickReplyButton(action=MessageAction(label="查詢個股", text="Pltr"))
            ])
        )
        line_bot_api.reply_message(event.reply_token, reply)
        return

    if "市場摘要" in user_msg:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="📰 今日市場摘要建構中..."))
        return

    if "佩羅西" in user_msg:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="👩‍🦳 佩羅西持股建構中..."))
        return

    if user_msg.lower() in ["pltr", "nvda", "aapl", "tsla", "msft"]:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"📈 查詢：{user_msg} 中，功能建構中..."))
        return

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🔍 你說的是：{user_msg}"))

# === 自動推播任務：每日中午 12 點推送市場摘要 ===
def send_daily_summary():
    try:
        message = f"📊 每日市場摘要
目前建構中（{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}）"
        line_bot_api.push_message(USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print("推播錯誤：", str(e))

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_summary, 'cron', hour=12, minute=0)
scheduler.start()

if __name__ == "__main__":
    app.run()

