from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings
from app.db.session import SessionLocal
from app.services.reminders.reminder_engine import reminder_engine

scheduler = BackgroundScheduler()

def scheduled_reminder_job():
    """Periodic job executed by APScheduler."""
    print("[APScheduler] Running scheduled evidence reminder check...")
    db = SessionLocal()
    try:
        results = reminder_engine.process_reminders(db)
        print(f"[APScheduler] Check complete: {results}")
    except Exception as e:
        print(f"[APScheduler] Error executing reminder job: {e}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        interval_minutes = max(1, settings.REMINDER_INTERVAL_MINUTES)
        scheduler.add_job(
            scheduled_reminder_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="evidence_reminder_check",
            name="Periodic Evidence Reminder and Escalation Check",
            replace_existing=True
        )
        scheduler.start()
        print(f"[APScheduler] Started reminder scheduler (Interval: {interval_minutes} minutes)")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("[APScheduler] Scheduler stopped gracefully.")
