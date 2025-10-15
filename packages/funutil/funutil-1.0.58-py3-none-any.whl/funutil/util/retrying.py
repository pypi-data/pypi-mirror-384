import time
from functools import wraps

from .log import getLogger

logger = getLogger("funutil")

__all__ = ["Retry", "retry"]


class Retry:
    def __init__(
        self,
        retry_cnt=3,
        sleep_after_retry=0,
        throw_error_after_retry=True,
        *args,
        **kwargs,
    ):
        self.retry_cnt = retry_cnt
        self.sleep_after_retry = sleep_after_retry
        self.throw_error_after_retry = throw_error_after_retry

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for step in range(self.retry_cnt):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(
                        f"Exception while retrying {step + 1}/{self.retry_cnt}: {e}"
                    )
                    if self.sleep_after_retry > 0:
                        time.sleep(self.sleep_after_retry)
                    if self.throw_error_after_retry and step == self.retry_cnt - 1:
                        raise Exception(e)
            return None

        return wrapper


def retry(
    retry_cnt=3,
    sleep_after_retry=0,
    throw_error_after_retry=True,
    *args,
    **kwargs,
):
    return Retry(
        retry_cnt=retry_cnt,
        sleep_after_retry=sleep_after_retry,
        throw_error_after_retry=throw_error_after_retry,
        *args,
        **kwargs,
    )
