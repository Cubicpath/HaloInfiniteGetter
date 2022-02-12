###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module used for TOML configurations."""
import warnings
from collections.abc import Callable
from pathlib import Path
from pathlib import PurePath
from types import UnionType
from typing import Any

import toml
from toml.decoder import CommentValue
from toml.decoder import TomlDecodeError
from toml.decoder import TomlPreserveCommentDecoder
from toml.encoder import _dump_str
from toml.encoder import TomlEncoder
# noinspection PyProtectedMember

__all__ = (
    'BetterTomlDecoder',
    'BetterTomlEncoder',
    'TOML_VALUE',
    'TomlFile',
)

TOML_VALUE: UnionType = dict | list | float | int | str | bool | PurePath
"""Represents a possible TOML value, with :py:class:`dict` being a Table, and :py:class:`list` being an Array."""

SPECIAL_PATH_PREFIX = '$PATH$|'

# TODO: Move event_subscribers to an EventBus class


class BetterTomlDecoder(TomlPreserveCommentDecoder):
    """Inherits the effects of :py:class:`toml.TomlPreserveCommentEncoder`.

    With native support for pathlib :py:class:`Path` values; not abandoning the TOML specification.
    """
    def load_value(self, v: str, strictly_valid=True):
        """If the value is a string and starts with the SPECIAL_PATH_PREFIX, load the value enclosed in quotes as a :py:class:`Path`."""
        if v[1:].startswith(SPECIAL_PATH_PREFIX):
            v = Path(v[1:].removeprefix(SPECIAL_PATH_PREFIX)[:-1])
            return v, strictly_valid
        return super().load_value(v=v, strictly_valid=strictly_valid)


class BetterTomlEncoder(TomlEncoder):
    """Combines both the effects of :py:class:`toml.TomlPreserveCommentEncoder` and of :py:class:`toml.TomlPathlibEncoder`.

    Has native support for pathlib :py:class:`PurePath`; not abandoning the TOML specification.
    """
    def __init__(self, _dict=dict, preserve=False):
        super().__init__(_dict, preserve)
        self.dump_funcs[CommentValue] = lambda comment_val: comment_val.dump(self.dump_value)
        self.dump_funcs[PurePath] = self._dump_pathlib_path

    @staticmethod
    def _dump_pathlib_path(v: PurePath):
        """Translate :py:class:`PurePath` to string and dump."""
        return _dump_str(str(v))

    def dump_value(self, v: TOML_VALUE):
        """Support :py:class:`Path` decoding by prefixing a :py:class:`PurePath` string with a special marker."""
        if isinstance(v, PurePath):
            if isinstance(v, Path):
                v = v.resolve()
            v = f'{SPECIAL_PATH_PREFIX}{v}'
        return super().dump_value(v=v)


class TomlFile:
    """Object that manages the getting and setting of TOML configurations.

    Houses an EventBus that allows you to subscribe Callables to changes in configuration.
    """

    def __init__(self, path: Path | str, default: dict[str, TOML_VALUE] | None = None) -> None:
        self.path = path
        # FIXME: Default not working as expected during import
        self._data: dict[str, TOML_VALUE | CommentValue] = default if default is not None else {}
        self._event_subscribers: dict[str, list[tuple[
            Callable[[...], None],  # Callable to call
            tuple[...],  # positional arguments
            dict[str, Any]  # keyword arguments
        ]]] = {}
        if self.reload() is False:
            warnings.warn(f'Could not load TOML file {self.path} on initialization.')

    def __getitem__(self, key: str) -> TOML_VALUE | None:
        return self.get_key(key)

    def __setitem__(self, key: str, value: TOML_VALUE) -> None:
        self.set_key(key, value)

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def _search_scope(self, path: str, mode: str) -> tuple[dict[str, TOML_VALUE | CommentValue], str]:
        """Search data for the given path to the value, and if found, return the scope and the key that path belongs to.

        :param path: Path to search data for.
        :param mode: Mode that determines which exceptions to raise.
        :return: Tuple containing the scope where the value is found, and the value key to access.
        :raises KeyError: If mode is 'set' and path is a table OR if mode is 'get' and path doesn't exist.
        :raises ValueError: If path is an empty string.
        """
        if not path:
            raise ValueError('Path can not be an empty string.')

        scope = self._data
        paths = path.split('/')

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

    def get_key(self, key: str) -> TOML_VALUE | None:
        """Get a key from path. Searches with each '/' defining a new table to check.

        Calls event $get:{key}.

        :param key: Key to get value from.
        """
        scope, path = self._search_scope(key, 'get')

        for sub in self._event_subscribers.get(f'$get:{key}', []):
            sub[0](*sub[1], **sub[2])

        # Get value from CommentValue
        val = scope.get(path)
        if isinstance(val, CommentValue):
            val = val.val

        return val

    def set_key(self, key: str, value: TOML_VALUE, comment: str | None = None) -> None:
        """Set a key at path. Searches with each '/' defining a new table to check.

        Calls event $set:{key}.

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

        for sub in self._event_subscribers.get(f'$set:{key}', []):
            sub[0](*sub[1], **sub[2])

    def save(self) -> bool:
        """Save current settings to self.path."""
        return self.export_to(self.path)

    def reload(self) -> bool:
        """Reset settings to settings stored in self.path."""
        for sub in self._event_subscribers.get('$reload', []):
            sub[0](*sub[1], **sub[2])
        return self.import_from(self.path, update=True)

    def export_to(self, path: Path | str) -> bool:
        """Export internal dictionary as a TOML file to path.

        :return: True if successful, otherwise False.
        """
        # TODO: upgrade similarly to import_from
        path = Path(path)  # Make sure path is of type Path
        if path.parent.is_dir():
            with path.open(mode='w', encoding='utf8') as file:
                toml.dump(self._data, file, encoder=BetterTomlEncoder())

            return True
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

            except (LookupError, OSError, TomlDecodeError):
                pass  # Pass to end of function, to fail.

            else:
                # Execute all events subscribed to $set
                for name, event in self._event_subscribers.items():
                    if name.startswith('$set'):
                        for sub in event:
                            sub[0](*sub[1], **sub[2])

                return True

        # If failed:
        for sub in self._event_subscribers.get('$fail:import', []):
            sub[0](*sub[1], **sub[2])
        return False

    def hook_event(self, key: str, f: Callable, *args, **kwargs) -> None:
        """Hook a Callable to an event. The callable will be called with args and kwargs when the event is activated."""
        subscribers = self._event_subscribers.get(key, [])
        subscribers.append((f, args, kwargs))
        self._event_subscribers[key] = subscribers
