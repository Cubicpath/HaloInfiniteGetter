###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module used for TOML configurations."""

__all__ = (
    'BetterTomlDecoder',
    'BetterTomlEncoder',
    'CommentValue',
    'make_comment_val',
    'TomlFile',
    'TomlEvents',
    'TomlTable',
    'TomlValue',
)

import warnings
from pathlib import Path
from pathlib import PurePath
from typing import Any
from typing import Final
from typing import TypeAlias

import toml.decoder
import toml.encoder
from toml.decoder import CommentValue

from .events import *

SPECIAL_PATH_PREFIX: Final[str] = '$PATH$|'

TomlTable: TypeAlias = dict[str, 'TomlValue']
TomlValue: TypeAlias = TomlTable | list | float | int | str | bool | PurePath
"""Represents a possible TOML value, with :py:class:`dict` being a Table, and :py:class:`list` being an Array."""


class TomlEvents:
    """Namespace for all events relating to :py:class:`TomlFile` objects."""
    class TomlEvent(Event):
        """Generic event for TomlFiles"""
        __slots__ = ('toml_file',)

        def __init__(self, toml_file: 'TomlFile') -> None:
            self.toml_file = toml_file

    class File(TomlEvent):
        """Accessing a File on disk."""
        __slots__ = ('toml_file', 'path')

        def __init__(self, toml_file: 'TomlFile', path: Path) -> None:
            super().__init__(toml_file=toml_file)
            self.path = path

    class Import(File):
        """Loading a TomlFile."""
        __slots__ = ('toml_file', 'path')

    class Export(File):
        """Exporting a TomlFile to disk"""
        __slots__ = ('toml_file', 'path')

    class KeyAccess(TomlEvent):
        """A key's value is accessed."""
        __slots__ = ('toml_file', 'key')

        def __init__(self, toml_file: 'TomlFile', key: str | None) -> None:
            super().__init__(toml_file=toml_file)
            self.key: str = self._Key(key)

        class _Key(str):
            """Proxy for a key :py:class:`str`.

            If key was none, act as a wildcard for :py:class:`str` comparisons
            """
            __slots__ = ('toml_file', 'key', 'wildcard')

            def __new__(cls, key: str | None) -> 'TomlEvents.KeyAccess._Key':
                o = super().__new__(cls, key if key is not None else '%WILDCARD%')
                return o

            def __init__(self, key: str | None) -> None:
                super().__init__()
                self.key:      str | None = key
                self.wildcard: bool = key is None

            def __bool__(self) -> bool:
                return bool(self.wildcard or self.key)

            def __eq__(self, other: Any) -> bool:
                return self.wildcard or self.key == other

    class Get(KeyAccess):
        """Value is given."""
        __slots__ = ('toml_file', 'key', 'value')

        def __init__(self, toml_file: 'TomlFile', key: str | None = None, value: TomlValue | None = None) -> None:
            super().__init__(toml_file=toml_file, key=key)
            self.value = value

    class Set(KeyAccess):
        """Value is set."""
        __slots__ = ('toml_file', 'key', 'old', 'new')

        def __init__(self, toml_file: 'TomlFile', key: str | None = None, old: TomlValue | None = None, new: TomlValue | None = None) -> None:
            super().__init__(toml_file=toml_file, key=key)
            self.old: TomlValue | None = old
            self.new: TomlValue | None = new

    class Fail(TomlEvent):
        """General Failure."""
        __slots__ = ('toml_file', 'failure',)

        def __init__(self, toml_file: 'TomlFile', failure: str) -> None:
            super().__init__(toml_file=toml_file)
            self.failure = failure


class BetterTomlDecoder(toml.TomlPreserveCommentDecoder):
    """Inherits the effects of :py:class:`toml.TomlPreserveCommentEncoder`.

    With native support for pathlib :py:class:`Path` values; not abandoning the TOML specification.
    """
    def load_value(self, v: str, strictly_valid=True) -> tuple[Any, str]:
        """If the value is a string and starts with the SPECIAL_PATH_PREFIX, load the value enclosed in quotes as a :py:class:`Path`."""
        if v[1:].startswith(SPECIAL_PATH_PREFIX):
            v_path = Path(v[1:].removeprefix(SPECIAL_PATH_PREFIX)[:-1])
            return v_path, 'path'
        return super().load_value(v=v, strictly_valid=strictly_valid)


class BetterTomlEncoder(toml.TomlEncoder):
    """Combines both the effects of :py:class:`toml.TomlPreserveCommentEncoder` and of :py:class:`toml.TomlPathlibEncoder`.

    Has native support for pathlib :py:class:`PurePath`; not abandoning the TOML specification.
    """
    def __init__(self, _dict=dict, preserve=False) -> None:
        super().__init__(_dict, preserve)
        self.dump_funcs[CommentValue] = lambda comment_val: comment_val.dump(self.dump_value)
        self.dump_funcs[PurePath] = self._dump_pathlib_path

    @staticmethod
    def _dump_pathlib_path(v: PurePath) -> str:
        """Translate :py:class:`PurePath` to string and dump."""
        # noinspection PyProtectedMember
        return toml.encoder._dump_str(str(v))

    def dump_value(self, v: TomlValue) -> str:
        """Support :py:class:`Path` decoding by prefixing a :py:class:`PurePath` string with a special marker."""
        if isinstance(v, PurePath):
            if isinstance(v, Path):
                v = v.resolve()
            v = f'{SPECIAL_PATH_PREFIX}{v}'
        return super().dump_value(v=v)


class TomlFile:
    """Object that manages the getting and setting of TOML configurations.

    Houses an :py:class:`EventBus` that allows you to subscribe Callables to changes in configuration.
    """

    def __init__(self, path: Path | str, default: dict[str, TomlValue | CommentValue] | None = None) -> None:
        self._path: Path = Path(path)
        # FIXME: Default not working as expected during import
        self._data: dict[str, TomlValue | CommentValue] = default if default is not None else {}
        self.event_bus: EventBus = EventBus()
        if self.reload() is False:
            warnings.warn(f'Could not load TOML file {self.path} on initialization.')

    def __getitem__(self, key: str) -> TomlValue | None:
        return self.get_key(key)

    def __setitem__(self, key: str, value: TomlValue) -> None:
        self.set_key(key, value)

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def _search_scope(self, path: str, mode: str) -> tuple[dict[str, TomlValue | CommentValue], str]:
        """Search data for the given path to the value, and if found, return the scope and the key that path belongs to.

        :param path: Path to search data for.
        :param mode: Mode that determines which exceptions to raise.
        :return: Tuple containing the scope where the value is found, and the value key to access.
        :raises KeyError: If mode is 'set' and path is a table OR if mode is 'get' and path doesn't exist.
        :raises ValueError: If path is an empty string.
        """
        if not path:
            raise ValueError('Path can not be an empty string.')

        scope: dict = self._data
        paths: list[str] = path.split('/')

        if len(paths) > 1:
            for i, key in enumerate(paths):
                if key:
                    if i == len(paths) - 1:
                        if mode == 'set' and isinstance(scope.get(key), dict):
                            raise KeyError(f'Cannot reassign Table "{".".join(paths[:i])}" to variable.')
                        if mode == 'get' and key not in scope:
                            raise KeyError(f'Key "{key}" not in Table "{".".join(paths[:i]) or "/"}".')

                    elif isinstance(scope.get(key), dict):
                        scope = scope[key]
                        continue
        else:
            key = path

        # noinspection PyUnboundLocalVariable
        return scope, key

    @property
    def path(self) -> Path:
        """Current OS path that TomlFile with save and reload from."""
        return self._path

    @path.setter
    def path(self, value: Path | str) -> None:
        self._path = Path(value)

    def get_key(self, key: str) -> TomlValue | None:
        """Get a key from path. Searches with each '/' defining a new table to check.

        :param key: Key to get value from.
        """
        scope, path = self._search_scope(key, mode='get')

        # Get value from CommentValue
        val = scope.get(path)
        if isinstance(val, CommentValue):
            val = val.val

        self.event_bus.fire(TomlEvents.Get(self, key, val))

        return val

    def set_key(self, key: str, value: TomlValue, comment: str | None = None) -> None:
        """Set a key at path. Searches with each '/' defining a new table to check.

        :param key: Key to set.
        :param value: Value to set key as.
        :param comment: Append an optional comment to the value.
        """
        scope, path = self._search_scope(key, 'set')

        # Preserve comments, or edit them if comment argument was filled
        prev_val = scope.get(path)
        if isinstance(prev_val, CommentValue):
            prev_val.val = value
            value = prev_val
            if comment is not None:
                prev_val.comment = comment
        if not isinstance(value, CommentValue) and comment is not None:
            value = CommentValue(val=value, comment=f'# {comment}', beginline=True, _dict=dict)

        scope[path] = value

        self.event_bus.fire(TomlEvents.Set(self, key, prev_val, value.val if isinstance(value, CommentValue) else value))

    def save(self) -> bool:
        """Save current settings to self.path."""
        return self.export_to(self.path)

    def reload(self) -> bool:
        """Reset settings to settings stored in self.path."""
        return self.import_from(self.path, update=True)

    def export_to(self, path: Path | str) -> bool:
        """Export internal dictionary as a TOML file to path.

        :return: True if successful, otherwise False.
        """
        path = Path(path)  # Make sure path is of type Path
        if path.parent.is_dir():
            with path.open(mode='w', encoding='utf8') as file:
                toml.dump(self._data, file, encoder=BetterTomlEncoder())

            self.event_bus.fire(TomlEvents.Export(self, path))
            self.event_bus.fire(TomlEvents.Get(self))
            return True

        self.event_bus.fire(TomlEvents.Fail(self, 'export'))
        return False

    def import_from(self, path: Path | str, update: bool = False) -> bool:
        """Import TOML file from path to internal dictionary.

        :return: True if successful, otherwise False."""

        path = Path(path)  # Make sure path is of type Path
        if path.is_file():
            try:
                with path.open(mode='r', encoding='utf8') as file:
                    toml_data = toml.load(file, decoder=BetterTomlDecoder())
                    if update:
                        self._data.update(toml_data)
                    else:
                        self._data = toml_data

            except (LookupError, OSError, toml.TomlDecodeError):
                pass  # Pass to end of function, to fail.

            else:
                self.event_bus.fire(TomlEvents.Import(self, path))
                self.event_bus.fire(TomlEvents.Set(self))
                return True

        # If failed:
        self.event_bus.fire(TomlEvents.Fail(self, 'import'))
        return False


def make_comment_val(val: TomlValue, comment: str, new_line=False) -> CommentValue:
    """Build and return :py:class:`CommentValue`."""
    return CommentValue(val=val, comment=f'# {comment}', beginline=new_line, _dict=dict)
