import json
import logging
import os


class JsonFormatter(logging.Formatter):
    """
    Custom formatter to output logs in JSON format, including logger name, extra data, and environment variables.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = os.getenv("SERVICE_NAME", "unknown_service")
        self.environment = os.getenv("ENVIRONMENT", "unknown_env")

    def format(self, record):
        log_record = {
            "level": record.levelname,
            "time": self.formatTime(record, self.datefmt),
            "logger": record.name,  # Include logger name
            "module": record.module,
            "message": self._format_message(record),
            "pathname": record.pathname,
            "lineno": record.lineno,
            "process": record.process,
            "thread": record.thread,
            "service": self.service,
            "environment": self.environment,
        }

        for attr, value in record.__dict__.items():
            if attr not in log_record and not attr.startswith("_"):
                log_record[attr] = value

        return json.dumps(log_record)

    def _format_message(self, record):
        """
        Handle the case where arguments are passed to the logger (like in logger.info('%s %s', arg1, arg2)).
        This method ensures that the message is correctly formatted.
        """
        if record.args:
            return record.getMessage() % record.args
        return record.getMessage()
