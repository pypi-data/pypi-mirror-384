import ipaddress
import logging
import os
import time
import tracemalloc
import zoneinfo
from logging import getLogger
from logging.handlers import RotatingFileHandler

import pytz
from django.db import connection
from django.http import HttpResponseForbidden
from django.test.utils import CaptureQueriesContext
from django.utils import timezone, translation
from django.utils.deprecation import MiddlewareMixin

from .utils import get_language_code

logger = getLogger(__file__)


BLOCKED_IPS = [x.strip() for x in os.getenv("BLOCKED_IPS", "").split(",") if x.strip()]
BLOCKED_NETWORKS = [
    x.strip() for x in os.getenv("BLOCKED_NETWORKS", "").split(",") if x.strip()
]


class TimeZoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz_header = request.headers.get("TZ")

        if tz_header:
            try:
                timezone.activate(tz_header)
            except (pytz.UnknownTimeZoneError, zoneinfo.ZoneInfoNotFoundError):
                logger.error("Invalid timezone %s", tz_header)
                pass  # Handle unknown timezone error here
        else:
            # Set default timezone if TZ header is not provided
            timezone.activate("UTC")

        response = self.get_response(request)
        timezone.deactivate()
        return response


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract language from _lang query parameter
        lang = request.GET.get("_lang")
        if lang:
            lang = get_language_code(lang).upper()
        if lang:
            # Activate the new language if it's valid
            translation.activate(lang)
        else:
            # Fallback to default language if not valid
            translation.activate("EN")

        response = self.get_response(request)
        # Restore the original language
        translation.activate("EN")
        return response


class RequestTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Record the start time
        start_time = time.time()

        # Process the request
        response = self.get_response(request)

        # Calculate the time taken
        duration = time.time() - start_time
        logger.info(f"Request to {request.path} took {duration:.4f} seconds")

        response["X-Request-Duration"] = f"{duration:.4f} seconds"
        return response


class MemoryUsageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        tracemalloc.start()  # Start tracking memory

    def process_response(self, request, response):
        _, peak_memory = tracemalloc.get_traced_memory()
        peak_memory_mb = peak_memory / 1024 / 1024  # Convert to MB
        tracemalloc.stop()  # Stop tracking

        logger.info(
            f"[{request.method}] {request.path} - Peak Memory Used: {peak_memory_mb:.2f} MB"
        )
        return response


class ResponseTimeLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("metric_logger")
        if not self.logger.handlers:
            handler = RotatingFileHandler(
                "metric.log", maxBytes=5 * 1024 * 1024, backupCount=3
            )
            formatter = logging.Formatter(
                "%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration_ms = int((time.time() - start) * 1000)
        path = request.path
        method = request.method
        self.logger.info(
            f"Method: {method} | Path: {path} | Response Time: {duration_ms} ms"
        )
        return response


class QueryLoggingMiddleware:
    """
    Django middleware for logging all SQL queries executed during the processing of each HTTP request.

    This middleware captures all database queries made during the lifecycle of a request,
    logs the total number of queries, their execution time, and details about each query
    (including the SQL statement and its duration) to a rotating log file ("query.log").
    The log entry also includes the HTTP method, request path, user (if authenticated), and
    the total duration of the request.

    Attributes:
        get_response (callable): The next middleware or view in the Django request/response cycle.
        logger (logging.Logger): Logger instance for writing query logs to file.

        Initialize the QueryLoggingMiddleware.

        Sets up the logger with a rotating file handler if it hasn't been set up already.

        Args:
            get_response (callable): The next middleware or view in the Django request/response cycle.

        # ...


        Process the incoming HTTP request, capture and log all SQL queries executed.

        Args:
            request (HttpRequest): The incoming HTTP request object.

        Returns:
            HttpResponse: The response generated by the next middleware or view.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("query_logger")
        if not self.logger.handlers:
            handler = RotatingFileHandler(
                "query.log", maxBytes=5 * 1024 * 1024, backupCount=3
            )
            formatter = logging.Formatter(
                "%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def __call__(self, request):
        start_time = time.time()
        with CaptureQueriesContext(connection) as queries:
            response = self.get_response(request)
        duration = time.time() - start_time
        path = request.path
        method = request.method
        user = getattr(request, "user", None)
        user_repr = str(user) if user and user.is_authenticated else "Anonymous"
        total_queries = len(queries.captured_queries)
        if queries.captured_queries:
            log_lines = [
                f"Method: {method} | Path: {path} | User: {user_repr} | "
                f"Total Queries: {total_queries} | Total Duration: {duration:.4f} sec | Queries:"
            ]
            for q in queries.captured_queries:
                sql = q.get("sql")
                q_duration = q.get("time")
                log_lines.append(f"    Query: {sql} | Duration: {q_duration} sec")
            log_message = "\n".join(log_lines)
            self.logger.info(log_message)
        return response


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "").strip()
    if x_forwarded_for and x_forwarded_for.split(","):
        ip = x_forwarded_for.split(",")[0].strip()  # Take the first IP in the list
    else:
        ip = request.META.get("REMOTE_ADDR", "").strip()
    return ip


class BlockBlackListedIPMiddleware:
    """
    Django middleware for blocking requests from blacklisted IP addresses and network ranges.

    This middleware checks the client's IP address against a list of blocked individual IPs
    and network ranges. If the client's IP matches any blocked IP or falls within a blocked
    network range, the request is denied with an HTTP 403 Forbidden response.

    The blocked IPs and networks are configured in Django settings as BLOCKED_IPS and
    BLOCKED_NETWORKS respectively.

    Attributes:
        get_response (callable): The next middleware or view in the Django request/response cycle.

    Args:
        get_response (callable): The next middleware or view in the Django request/response cycle.

    Returns:
        HttpResponse: Either an HTTP 403 Forbidden response for blocked IPs, or the response
                     from the next middleware/view in the chain.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = get_client_ip(request)
        if ip:
            client_ip = ipaddress.ip_address(ip)

            # Check individual IPs
            if BLOCKED_IPS and ip in BLOCKED_IPS:
                logger.info(
                    f"[BlockBlackListedIPMiddleware] Blocked request from IP: {ip} - IP found in blocked list"
                )
                return HttpResponseForbidden("Access Denied: Your IP is blocked.")

            # Check IP ranges
            if BLOCKED_NETWORKS:
                for network_str in BLOCKED_NETWORKS:
                    network = ipaddress.ip_network(network_str)
                    if client_ip in network:
                        logger.info(
                            f"[BlockBlackListedIPMiddleware] Blocked request from IP: {ip} - IP "
                            f"falls within blocked network range: {network_str}"
                        )
                        return HttpResponseForbidden(
                            "Access Denied: Your IP range is blocked."
                        )

        response = self.get_response(request)
        return response
