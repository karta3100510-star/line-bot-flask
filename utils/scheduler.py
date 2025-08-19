from apscheduler.schedulers.background import BackgroundScheduler
from utils.social_crawler import crawl_social_data

scheduler = BackgroundScheduler()

@scheduler.scheduled_job("interval", hours=1)
def analyze_data():
    print("[排程任務] 每小時執行抓取社群資料")
    crawl_social_data()
