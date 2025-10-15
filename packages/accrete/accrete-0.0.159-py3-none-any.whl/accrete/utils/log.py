import logging
from functools import wraps
from timeit import default_timer as timer

_logger = logging.getLogger(__name__)


def log_time(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        start = timer()
        result = f(*args, **kwargs)
        stop = timer()
        _logger.info(f'{f.__module__}.{f.__name__} Duration: {(stop - start)} Seconds')
        return result
    return decorator
