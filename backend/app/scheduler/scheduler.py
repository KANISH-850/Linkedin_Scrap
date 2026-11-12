"""Scheduler implementation supporting both local APScheduler and standalone hosted execution (Render Cron)."""

import asyncio
import os
import sys
from datetime import datetime
import pytz

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database.session import SessionLocal
from app.services.discovery_service import discovery_engine

logger = get_logger(__name__)


async def run_scheduled_job(trigger: str = "scheduled_cron") -> None:
    """Entry point for the daily discovery process."""
    logger.info(f"Starting scheduled discovery job. Trigger: {trigger}")
    db = SessionLocal()
    try:
        run = await discovery_engine.execute_run(db, trigger_type=trigger)
        logger.info(
            f"Scheduled discovery completed successfully. Run ID: {run.id}, Status: {run.status}, "
            f"Discovered: {run.opportunities_discovered}, New: {run.new_opportunities}, High: {run.high_match_count}"
        )
    except Exception as exc:
        logger.error(f"Scheduled discovery failed: {exc}", exc_info=True)
    finally:
        db.close()


def setup_local_apscheduler():
    """
    Sets up an in-process APScheduler strictly for local development.
    Scheduled at 9:00 AM Asia/Kolkata (IST).
    """
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    settings = get_settings()
    tz = pytz.timezone(settings.scheduler_timezone)
    scheduler = AsyncIOScheduler(timezone=tz)

    # 9:00 AM IST
    trigger = CronTrigger(hour=9, minute=0, timezone=tz)
    scheduler.add_job(
        lambda: asyncio.create_task(run_scheduled_job("local_apscheduler_9am_ist")),
        trigger=trigger,
        id="daily_discovery_9am_ist",
        name="Daily Opportunity Discovery 9 AM IST",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Local APScheduler initialized for 09:00 AM Asia/Kolkata (IST).")
    return scheduler


if __name__ == "__main__":
    # Allows Render Cron Job or external runner to execute via:
    # python -m app.scheduler.scheduler
    setup_logging("INFO")
    trigger_type = sys.argv[1] if len(sys.argv) > 1 else "render_cron"
    asyncio.run(run_scheduled_job(trigger_type))

