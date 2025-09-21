# utils/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import os

TZ = os.environ.get("TZ", "Asia/Taipei")
scheduler = BackgroundScheduler(timezone=TZ)

def job_analyze_data():
    try:
        from analyzer import analyze_data
        analyze_data()
    except Exception as e:
        logging.exception("job_analyze_data failed: %s", e)

def job_send_daily_summary():
    try:
        from utils.notifier import send_daily_summary
        send_daily_summary()
    except Exception as e:
        logging.exception("job_send_daily_summary failed: %s", e)

def register_jobs():
    if not scheduler.get_job("crawl_and_analyze"):
        scheduler.add_job(
            job_analyze_data,
            trigger="interval",
            hours=1,
            id="crawl_and_analyze",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
    if not scheduler.get_job("daily_noon_summary"):
        scheduler.add_job(
            job_send_daily_summary,
            trigger=CronTrigger(hour=12, minute=0),
            id="daily_noon_summary",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

def start():
    register_jobs()
    if not scheduler.running:
        scheduler.start()
        logging.info("[scheduler] started with TZ=%s", TZ)

if os.environ.get("SCHEDULER_AUTOSTART", "1") in ("1", "true", "True"):
    try:
        start()
    except Exception as e:
        logging.exception("Failed to start scheduler: %s", e)
