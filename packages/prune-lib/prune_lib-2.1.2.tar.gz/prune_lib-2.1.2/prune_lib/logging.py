import inspect
import logging
from logging import LoggerAdapter
from pathlib import Path

from django.core.handlers.asgi import ASGIRequest
from django.core.handlers.wsgi import WSGIRequest


def get_django_logging_config(
    base_dir: Path, *, with_file_handler=False, testing=False
):
    def remove_prefix(text: str, substring: str) -> str:
        if text.startswith(substring):
            return text[len(substring) :]
        return text

    def strip_pathname(record):
        if "extra_pathname" not in record.__dict__:
            setattr(record, "extra_pathname", record.pathname)
        if "extra_lineno" not in record.__dict__:
            setattr(record, "extra_lineno", record.lineno)
        if record.extra_pathname:
            record.extra_pathname = remove_prefix(
                record.extra_pathname, str(base_dir) + "/"
            )
        return True

    def add_context(record):
        if "context" in record.__dict__ and record.context:
            if not record.context.startswith(" (context: "):
                record.context = f" (context: {record.context})"
        else:
            setattr(record, "context", "")
        return True

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "strip_pathname": {
                "()": "django.utils.log.CallbackFilter",
                "callback": strip_pathname,
            },
            "add_context": {
                "()": "django.utils.log.CallbackFilter",
                "callback": add_context,
            },
        },
        "formatters": {
            "verbose": {
                "format": "[{asctime} - {levelname} - {extra_pathname}.{extra_lineno:d}] {message}{context}\n",
                "style": "{",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "null": {"class": "logging.NullHandler"},
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
                "filters": ["strip_pathname", "add_context"],
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "dev": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    if testing:
        config["loggers"]["django"]["level"] = "ERROR"
        config["loggers"]["dev"]["handlers"] = ["null"]
    elif with_file_handler:
        config["handlers"]["devfile"] = {
            "class": "logging.FileHandler",
            "filename": "/var/log/django/dev.log",
            "formatter": "verbose",
            "filters": ["strip_pathname", "add_context"],
        }
        config["loggers"]["dev"]["handlers"] += ["devfile"]
        config["loggers"]["django"]["handlers"] += ["devfile"]
    return config


_logger = logging.getLogger("dev")


def get_caller_info(frame_index):
    caller_frame = inspect.currentframe().f_back.f_back.f_back
    for _ in range(frame_index):
        caller_frame = caller_frame.f_back
    filename = caller_frame.f_code.co_filename
    line_number = caller_frame.f_lineno
    return filename, line_number


class ContextAdapter(LoggerAdapter):
    def log(self, level, msg, *args, context=None, frame_index=0, **kwargs):
        if context:
            pcontext = {}
            for key, value in context.items():
                if isinstance(value, (ASGIRequest, WSGIRequest)):
                    value = {
                        "id": id(value),
                        "user": value.user.id,
                        "path": value.get_full_path(),
                    }
                pcontext[key] = value
            if "extra_request" in pcontext and "request" in pcontext:
                pcontext["request"].update(pcontext["extra_request"])
                del pcontext["extra_request"]
            self.extra = {"context": str(pcontext)}
        else:
            self.extra = {}
        filename, line_number = get_caller_info(frame_index)
        self.extra["extra_pathname"] = filename
        self.extra["extra_lineno"] = line_number
        super().log(level, msg, *args, **kwargs)


logger = ContextAdapter(_logger)
