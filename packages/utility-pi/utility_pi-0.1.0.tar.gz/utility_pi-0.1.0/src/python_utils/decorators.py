import logging
import inspect
from functools import wraps
from typing import (
    Awaitable,
    Callable,
    Any,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)


P = ParamSpec("P")
R = TypeVar("R", bound=Any)


logger = logging.getLogger("python-utils")


@overload
def debug(func: Callable[P, R]) -> Callable[P, R]: ...
@overload
def debug(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]: ...


def debug(func: Callable[P, R]) -> Callable[P, Any]:
    # optimize in non-debug environment
    if not __debug__:
        return cast(Callable[P, R], func)

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Awaitable[R]:
            logger.debug("[%s] args: %s, kwargs: %s", func.__name__, args, kwargs)
            result = await func(*args, **kwargs)
            logger.debug("[%s] result: %s", func.__name__, result)
            return result

        return cast(Callable[P, Awaitable[R]], async_wrapper)
    else:

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            logger.debug("[%s] args: %s, kwargs: %s", func.__name__, args, kwargs)
            result = func(*args, **kwargs)
            logger.debug("[%s] result: %s", func.__name__, result)
            return result

        return cast(Callable[P, R], wrapper)
