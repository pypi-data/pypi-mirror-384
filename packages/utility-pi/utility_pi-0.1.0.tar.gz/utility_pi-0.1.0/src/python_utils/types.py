from typing import (
    Awaitable,
    Callable,
    Any,
    ParamSpec,
    TypeAlias,
    TypeVar,
    Union,
)

P = ParamSpec("P")
R = TypeVar("R", bound=Any)
SyncT: TypeAlias = Callable[P, R]
AsyncT: TypeAlias = Callable[P, Awaitable[R]]
TargetT = Union[SyncT | AsyncT]
Args = tuple[Any, ...]
Kwargs = dict[str | Any, Any]
