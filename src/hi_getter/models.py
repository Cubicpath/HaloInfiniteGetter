###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Miscellaneous objects for hi_getter."""

__all__ = (
    'DeferredCallable',
    'DistributedCallable',
)

from abc import ABC
from abc import abstractmethod
from collections.abc import Callable
from collections.abc import Collection
from collections.abc import Generator
from typing import Any


class _AbstractCallable(ABC):
    """Abstract callable object."""

    def __call__(self, *args, **kwargs) -> Any:
        """Syntax sugar for self.run()"""
        return self.run(*args, **kwargs)

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute functionality with the provided arguments and return the result.

        :param args: positional arguments to call with.
        :param kwargs: keyword arguments to call with.
        """
        raise NotImplementedError


class DeferredCallable(_AbstractCallable):
    """A :py:class:`Callable` with args and kwargs stored for further execution.

    Supports deferred argument evaluation when using :py:class:`Callable`'s as arguments.
    This allows the value of the stored arguments to dynamically change depending on
    when the :py:class:`DeferredCallable` is executed.
    """
    __slots__ = ('_extra_pos_args', 'call_funcs', 'call_types', 'callable', 'args', 'kwargs')

    def __init__(self, __callable: Callable = lambda: None, /, *args: Any | Callable[[], Any],
                 _extra_pos_args: int = 0,
                 _call_funcs: bool = True,
                 _call_types: bool = False,
                 **kwargs: Any | Callable[[], Any]) -> None:
        """Creates a new :py:class:`DeferredCallable`.

        When called, any additional arguments must be expected with _extra_pos_args.
        Any arguments that exceed the extra positional argument limit will be trimmed off.

        :param __callable: Callable to store for later execution.
        :param args: positional arguments to store
        :param _extra_pos_args: Extra positional arguments to expect with self.run.
        :param _call_funcs: Whether to call non-type callables
        :param _call_types: Whether to call class constructors
        :param kwargs: keyword arguments to store
        """
        self._extra_pos_args:   int = _extra_pos_args
        self.call_funcs:        bool = _call_funcs
        self.call_types:        bool = _call_types
        self.callable:          Callable = __callable
        self.args:              tuple[Any | Callable[[], Any], ...] = args
        self.kwargs:            dict[str, Any | Callable[[], Any]] = kwargs

    def __repr__(self) -> str:
        """Represents the :py:class:`DeferredCallable` with the stored callable, args, and kwargs."""
        args, kwargs = self.args, self.kwargs
        return f'<{type(self).__name__} {self.callable} with {args=}, {kwargs=}>'

    def _evaluate_value(self, val: Any) -> Any:
        """Evaluates any callables to their called values.

        :param val: Value to evaluate.
        :return: The called value, if callable.
        """
        return val() if callable(val) and (
                (isinstance(val, type) and self.call_types) or
                (not isinstance(val, type) and self.call_funcs)
        ) else val

    def run(self, *args: Any | Callable[[], Any], **kwargs: Any | Callable[[], Any]) -> Any:
        """Run the stored :py:class:`Callable`.

        Takes any additional arguments and temporarily adds to the stored arguments before execution.

        :param args: positional arguments to pass to callable.
        :param kwargs: keyword arguments to pass callable.
        :raises RuntimeError: Internal callable was not expecting the amount of positional arguments given.
        """
        # Add additional arguments from local args
        args = self.args + args[:self._extra_pos_args]  # Trim all arguments that are not expected
        kwargs |= self.kwargs  # PEP 0584

        # Evaluate all callable arguments
        args = tuple(self._evaluate_value(arg) for arg in args)
        kwargs = {key: self._evaluate_value(val) for key, val in kwargs.items()}

        try:
            return self.callable(*args, **kwargs)
        except TypeError as e:
            if ' positional argument but ' in str(e):
                raise RuntimeError(f'{str(e).split(" ", maxsplit=1)[0]} was not expecting additional args, '
                                   f'{type(self).__name__}._extra_call_args may not be set correctly.') from e


class DistributedCallable(_AbstractCallable):
    """A :py:class:`Callable` that distributes arguments to all specified callables."""

    def __init__(self, __callables: Collection[Callable], *args: Any, **kwargs: Any) -> None:
        """Creates a new :py:class:`DistributedCallable` with the stored callables, args, and kwargs."""
        self.callables: Collection[Callable] = __callables
        self.args:      tuple[Any] = args
        self.kwargs:    dict[str, Any] = kwargs

    def __repr__(self) -> str:
        """Represents the :py:class:`DistributedCallable` with the stored callable, args, and kwargs."""
        args, kwargs = self.args, self.kwargs
        return f'<{type(self).__name__} {len(self.callables)} functions with {args=}, {kwargs=}>'

    def run(self, *args, **kwargs) -> tuple[Any]:
        """Run all stored :py:class:`Callable`'s with the given extra arguments.

        :returns: The results of each callable, packaged in a tuple.
        """
        return tuple(func(*self.args, **self.kwargs) for func in self.callables)

    def generate(self, *args, **kwargs) -> Generator[Any]:
        """Run all stored :py:class:`Callable`'s with the given extra arguments. Yielding every result.

        :returns: A generator yielding the results of each callable.
        """
        for func in self.callables:
            yield func(*args, **kwargs)
