import logging

from django.http.request import HttpRequest
from django.http.response import JsonResponse

from iam_service.learngual.services.celery_beat_helper import beat_is_alive


def celery_beat_health_check(request: HttpRequest):
    """
    View to check the health status of Celery Beat.

    This endpoint returns a JSON response indicating whether the Celery Beat scheduler is alive.
    Returns HTTP 200 if alive, otherwise HTTP 503.
    """
    logger = logging.getLogger(__name__)

    # Check if Celery Beat is alive using the beat_is_alive service
    if beat_is_alive():
        logger.info("Celery Beat health check passed.")
        return JsonResponse(
            {"status": "ok"}, status=200, content_type="application/json"
        )

    logger.warning("Celery Beat health check failed: Celery Beat is not alive.")
    return JsonResponse(
        {"status": "error", "message": "Celery Beat is not alive"},
        status=503,
        content_type="application/json",
    )
