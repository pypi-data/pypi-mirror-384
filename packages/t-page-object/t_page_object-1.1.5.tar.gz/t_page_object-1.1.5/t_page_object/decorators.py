"""Decorators module."""

import time

from selenium.common import ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException

MAX_RETRIES = 5


def retry_if_stale_element_error(func):
    """Decorator to retry if stale element error occurs."""

    def wrapper(*args, **kwargs):
        tries = 0
        exception = None
        while tries < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except (StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException) as e:
                time.sleep(1)
                exception = e
                tries += 1
        else:
            raise exception

    return wrapper
