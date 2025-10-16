# import environ
# env = environ.Env()
from pythonjsonlogger.json import JsonFormatter

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JsonFormatter,  # Use custom JsonFormatter
        },
    },
    "handlers": {
        "json_console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["json_console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
