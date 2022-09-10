###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Miscellaneous objects for hi_getter."""
from __future__ import annotations

__all__ = (
    'CaseInsensitiveDict',
    'DeferredCallable',
    'DistributedCallable',
)

from abc import ABC
from abc import abstractmethod
from collections import OrderedDict
from collections.abc import Callable
from collections.abc import Collection
from collections.abc import Generator
from collections.abc import Mapping
from collections.abc import MutableMapping
from typing import Any
from typing import Generic
from typing import TypeAlias
from typing import TypeVar

_VT = TypeVar('_VT')
_CT = TypeVar('_CT', bound=Collection[Callable])  # Bound to Collection of Callables
_PT = TypeVar('_PT')  # Positional Arguments
_KT = TypeVar('_KT')  # Keyword Arguments
_PTCallable: TypeAlias = Callable[[], _PT]  # Which returns _PT
_KTCallable: TypeAlias = Callable[[], _KT]  # Which returns _KT


class _AbstractCallable(ABC):
    """Abstract callable object.

    Child objects are callable as a shortcut to their `run` method.
    """

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


# NOTICE:
#
# Requests
# Copyright 2019 Kenneth Reitz
# Apache 2.0 License
# https://github.com/psf/requests/blob/main/LICENSE

class CaseInsensitiveDict(MutableMapping, Generic[_VT]):
    """A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, **kwargs) -> None:
        self._store: OrderedDict[str, _VT] = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key: str, value: _VT) -> None:
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key: str) -> _VT:
        return self._store[key.lower()][1]

    def __delitem__(self, key: str) -> None:
        del self._store[key.lower()]

    def __iter__(self) -> Generator[str]:
        return (cased_key for cased_key, mapped_value in self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def __or__(self, other: Mapping) -> CaseInsensitiveDict:
        if not isinstance(other, Mapping):
            return NotImplemented

        new = self.__class__(self)
        new.update(other)
        return new

    def __ror__(self, other: Mapping) -> CaseInsensitiveDict:
        if not isinstance(other, Mapping):
            return NotImplemented

        new = self.__class__(other)
        new.update(self)
        return new

    def __ior__(self, other: Mapping) -> CaseInsensitiveDict:
        self.update(other)

        return self

    def lower_items(self) -> Generator[tuple[str, _VT]]:
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lower_key, keyval[1])
            for (lower_key, keyval)
            in self._store.items()
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Mapping):
            return NotImplemented

        other = self.__class__(other)
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self) -> CaseInsensitiveDict:
        """Return new :py:class:`CaseInsensitiveDict` with a copy of this instance's keys and values."""
        return self.__class__(self._store.values())

    def __repr__(self) -> str:
        return str(dict(self.items()))


class DeferredCallable(_AbstractCallable, Generic[_PT, _KT]):
    """A :py:class:`Callable` with args and kwargs stored for further execution.

    Supports deferred argument evaluation when using :py:class:`Callable`'s as arguments.
    This allows the value of the stored arguments to dynamically change depending on
    when the :py:class:`DeferredCallable` is executed.
    """
    __slots__ = ('_extra_pos_args', 'call_funcs', 'call_types', 'callable', 'args', 'kwargs')

    def __init__(self, __callable: Callable = lambda: None, /, *args: _PT | _PTCallable,
                 _extra_pos_args: int = 0,
                 _call_funcs: bool = True,
                 _call_types: bool = False,
                 **kwargs: _KT | _KTCallable) -> None:
        """Creates a new :py:class:`DeferredCallable`.

        When called, any additional arguments must be expected with _extra_pos_args.
        Any arguments that exceed the extra positional argument limit will be trimmed off.

        :param __callable: Callable to store for later execution.
        :param args: positional arguments to store
        :param _extra_pos_args: Extra positional arguments to expect with self.run.
        :param _call_funcs: Whether to call (non-type) callable arguments
        :param _call_types: Whether to call class constructor arguments
        :param kwargs: keyword arguments to store
        """
        self._extra_pos_args:   int = _extra_pos_args
        self.call_funcs:        bool = _call_funcs
        self.call_types:        bool = _call_types
        self.callable:          Callable = __callable
        self.args:              tuple[_PT | _PTCallable, ...] = args
        self.kwargs:            dict[str, _KT | _KTCallable] = kwargs

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

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the stored :py:class:`Callable`.

        Takes any additional arguments and temporarily adds to the stored arguments before execution.

        :param args: positional arguments to pass to callable.
        :param kwargs: keyword arguments to pass callable.
        :raises RuntimeError: Internal callable was not expecting the amount of positional arguments given.
        """
        # Add additional arguments from local args
        args = self.args + args[:self._extra_pos_args]  # Trim all arguments that are not expected
        kwargs |= self.kwargs

        # Evaluate all callable arguments
        args = tuple(self._evaluate_value(arg) for arg in args)
        kwargs = {key: self._evaluate_value(val) for key, val in kwargs.items()}

        try:
            return self.callable(*args, **kwargs)
        except TypeError as e:
            if ' positional argument but ' in str(e):
                raise RuntimeError(f'{str(e).split(" ", maxsplit=1)[0]} was not expecting additional args, '
                                   f'{type(self).__name__}._extra_call_args may not be set correctly.') from e


class DistributedCallable(_AbstractCallable, Generic[_CT, _PT, _KT]):
    """A :py:class:`Callable` that distributes arguments to all specified callables.

    Supports generic type hinting for the callable collections and arguments. Ex::

        foo: DistributedCallable[set] = DistributedCallable({bar}, 1, 2, 3, four=4)
        foo2: DistributedCallable[list] = DistributedCallable([bar], 1, 2, 3, four=4)

        # Now there's no error when doing

        foo.callables.add(baz)
        # And
        foo2.callables.append(baz)
    """
    __slots__ = ('callables', 'args', 'kwargs')

    def __init__(self, __callables: _CT = (), *args: _PT, **kwargs: _KT) -> None:
        """Creates a new :py:class:`DistributedCallable` with the stored callables, args, and kwargs.

        _CT is a Type Generic containing a :py:class:`Collection` of callables.
        """
        self.callables: _CT = __callables
        self.args:      tuple[_PT, ...] = args
        self.kwargs:    dict[str, _KT] = kwargs

    def __repr__(self) -> str:
        """Represents the :py:class:`DistributedCallable` with the stored callable, args, and kwargs."""
        args, kwargs = self.args, self.kwargs
        return f'<{type(self).__name__} {len(self.callables)} functions with {args=}, {kwargs=}>'

    def run(self, *args, **kwargs) -> tuple[Any]:
        """Run all stored :py:class:`Callable`'s with the given extra arguments.

        :return: The results of each callable, packaged in a tuple.
        """
        return tuple(func(*self.args, **self.kwargs) for func in self.callables)

    def generate(self, *args, **kwargs) -> Generator[Any]:
        """Run all stored :py:class:`Callable`'s with the given extra arguments. Yielding every result.

        :return: A generator yielding the results of each callable.
        """
        for func in self.callables:
            yield func(*args, **kwargs)
