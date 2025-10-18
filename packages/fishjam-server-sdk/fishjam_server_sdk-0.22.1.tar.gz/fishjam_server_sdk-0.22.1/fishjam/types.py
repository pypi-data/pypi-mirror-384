import functools
from typing import (
    Any,
    Callable,
    Coroutine,
    ParamSpec,
    TypeVar,
)

R = TypeVar("R")
P = ParamSpec("P")

AsyncCallable = Callable[P, Coroutine[Any, Any, R]]

AnyCallable = Callable[P, R] | AsyncCallable[P, R]


def to_async(f: Callable[P, R]) -> AsyncCallable[P, R]:
    @functools.wraps(f)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs):
        return f(*args, **kwargs)

    return _wrapper
