###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Custom :py:class:`Exception`'s and excepthook implementation."""

__all__ = (
    'ExceptionHook',
)

import sys
from types import BuiltinFunctionType
from types import TracebackType

from .events import *


class ExceptionHook:
    """Object that intercepts :py:class:`Exception`'s and handles them"""

    def __init__(self):
        """Initialize the :py:class:`ExceptionHook` for use in a context manager."""
        self.__old_hook: BuiltinFunctionType | None = None
        EventBus['exceptions'] = EventBus()

    def __call__(self, type_: type[BaseException], exception: BaseException, traceback: TracebackType) -> None:
        """Called when an exception is raised."""
        if not issubclass(type_, Exception):
            # Don't handle BaseException's
            return self.__old_hook(self, type_, exception, traceback)

        print(f'{type_} raised: {exception}', file=sys.stderr)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} (old_hook={self.__old_hook})>'

    def __enter__(self) -> None:
        """Temporary extend current exception hook."""
        self.__old_hook = sys.excepthook
        sys.excepthook = self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Reset current exception hook to the original one."""
        sys.excepthook = self.__old_hook

    @property
    def old_hook(self):
        """The original exception hook."""
        return self.__old_hook
