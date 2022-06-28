###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Custom :py:class:`Exception`'s and excepthook implementation."""

__all__ = (
    'ExceptHookCallable',
    'ExceptionEvent',
    'ExceptionHook',
)

import sys
from collections.abc import Callable
from types import TracebackType
from typing import TypeAlias

from .events import *

ExceptHookCallable: TypeAlias = Callable[[type[BaseException], BaseException, TracebackType], None]


class ExceptionEvent(Event):
    """Event fired when an exception is caught by an :py:class:`ExceptionHook`."""
    __slots__ = ('exception', 'traceback')

    def __init__(self, exception: BaseException, traceback: TracebackType) -> None:
        self.exception: BaseException = exception
        self.traceback: TracebackType = traceback


class ExceptionHook:
    """Object that intercepts :py:class:`Exception`'s and handles them"""

    def __init__(self):
        """Initialize the :py:class:`ExceptionHook` for use in a context manager."""
        self.__old_hook: ExceptHookCallable | None = None
        self.event_bus:  EventBus | None = None

    def __call__(self, type_: type[BaseException], exception: BaseException, traceback: TracebackType) -> None:
        """Called when an exception is raised."""
        # Don't handle BaseExceptions
        if not issubclass(type_, Exception):
            return self.__old_hook(type_, exception, traceback)

        EventBus['exceptions'] << ExceptionEvent(exception, traceback)

    def __repr__(self) -> str:
        return f'<{type(self).__name__} (old_hook={self.__old_hook})>'

    def __enter__(self) -> None:
        """Temporary extend current exception hook."""
        self.__old_hook = sys.excepthook
        self.event_bus = EventBus('exceptions')
        sys.excepthook = self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Reset current exception hook to the original one."""
        sys.excepthook = self.__old_hook
        del EventBus['exceptions']

    @property
    def old_hook(self):
        """The original exception hook."""
        return self.__old_hook
