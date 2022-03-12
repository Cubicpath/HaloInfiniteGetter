###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utils for hi_getter."""
import json
import os
import sys
from collections.abc import Iterable
from collections.abc import Mapping
from http import HTTPStatus
from pathlib import Path

__all__ = (
    'current_requirement_versions',
    'dump_data',
    'HTTP_CODE_MAP',
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


def patch_windows_taskbar_icon(app_id: str = '') -> None:
    """Override Python's default Windows taskbar icon with the custom one set by the app window."""
    if sys.platform == 'win32':
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


def current_requirement_versions(package: str, include_extras: bool = False) -> dict[str, str]:
    """Return the current versions of the requirements for the given package name."""
    from importlib import metadata
    req_names = []
    for requirement in metadata.requires(package):
        if not include_extras and '; extra' in requirement:
            continue

        split_char = 0
        for char in requirement:
            if not char.isalnum() and char not in ('-', '_'):
                break
            split_char += 1

        req_names.append(requirement[:split_char])
    return {name: metadata.version(name) for name in req_names}


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
