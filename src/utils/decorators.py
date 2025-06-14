import functools
import os
import time
from functools import wraps

from flask import abort, request
from utils.logger import get_logger

logger = get_logger(__name__)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_token = request.headers.get("Authorization")
        if not auth_token or auth_token != os.getenv("AUTH_TOKEN"):
            abort(403)  # Forbidden
        return f(*args, **kwargs)

    return decorated


def log_request(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        print(f"Request made to {request.path} with method {request.method}")
        return f(*args, **kwargs)

    return decorated


def timing_decorator(func):
    """Decorator to measure function execution time"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result

    return wrapper


def error_handler(func):
    """Decorator to handle and log errors"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise

    return wrapper


def log_calls(func):
    """Decorator to log function calls"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        logger.debug(f"{func.__name__} returned: {result}")
        return result

    return wrapper
