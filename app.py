import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from utils.scheduler import scheduler
from utils.social_crawler import crawl_social_data
from analyzer import analyze_data
from utils.notifier import send_daily_summary
import config

app = Flask(__name__)

# 直接启动 APScheduler，不再调用 init_app()
scheduler.start()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        # TODO: Handle LINE webhook events here
        pass
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@app.route("/healthz", methods=['GET'])
def health_check():
    return 'OK'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
