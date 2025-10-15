import copy
import logging
import os
from pathlib import Path

import structlog

# List to store log messages
log_storage = []


def store_log_message(_, __, event_dict):
    """
    Custom processor to store log messages in a list of dictionaries containing the log messages as:

        {
            'event': <the log message>,
            'timestamp': <the timestamp>,
            'level': <the log level (info, debug, warning, etc)>,
        }
    """
    log_storage.append(copy.deepcopy(event_dict))
    return event_dict


log_to_file = os.getenv("PYRXIV_LOG_TO_FILE", "1") == "1"
log_path = Path("./data/logs.json")

if log_to_file and log_path.parent.exists():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        filename=log_path,
        filemode="w",
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

# Add this basic config to ensure logs go to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    # stream=sys.stdout,
    filename="./data/logs.json",
    filemode="w",
)


# Configure structlog with the custom processor
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        store_log_message,
        # structlog.dev.ConsoleRenderer(),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),  # Use stdlib logger backend
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
)

# Create a logger instance
logger = structlog.get_logger()


import functools
import warnings


def deprecated(message="This function is deprecated."):
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapped

    return decorator
