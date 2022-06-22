###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Data structures for hi_getter.network."""

__all__ = (
    'CaseInsensitiveDict',
)

from collections import OrderedDict
from collections.abc import Generator
from collections.abc import Mapping
from collections.abc import MutableMapping
from typing import Generic
from typing import TypeVar

_VT = TypeVar('_VT')


# NOTICE:
#
# Requests
# Copyright 2019 Kenneth Reitz
# Apache 2.0 License

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

    def __or__(self, other: Mapping) -> 'CaseInsensitiveDict':
        if not isinstance(other, Mapping):
            return NotImplemented

        new = self.__class__(self)
        new.update(other)
        return new

    def __ror__(self, other: Mapping) -> 'CaseInsensitiveDict':
        if not isinstance(other, Mapping):
            return NotImplemented

        new = self.__class__(other)
        new.update(self)
        return new

    def __ior__(self, other: Mapping) -> 'CaseInsensitiveDict':
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
    def copy(self) -> 'CaseInsensitiveDict':
        """Return new :py:class:`CaseInsensitiveDict` with a copy of this instance's keys and values."""
        return self.__class__(self._store.values())

    def __repr__(self) -> str:
        return str(dict(self.items()))
