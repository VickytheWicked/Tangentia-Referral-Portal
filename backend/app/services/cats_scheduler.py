import asyncio
from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Dict, Optional

from app.database import SessionLocal
from app.services.cats_scraper import sync_cats_jobs_with_db

logger = logging.getLogger("referral_portal.cats_scheduler")

# Background scheduler state
_scheduler_task: Optional[asyncio.Task] = None
_last_sync_info: Dict[str, Any] = {
    "enabled": True,
    "interval_hours": 6,
    "deactivate_missing": True,
    "last_run_time": None,
    "last_run_status": "never",
    "last_run_summary": None,
    "last_error": None,
    "next_run_time": None,
}


def get_cats_scheduler_status() -> Dict[str, Any]:
    """Retrieve status of the 6-hour CATS auto-sync scheduler"""
    return dict(_last_sync_info)


def _execute_sync_worker() -> Dict[str, Any]:
    """Worker function executed in worker thread to scrape and sync jobs without blocking the event loop."""
    db = SessionLocal()
    try:
        logger.info("Executing scheduled CATS One background sync (deactivating closed positions)...")
        result = sync_cats_jobs_with_db(db, deactivate_missing=True)
        return result
    finally:
        db.close()


async def _cats_periodic_sync_loop():
    """Periodic background loop that refreshes CATS One jobs every 6 hours."""
    # Brief initial pause to let server startup and DB initialization complete
    await asyncio.sleep(10)

    interval_seconds = 6 * 3600  # 6 hours

    while True:
        start_time = datetime.now(timezone.utc)
        _last_sync_info["last_run_time"] = start_time.isoformat()
        _last_sync_info["next_run_time"] = (start_time + timedelta(seconds=interval_seconds)).isoformat()

        try:
            # Run sync in threadpool to keep FastAPI async event loop unblocked
            result = await asyncio.to_thread(_execute_sync_worker)

            _last_sync_info["last_run_status"] = "success"
            _last_sync_info["last_run_summary"] = {
                "total_scraped": result.get("total_scraped", 0),
                "created_count": result.get("created_count", 0),
                "updated_count": result.get("updated_count", 0),
                "deactivated_count": result.get("deactivated_count", 0),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            _last_sync_info["last_error"] = None
            logger.info(
                f"Automatic 6-hour CATS One sync finished successfully: "
                f"{result.get('total_scraped')} scraped, {result.get('created_count')} created, "
                f"{result.get('updated_count')} updated, {result.get('deactivated_count')} deactivated."
            )
        except asyncio.CancelledError:
            logger.info("CATS auto-sync scheduler task cancelled during shutdown.")
            break
        except Exception as ex:
            _last_sync_info["last_run_status"] = "error"
            _last_sync_info["last_error"] = str(ex)
            logger.error(f"Error during automatic CATS One sync: {ex}", exc_info=True)

        # Sleep for 6 hours until next execution
        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("CATS auto-sync scheduler task sleep cancelled.")
            break


def start_cats_scheduler():
    """Start the 6-hour background sync scheduler."""
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_cats_periodic_sync_loop())
        logger.info("Started 6-hour automatic CATS One background sync scheduler.")


def stop_cats_scheduler():
    """Cancel the background sync scheduler on application shutdown."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("Stopped 6-hour automatic CATS One background sync scheduler.")
