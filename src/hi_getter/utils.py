###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utils for hi_getter."""
import json
import os
import platform
from collections.abc import Iterable
from collections.abc import Mapping
from http import HTTPStatus
from pathlib import Path

from ._version import __version__
from .tomlfile import CommentValue
from .tomlfile import TOML_VALUE

__all__ = (
    'dump_data',
    'HTTP_CODE_MAP',
    'make_comment_val',
    'patch_windows_taskbar_icon',
    'unique_values',
)

# pylint: disable=not-an-iterable

HTTP_CODE_MAP = {status.value: (status.phrase, status.description) for status in HTTPStatus}


def dump_data(path: Path | str, data: bytes | dict | str, encoding: str | None = None) -> None:
    """Dump data to path as a file."""
    default_encoding = 'utf8'
    path = Path(path)
    if not path.parent.exists():
        os.makedirs(path.parent)

    if isinstance(data, str):
        path.write_text(data, encoding=encoding or default_encoding)
    elif isinstance(data, bytes):
        if encoding is not None:
            data = data.decode(encoding=encoding)
            path.write_text(data, encoding=encoding)
        else:
            path.write_bytes(data)
    elif isinstance(data, dict):
        with path.open('w', encoding=encoding or default_encoding) as file:
            json.dump(data, file, indent=2)


def make_comment_val(val: TOML_VALUE, comment: str, new_line=False) -> CommentValue:
    """Build and return :py:class:`CommentValue`."""
    return CommentValue(val=val, comment=f'# {comment}', beginline=new_line, _dict=dict)


def patch_windows_taskbar_icon() -> None:
    """Override Python's default Windows taskbar icon with the custom one set by the app window."""
    if platform == 'win32':
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(f'cubicpath.hi_getter.app.{__version__}')


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
