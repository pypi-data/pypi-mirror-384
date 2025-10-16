from __future__ import annotations

import inspect
import threading
from contextlib import contextmanager
from contextvars import Context, ContextVar, Token, copy_context
from functools import partial, wraps
from typing import TYPE_CHECKING, Any, overload

from typing_extensions import TypeVar

from typed_diskcache.core.const import DEFAULT_LOG_CONTEXT, DEFAULT_LOG_THREAD

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session

__all__ = ["context", "enter_session", "log_context"]

_F = TypeVar("_F", bound="Callable[..., Any]", infer_variance=True)
_T = TypeVar("_T", bound="Session | AsyncSession", infer_variance=True)

log_context: ContextVar[tuple[str, int]] = ContextVar(
    "log_thread_context", default=(DEFAULT_LOG_CONTEXT, DEFAULT_LOG_THREAD)
)


@contextmanager
def enter_context(
    context: str, var: ContextVar[tuple[str, int]] | ContextVar[tuple[str, int] | None]
) -> Generator[None, None, None]:
    thread_id = threading.get_native_id()
    log_token: Token[Any] | None = None
    try:
        log_token = var.set((context, thread_id))
        yield
    finally:
        if log_token is not None:
            var.reset(log_token)


@overload
def context(func_or_context: str) -> Callable[[_F], _F]: ...
@overload
def context(func_or_context: _F) -> _F: ...
@overload
def context(func_or_context: _F | str) -> _F | Callable[[_F], _F]: ...
def context(func_or_context: _F | str) -> _F | Callable[[_F], _F]:
    """Decorator to set the log context for the decorated function.

    Args:
        func_or_context: The function to decorate or the context to set.

    Returns:
        The decorated function or the decorator.
    """
    if not isinstance(func_or_context, str):
        name = getattr(func_or_context, "__qualname__", func_or_context.__name__)
        return _context(func_or_context, name=name)

    return partial(_context, name=func_or_context)


@contextmanager
def enter_session(
    session: _T, context_var: ContextVar[_T | None]
) -> Generator[Context, None, None]:
    """Enter the session context.

    Args:
        session: The session to enter.
        context_var: The context variable to set.

    Yields:
        Copy of the current context.
    """
    token = context_var.set(session)
    context = copy_context()
    try:
        yield context
    finally:
        context_var.reset(token)


def _context(func: _F, *, name: str) -> _F:
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapped(*args: Any, **kwargs: Any) -> Any:
            with enter_context(name, log_context):
                local_context = copy_context()
                return await local_context.run(func, *args, **kwargs)

        return async_wrapped  # pyright: ignore[reportReturnType]

    @wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        with enter_context(name, log_context):
            local_context = copy_context()
            return local_context.run(func, *args, **kwargs)

    return wrapped  # pyright: ignore[reportReturnType]
