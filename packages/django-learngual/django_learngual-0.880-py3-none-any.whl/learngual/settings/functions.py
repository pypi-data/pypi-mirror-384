import logging
from typing import Literal

import environ
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

env = environ.Env()


SENTRY_DSN = env("SENTRY_DSN")
SENTRY_LOG_LEVEL = env("DJANGO_SENTRY_LOG_LEVEL", default=logging.INFO)

sentry_logging = LoggingIntegration(
    level=SENTRY_LOG_LEVEL,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR,  # Send errors as events
)
integrations = [
    sentry_logging,
    DjangoIntegration(),
    CeleryIntegration(monitor_beat_tasks=True),
    RedisIntegration(),
]


def strip_request_data(event, hint):
    if "request" in event:
        if "headers" in event["request"]:
            headers = event["request"]["headers"]
            headers.pop("Authorization", None)

        if "data" in event["request"]:
            del event["request"]["data"]  # Remove request body

    return event


# https://docs.sentry.io/platforms/python/guides/celery/configuration/options/


def sentry_sdk_init(
    env: environ.Env = env,
    server_name: Literal["iam", "messaging", "learn", "payment", "media"] = "iam",
    integrations=integrations,
    environment=None,
    traces_sample_rate=None,
    send_default_pii=False,
    debug=None,
    dsn=SENTRY_DSN,
    before_send=strip_request_data,
    **kwargs
):
    sentry_sdk.init(
        dsn=dsn,
        integrations=integrations,
        environment=environment or env("SENTRY_ENVIRONMENT", default="production")
        if environment is None
        else environment,
        traces_sample_rate=traces_sample_rate
        or env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0)
        if traces_sample_rate is None
        else traces_sample_rate,
        send_default_pii=send_default_pii,
        debug=env.bool("SENTRY_DEBUG", default=False) if debug is None else debug,
        server_name=server_name,
        before_send=before_send,
        **kwargs
    )
    return sentry_sdk
