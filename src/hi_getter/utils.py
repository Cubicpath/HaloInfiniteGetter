###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utils for hi_getter."""

__all__ = (
    'current_requirement_licenses',
    'current_requirement_names',
    'current_requirement_versions',
    'DeferredCallable',
    'dump_data',
    'get_parent_doc',
    'has_package',
    'patch_windows_taskbar_icon',
    'unique_values',
)

import json
import os
import sys
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Generator
from pathlib import Path
from typing import Any


class DeferredCallable:
    """A :py:class:`Callable` with args and kwargs stored for further execution.

    Supports deferred argument evaluation when using :py:class:`Callable`'s as arguments.
    This allows the value of the stored arguments to dynamically change depending on
    when the :py:class:`DeferredCallable` is executed.
    """
    __slots__ = ('__no_event_arg__', '_extra_pos_args', 'call_funcs', 'call_types', 'callable', 'args', 'kwargs')

    def __init__(self, __callable: Callable = lambda: None, /, *args: Any | Callable,
                 _extra_pos_args: int = -1,
                 _call_funcs: bool = True,
                 _call_types: bool = False,
                 **kwargs: Any | Callable) -> None:
        """Creates a new :py:class:`DeferredCallable`.

        :param __callable: Callable to store for later execution.
        :param args: positional arguments to store
        :param _extra_pos_args: Extra positional arguments to expect with self.run; -1 is wildcard.
        :param _call_funcs: Whether to call non-type callables
        :param _call_types: Whether to call class constructors
        :param kwargs: keyword arguments to store
        """
        self.__no_event_arg__:  bool = _extra_pos_args < 1
        self._extra_pos_args:   int = _extra_pos_args
        self.call_funcs:        bool = _call_funcs
        self.call_types:        bool = _call_types
        self.callable:          Callable = __callable
        self.args:              tuple[Any | Callable, ...] = args
        self.kwargs:            dict[str, Any | Callable] = kwargs

    def __call__(self, *args, **kwargs) -> Any:
        """Syntax sugar for self.run()"""
        return self.run(*args, **kwargs)

    def __repr__(self) -> str:
        """Represents the :py:class:`DeferredCallable` with the stored callable, args, and kwargs."""
        args, kwargs = self.args, self.kwargs
        return f'<{type(self).__name__} {self.callable} with {args=}, {kwargs=}>'

    def run(self, *args, **kwargs) -> Any:
        """Run the stored :py:class:`Callable`.

        Takes any additional arguments and temporarily adds to the stored arguments before execution.

        :param args: positional arguments to pass to callable.
        :param kwargs: keyword arguments to pass callable.
        :raises RuntimeError: Internal callable was not expecting the amount of positional arguments given.
        :raises ValueError: Amount of positional arguments given is not equal to the expected amount defined during object initialization.
        """
        if 0 <= self._extra_pos_args != len(args):
            raise ValueError(f'Amount of args given ({len(args)}) is not equal to the expected amount ({self._extra_pos_args})')

        # Add additional arguments from local args
        args: tuple[Any | Callable, ...] = self.args + args
        kwargs |= self.kwargs  # PEP 0584

        # Evaluate all callable arguments
        args:   Generator[Any] = (arg() if callable(arg) and (
                (isinstance(arg, type) and self.call_types) or
                (not isinstance(arg, type) and self.call_funcs)
        ) else arg for arg in args)

        kwargs: dict[Any] = {key: val() if callable(val) and (
                (isinstance(val, type) and self.call_types) or
                (not isinstance(val, type) and self.call_funcs)
        ) else val for key, val in kwargs.items()}

        try:
            return self.callable(*args, **kwargs)
        except TypeError as e:
            if ' positional argument but ' in str(e):
                raise RuntimeError(f'{str(e).split(" ", maxsplit=1)[0]} was not expecting additional args, '
                                   f'{type(self).__name__}._extra_call_args may not be set correctly.') from e


def dump_data(path: Path | str, data: bytes | dict | str, encoding: str | None = None) -> None:
    """Dump data to path as a file."""
    default_encoding = 'utf8'
    path = Path(path)
    if not path.parent.exists():
        os.makedirs(path.parent)

    if isinstance(data, str):
        # Write strings at text files
        path.write_text(data, encoding=encoding or default_encoding)
    elif isinstance(data, bytes):
        # Decode bytes if provided with encoding, else write as data
        if encoding is not None:
            data = data.decode(encoding=encoding)
            path.write_text(data, encoding=encoding)
        else:
            path.write_bytes(data)
    elif isinstance(data, dict):
        # Write dictionaries as json files
        with path.open('w', encoding=encoding or default_encoding) as file:
            json.dump(data, file, indent=2)


def get_parent_doc(__type: type, /) -> str | None:
    """Get the nearest parent documentation using the given :py:class:`type`'s mro."""
    doc = None
    for parent in __type.__mro__:
        doc = parent.__doc__
        if doc:
            break
    return doc


def patch_windows_taskbar_icon(app_id: str = '') -> None:
    """Override Python's default Windows taskbar icon with the custom one set by the app window."""
    if sys.platform == 'win32':
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


def has_package(package: str) -> bool:
    """Returns whether the given package name is installed in the current environment.

    :param package: Package name to search; hyphen-insensitive
    """
    from pkg_resources import WorkingSet

    for pkg in WorkingSet():
        if package.replace('-', '_') == pkg.project_name.replace('-', '_'):
            return True
    return False


def current_requirement_names(package: str, include_extras: bool = False) -> list[str]:
    """Return the current requirement names for the given package.

    :param package: Package name to search
    :param include_extras: Whether to include packages installed with extras
    :return: list of package names.
    """
    from importlib.metadata import requires

    req_names = []
    for requirement in requires(package):
        if not include_extras and '; extra' in requirement:
            continue

        split_char = 0
        for char in requirement:
            if not char.isalnum() and char not in ('-', '_'):
                break
            split_char += 1

        req_names.append(requirement[:split_char])

    return req_names


def current_requirement_versions(package: str, include_extras: bool = False) -> dict[str, str]:
    """Return the current versions for the requirements of the given package.

    :param package: Package name to search
    :param include_extras: Whether to include packages installed with extras
    :return: dict mapping package names to their version string.
    """
    from importlib.metadata import version
    return {name: version(name) for name in current_requirement_names(package, include_extras)}


def current_requirement_licenses(package: str, include_extras: bool = False) -> dict[str, tuple[str, str]]:
    """Return the current licenses for the requirements of the given package.

    CANNOT get license file from a package with an editable installation.

    :param package: Package name to search
    :param include_extras: Whether to include packages installed with extras
    :return: dict mapping a package nams to a tuple containing the license name and contents.
    """
    from importlib.metadata import metadata
    from pkg_resources import get_distribution

    result = {}
    for requirement in ([package] + current_requirement_names(package, include_extras)):
        dist = get_distribution(requirement)
        name = dist.project_name.replace("-", "_")
        license_text = None

        info_path = Path(dist.location) / f'{name}-{dist.version}.dist-info'
        if not info_path.is_dir():
            egg_path = info_path.with_name(f'{name}.egg-info')
            if egg_path.is_dir():
                info_path = egg_path

        for file in info_path.iterdir():
            f_name = file.name.lower()
            if 'license' in f_name:
                license_text = file.read_text(encoding='utf8')

        result[name] = (metadata(name).get('License', 'UNKNOWN'), license_text)

    return result


def unique_values(data: Iterable) -> set:
    """Recursively get all values in any Iterables. For Mappings, ignore keys and only remember values."""
    new: set = set()
    if isinstance(data, Mapping):
        # Loop through Mapping values
        for value in data.values():
            new.update(unique_values(value))
    elif isinstance(data, Iterable) and not isinstance(data, str):
        # Loop through Iterable values
        for value in data:
            new.update(unique_values(value))
    else:
        # Finally, get value
        new.add(data)
    return new
