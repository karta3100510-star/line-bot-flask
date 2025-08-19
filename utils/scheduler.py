from apscheduler.schedulers.background import BackgroundScheduler
from analyzer import analyze_data
from utils.notifier import send_daily_summary

scheduler = BackgroundScheduler()
scheduler.add_job(analyze_data, 'interval', hours=1, id='crawl_and_analyze')
scheduler.add_job(send_daily_summary, 'cron', hour=12, minute=0, id='daily_summary')
