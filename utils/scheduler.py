# utils/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from linebot.models import TextSendMessage
import config

def daily_market_summary(line_bot_api):
    msg = TextSendMessage(text="📊 每日市場摘要\n\n🔔 AI 與晶片為今日重點")
    line_bot_api.push_message(config.USER_ID, msg)

def setup_scheduler(line_bot_api):
    sched = BackgroundScheduler()
    # 設定每天台灣時間 12:00 執行
    sched.add_job(lambda: daily_market_summary(line_bot_api),
                  "cron", hour=12, minute=0)
    sched.start()
    return sched
