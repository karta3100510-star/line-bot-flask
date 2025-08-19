from apscheduler.schedulers.background import BackgroundScheduler
from utils.social_crawler import crawl_social_data

def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(crawl_social_data, 'interval', hours=1)
    scheduler.start()
