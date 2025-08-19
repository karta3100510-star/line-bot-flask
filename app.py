import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os


from utils.social_crawler import crawl_social_data
from utils.notifier import send_daily_summary
from utils.analyzer import analyze_data


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


@app.route("/healthz")
def healthz():
return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
text = event.message.text.strip()
reply = ""


if text.lower() == "/start":
reply = "歡迎使用 Tai聊天機器人\n可用指令：\n/social 抓社群\n/summary 回顧推薦\n/quote <代碼> 查股價"
elif text.lower() == "/social":
crawl_social_data()
analyze_data()
reply = send_daily_summary(dry_run=True)
elif text.lower() == "/summary":
reply = send_daily_summary(dry_run=True)
elif text.lower().startswith("/quote"):
from utils.stock import get_quote_summary
parts = text.split()
if len(parts) > 1:
reply = get_quote_summary(parts[1])
else:
reply = "請提供股票代碼，如 /quote NVDA"
else:
reply = f"You said: {text}"


line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


if __name__ == "__main__":
app.run()
