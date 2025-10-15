import os
from typing import Callable

from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
)

_WAIT_MIN = int(os.getenv('EXTRACT_WAIT_MIN', '10'))
_WAIT_MAX = int(os.getenv('EXTRACT_WAIT_MAX', '60'))
_STOP_AFTER = int(os.getenv('EXTRACT_STOP_AFTER', '5'))


def call_function_with_retry(
    func: Callable,
    kwargs: dict,
    min_wait: int = _WAIT_MIN,
    max_wait: int = _WAIT_MAX,
    stop_after: int = _STOP_AFTER,
):
    """
    Call a function with retry logic.
    :param func: the function to call
    :param kwargs: the keyword arguments to pass to the function
    :param min_wait: the minimum wait time between retries in seconds (0-10 seconds)
    :param max_wait: the maximum wait time between retries in seconds (0-60 seconds)
    :param stop_after: the number of attempts to retry before giving up (0-5 attempts)
    :return: the result of the function call
    """
    min_wait = min_wait if _WAIT_MIN > min_wait >= 0 else _WAIT_MIN
    max_wait = max_wait if _WAIT_MAX > max_wait >= 0 else _WAIT_MAX
    stop_after = stop_after if _STOP_AFTER > stop_after >= 0 else _STOP_AFTER

    @retry(
        wait=wait_exponential(multiplier=2, min=min_wait, max=max_wait),
        stop=stop_after_attempt(stop_after),
        retry=retry_if_not_exception_type(RuntimeError)  # Retry on all exceptions except RuntimeError
    )
    def do_call():
        return func(**kwargs)

    return do_call()
