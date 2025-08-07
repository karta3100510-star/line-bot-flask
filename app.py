import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from utils.scheduler import scheduler
from utils.social_crawler import crawl_social_data
from utils.subscriber import add_subscriber
from analyzer import analyze_data
from utils.notifier import send_daily_summary
import config

app = Flask(__name__)

# 初始化 Line SDK
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

# 启动排程
scheduler.start()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    # 记录一下 body，方便调试
    print("Request body:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 注册一个简单的文字消息处理函数
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    user_id = event.source.user_id
    # 1) 自动记录为订阅者
    add_subscriber(user_id)
    incoming = event.message.text.strip()

    # 1. 社群爬取命令
    if incoming.lower() == '/social':
        results = crawl_social_data()
        if not results:
            reply = "目前尚未抓取到任何社群内容。"
        else:
            lines = [f"{r['url']} → {r['data']}" for r in results]
            # 如果结果过多，可截断或分批发送
            reply = "\n".join(lines[:10])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 其余已有逻辑——先保留回声，后续再接其它命令
    print(f"Fallback echo for: {incoming}")
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"You said: {incoming}"))

@app.route("/healthz", methods=['GET'])
def health_check():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
