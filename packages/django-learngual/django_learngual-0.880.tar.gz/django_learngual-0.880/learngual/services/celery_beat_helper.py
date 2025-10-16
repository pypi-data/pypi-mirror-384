import logging
from datetime import datetime

from django.core.cache import cache
from django.utils import timezone

BEAT_KEY_CACHE = "celery_beat_health"

logger = logging.getLogger(__name__)


def beat_is_alive() -> bool:
    """
    Check if Celery Beat is alive by verifying the last heartbeat timestamp in cache.

    Returns:
        bool: True if Celery Beat is considered alive (last heartbeat within 2 minutes), False otherwise.
    """
    # Retrieve the last heartbeat timestamp from cache
    datetime_str = cache.get(BEAT_KEY_CACHE, "")
    if not datetime_str:
        logger.warning(
            "Celery Beat health key not found in cache. Setting new heartbeat."
        )
        set_beat_health()
        return True

    datetime_obj = datetime.fromisoformat(datetime_str)

    # Calculate the time difference between now and the last heartbeat
    delta = timezone.now() - datetime_obj
    if delta.total_seconds() < 120:
        logger.info("Celery Beat is alive.")
        return True

    logger.warning(
        f"Celery Beat heartbeat is stale (older than 2 minutes). {datetime_obj.ctime()}"
    )
    return False


def set_beat_health():
    """
    Update the Celery Beat heartbeat timestamp in cache.

    This function sets the current timestamp in the cache to indicate that Celery Beat is alive.
    It can be called by a scheduled task or a health check endpoint to refresh the heartbeat.

    Returns:
        dict: A dictionary containing the status and the timestamp when the heartbeat was set.
    """
    now = timezone.now()
    datetime_str = now.isoformat()
    # Store the current timestamp in cache with a timeout of 5 minutes
    cache.set(BEAT_KEY_CACHE, datetime_str, timeout=300)
    logger.info(f"Set Celery Beat heartbeat in cache at {datetime_str}.")
    return {"status": "ok", "timestamp": datetime_str}
