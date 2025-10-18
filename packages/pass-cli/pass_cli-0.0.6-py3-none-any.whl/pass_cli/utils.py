import logging
import sys
from functools import wraps, partial


def setup_logger(name, format):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def store_last_op(app):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            app.last_op = partial(f, *args, **kwargs)
            return f(*args, **kwargs)

        return decorated

    return decorator
