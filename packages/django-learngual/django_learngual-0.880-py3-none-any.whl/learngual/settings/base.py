import environ

from . import LOGGING as GEN_LOGGING

env = environ.Env()

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = False
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        },
        **GEN_LOGGING.get("formatters", {}),
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        **GEN_LOGGING.get("handlers", {}),
    },
    "loggers": {**GEN_LOGGING.get("loggers", {})},
    "root": {"level": "INFO", "handlers": ["console", "json_console"]},
}


LEARNGUAL_GITHUB_TOKEN = env("LEARNGUAL_GITHUB_TOKEN")
LEARNGUAL_GITHUB_USERNAME = env("LEARNGUAL_GITHUB_USERNAME")
LEARNGUAL_GITHUB_REPO_NAME = env("LEARNGUAL_GITHUB_REPO_NAME")
LEARNGUAL_GITHUB_BRANCH = env("LEARNGUAL_GITHUB_BRANCH")
