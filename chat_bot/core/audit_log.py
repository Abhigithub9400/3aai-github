import logging
from datetime import datetime

import colorlog

from chat_bot.core.config import Settings


def setup_logger(settings: Settings) -> None:
    """
    Copilot audit log setup
    @return:
    """
    # Root logger cleanup
    root_logger = logging.getLogger("uvicorn.error")
    root_logger.setLevel(settings.APP_LOG_LEVEL.upper())

    """Sets up and returns a logger with color and timestamp support, including milliseconds."""
    log_format = "%(levelname)s:     " "%(asctime)s :: %(name)s :: " "%(message)-20s :: " "{%(filename)s : %(funcName)s : %(lineno)d}"
    # Create or get a logger with the given name
    logger = logging.getLogger("chatbot")
    # Prevent the logger from propagating to the root logger (disable extra output)
    logger.propagate = False

    # Clear existing handlers to avoid duplicate messages
    if logger.hasHandlers():  # pragma: no cover
        logger.handlers.clear()
    # Set the log level
    logger.setLevel(settings.APP_LOG_LEVEL.upper())
    # Create console handler
    handler = logging.StreamHandler()

    # Custom formatter for adding milliseconds
    class CustomFormatter(colorlog.ColoredFormatter):
        def formatTime(self, record, datefmt=None):
            record_time = datetime.fromtimestamp(record.created)
            if datefmt:  # pragma: no cover
                return record_time.strftime(datefmt) + f",{int(record.msecs):03d}"
            return record_time.strftime("%Y-%m-%d %H:%M:%S") + f",{int(record.msecs):03d}"  # pragma: no cover

    # Use custom formatter that includes milliseconds
    formatter = CustomFormatter(
        "%(log_color)s" + log_format,
        defaults={"tenant": "global", "user": "cpai"},
        datefmt="%Y-%m-%d %H:%M:%S",  # Milliseconds will be appended manually
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    handler.setFormatter(formatter)
    # Add the handler to the logger
    logger.addHandler(handler)
