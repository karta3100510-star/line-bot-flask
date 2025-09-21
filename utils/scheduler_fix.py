# utils/scheduler_fix.py
import logging, os, importlib
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

TZ = os.environ.get("TZ", "Asia/Taipei")
scheduler = BackgroundScheduler(timezone=TZ)
__VERSION__ = "2025-09-22.fix1"

def job_analyze_data():
    try:
        mod = importlib.import_module("analyzer")
        fn = getattr(mod, "analyze_data")
        fn()
    except Exception as e:
        logging.exception("job_analyze_data failed: %s", e)

def job_send_daily_summary():
    try:
        mod = importlib.import_module("utils.notifier")
        fn = getattr(mod, "send_daily_summary")
        fn()
    except Exception as e:
        logging.exception("job_send_daily_summary failed: %s", e)

def register_jobs():
    if not scheduler.get_job("crawl_and_analyze"):
        scheduler.add_job(job_analyze_data, trigger="interval", hours=1,
                          id="crawl_and_analyze", replace_existing=True, coalesce=True, max_instances=1)
    if not scheduler.get_job("daily_noon_summary"):
        scheduler.add_job(job_send_daily_summary, trigger=CronTrigger(hour=12, minute=0),
                          id="daily_noon_summary", replace_existing=True, coalesce=True, max_instances=1)

def start():
    register_jobs()
    if not scheduler.running:
        scheduler.start()
        logging.info("[scheduler_fix] started TZ=%s, version=%s", TZ, __VERSION__)

def diagnostics():
    return {
        "module": __name__,
        "file": __file__,
        "version": __VERSION__,
        "tz": TZ,
    }
