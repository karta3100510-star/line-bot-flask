from apscheduler.schedulers.background import BackgroundScheduler
from utils.social_crawler import crawl_social_data
from analyzer import analyze_data
from utils.notifier import send_daily_summary

scheduler = BackgroundScheduler()

# Social crawl and data analysis every 1 hour
scheduler.add_job(analyze_data, 'interval', hours=1, id='crawl_and_analyze')

# Daily summary at 12:00
scheduler.add_job(send_daily_summary, 'cron', hour=12, minute=0, id='daily_summary')
