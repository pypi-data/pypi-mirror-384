import logging
import time
import traceback
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from functools import wraps
from logging import Logger
from typing import Any, ParamSpec, TypeVar, cast

from hpyhrtbase.model import ErrorInfoException, ErrorResponse

mod_logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


class FuncUtil:
    @staticmethod
    def deco_handle_error_info_exception(f: Callable[P, T]) -> Callable[P, T]:
        @wraps(f)
        def f_handle_error_info_exception(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return f(*args, **kwargs)
            except ErrorInfoException as e:
                return cast(T, ErrorResponse(error=e.error_info))

        return f_handle_error_info_exception

    @staticmethod
    def retry(
        ExceptionToCheck: type[Exception],
        tries: int = 4,
        delay: float = 3,
        backoff: float = 2,
        logger: Logger | None = None,
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """Retry calling the decorated function using an exponential backoff.

        http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
        original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

        :param ExceptionToCheck: the exception to check. may be a tuple of
            exceptions to check
        :type ExceptionToCheck: Exception or tuple
        :param tries: number of times to try (not retry) before giving up
        :type tries: int
        :param delay: initial delay between retries in seconds
        :type delay: int
        :param backoff: backoff multiplier e.g. value of 2 will double the delay
            each retry
        :type backoff: int
        :param logger: logger to use. If None, print
        :type logger: logging.Logger instance
        """

        def deco_retry(f: Callable[P, T]) -> Callable[P, T]:
            @wraps(f)
            def f_retry(*args: P.args, **kwargs: P.kwargs) -> T:
                mtries, mdelay = tries, delay
                while mtries > 1:
                    try:
                        return f(*args, **kwargs)
                    except ExceptionToCheck as e:
                        mod_logger.info(traceback.format_exc())
                        msg = f"{str(e)}, Retrying in {mdelay:.2f} seconds..."
                        if logger:
                            logger.warning(msg)
                        else:
                            mod_logger.warning(msg)
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                return f(*args, **kwargs)

            return f_retry  # true decorator

        return deco_retry

    @staticmethod
    def retry_until_timeout(func: Callable[..., Any], timeout: float, sleep_time: float = 1) -> Any:
        final_time = datetime.now(timezone.utc) + timedelta(seconds=timeout)

        first = True
        while datetime.now(timezone.utc) <= final_time:
            if first:
                rsp = func()
                first = False
            else:
                time.sleep(sleep_time)
                rsp = func()

            if rsp is None:
                continue
            else:
                return rsp

        return None

    @staticmethod
    def run_ignore_exception(func: Callable[..., Any]) -> None:
        try:
            func()
        except Exception:
            pass
