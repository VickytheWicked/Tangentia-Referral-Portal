import asyncio
import logging
import time
from typing import Dict, Any, Optional, Set

from app.config import settings

logger = logging.getLogger("cv_intelligence.queue")

# Singleton queue state
_queue: Optional[asyncio.Queue] = None
_queue_loop: Optional[asyncio.AbstractEventLoop] = None
_worker_task: Optional[asyncio.Task] = None
_pending_ids: Set[str] = set()

# Default delay in seconds between processing successive candidate CVs
# to respect Google Gemini API rate limits (e.g. 15 RPM free tier)
DEFAULT_RATE_LIMIT_DELAY = 4.0


def _get_queue() -> asyncio.Queue:
    global _queue, _queue_loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _queue is None or (_queue_loop is not None and current_loop is not None and _queue_loop != current_loop):
        _queue = asyncio.Queue()
        _queue_loop = current_loop
    elif _queue_loop is None and current_loop is not None:
        _queue_loop = current_loop

    return _queue


async def _cv_queue_worker_loop():
    """
    Background worker loop that processes candidate CV extraction jobs sequentially.
    Paces requests with an inter-job delay to strictly respect Gemini API rate limits.
    """
    logger.info("CV Intelligence processing queue worker loop started.")
    q = _get_queue()

    while True:
        try:
            referral_id = await q.get()
        except asyncio.CancelledError:
            logger.info("CV queue worker cancelled while waiting for jobs.")
            break

        try:
            logger.info(f"[CV Queue] Beginning automatic CV processing for referral ID: {referral_id}")

            # Check if Gemini circuit breaker is currently open
            try:
                from app.cv_intelligence.extractor import GeminiCVExtractor
                circuit_remaining = GeminiCVExtractor._circuit_open_until - time.time()
                if circuit_remaining > 0:
                    wait_time = min(circuit_remaining, 30.0)
                    logger.info(
                        f"[CV Queue] Gemini circuit breaker open ({circuit_remaining:.1f}s remaining); "
                        f"waiting {wait_time:.1f}s before processing referral {referral_id}..."
                    )
                    await asyncio.sleep(wait_time)
            except Exception as cb_err:
                logger.debug(f"[CV Queue] Circuit breaker check skipped: {cb_err}")

            # Run CV Intelligence processing with fresh DB sessions
            from app.database import SessionLocal
            from app.cv_intelligence.database import CVSessionLocal
            from app.cv_intelligence.service import CVIntelligenceService

            db = SessionLocal()
            cv_db = CVSessionLocal()
            try:
                await CVIntelligenceService.process_referral_cv(
                    db=db,
                    cv_db=cv_db,
                    referral_id=referral_id,
                    force_reprocess=False,
                )
                logger.info(f"[CV Queue] Successfully completed automatic CV processing for referral ID: {referral_id}")
            except Exception as proc_err:
                err_str = str(proc_err)
                logger.error(f"[CV Queue] Processing error on referral {referral_id}: {proc_err}", exc_info=True)

                # Rate-limit backoff handling for HTTP 429 / ResourceExhausted
                if "429" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower():
                    logger.warning("[CV Queue] Gemini rate limit detected (429/ResourceExhausted). Backing off for 20 seconds...")
                    await asyncio.sleep(20.0)
            finally:
                db.close()
                cv_db.close()

        except asyncio.CancelledError:
            logger.info("CV queue worker cancelled during processing.")
            _pending_ids.discard(referral_id)
            q.task_done()
            break
        except Exception as unhandled_err:
            logger.error(f"[CV Queue] Unexpected error processing referral {referral_id}: {unhandled_err}", exc_info=True)
        finally:
            _pending_ids.discard(referral_id)
            q.task_done()

        # Enforce rate-limiting delay before pulling the next candidate from queue
        try:
            await asyncio.sleep(DEFAULT_RATE_LIMIT_DELAY)
        except asyncio.CancelledError:
            logger.info("CV queue worker cancelled during rate-limit delay.")
            break


def start_cv_queue_worker():
    """
    Start the background queue worker task if not already running.
    """
    global _worker_task
    if not settings.CV_INTELLIGENCE_ENABLED:
        logger.info("CV Intelligence feature flag disabled; queue worker not started.")
        return

    if _worker_task is None or _worker_task.done():
        try:
            loop = asyncio.get_running_loop()
            _worker_task = loop.create_task(_cv_queue_worker_loop())
            logger.info("Started automatic background CV Intelligence queue worker.")
        except RuntimeError:
            logger.warning("No running asyncio event loop found to start CV queue worker.")


def stop_cv_queue_worker():
    """
    Cancel the background queue worker on application shutdown.
    """
    global _worker_task
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        logger.info("Stopped CV Intelligence queue worker.")


def enqueue_referral_cv(referral_id: str) -> bool:
    """
    Enqueue a referral for automatic background CV extraction and matching.
    Returns True if successfully enqueued, False if already queued or disabled.
    """
    if not settings.CV_INTELLIGENCE_ENABLED:
        logger.debug(f"CV Intelligence disabled; skipping enqueue for referral {referral_id}")
        return False

    if referral_id in _pending_ids:
        logger.info(f"Referral {referral_id} is already in the CV processing queue or active.")
        return False

    _pending_ids.add(referral_id)
    q = _get_queue()

    try:
        q.put_nowait(referral_id)
        logger.info(f"[CV Queue] Referral {referral_id} enqueued for automatic CV extraction. (Queue depth: {q.qsize()})")
    except Exception as e:
        logger.error(f"Failed to enqueue referral {referral_id} into CV queue: {e}")
        _pending_ids.discard(referral_id)
        return False

    # Ensure worker task is running
    global _worker_task
    if _worker_task is None or _worker_task.done():
        start_cv_queue_worker()

    return True


def get_cv_queue_status() -> Dict[str, Any]:
    """
    Retrieve diagnostics regarding the CV processing queue.
    """
    q = _get_queue()
    return {
        "is_running": _worker_task is not None and not _worker_task.done(),
        "queue_size": q.qsize(),
        "pending_ids_count": len(_pending_ids),
        "rate_limit_delay_seconds": DEFAULT_RATE_LIMIT_DELAY,
    }
