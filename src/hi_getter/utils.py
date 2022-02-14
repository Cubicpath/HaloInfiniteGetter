###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utils for hi_getter."""
import json
import os
from collections.abc import Iterable
from collections.abc import Mapping
from http import HTTPStatus
from pathlib import Path

__all__ = (
    'dump_data',
    'HTTP_CODE_MAP',
    'unique_values',
)

# pylint: disable=not-an-iterable
HTTP_CODE_MAP = {status.value: (status.phrase, status.description) for status in HTTPStatus}


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
