###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utility functions for hi_getter."""

__all__ = (
    'current_requirement_licenses',
    'current_requirement_names',
    'current_requirement_versions',
    'dump_data',
    'get_parent_doc',
    'has_package',
    'hide_windows_file',
    'patch_windows_taskbar_icon',
    'unique_values',
)

from collections.abc import Iterable
from collections.abc import Mapping
from pathlib import Path


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


def dump_data(path: Path | str, data: bytes | dict | str, encoding: str | None = None) -> None:
    """Dump data to path as a file."""
    import json
    import os

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
    """Get the nearest parent documentation using the given :py:class:`type`'s mro.

    :return The closest docstring for an object's class, None if not found.
    """
    doc = None
    for parent in __type.__mro__:
        doc = parent.__doc__
        if doc:
            break
    return doc


def has_package(package: str) -> bool:
    """Check if the given package is available.

    :param package: Package name to search; hyphen-insensitive
    :return: Whether the given package name is installed to the current environment.
    """
    from pkg_resources import WorkingSet

    for pkg in WorkingSet():
        if package.replace('-', '_') == pkg.project_name.replace('-', '_'):
            return True
    return False


def hide_windows_file(file_path: Path | str, *, unhide: bool = False) -> int | None:
    """Hide an existing Windows file. If not running windows, do nothing.

    Use unhide kwarg to reverse the operation

    :param file_path: Absolute or relative path to hide.
    :param unhide: Unhide a hidden file in Windows.
    :return: None if not on Windows, else if the function succeeds, the return value is nonzero.
    """
    import sys

    # Resolve string path to use with kernel32
    file_path = str(Path(file_path).resolve())
    if sys.platform == 'win32':
        import win32con
        from ctypes import windll

        # bitarray for boolean flags representing file attributes
        current_attributes: int = windll.kernel32.GetFileAttributesW(file_path)
        if not unhide:
            # Add hide attribute to bitarray using bitwise OR
            # 0b00000000 -> 0b00000010 ---- 0b00000110 -> 0b00000110
            merged_attributes: int = current_attributes | win32con.FILE_ATTRIBUTE_HIDDEN
            return windll.kernel32.SetFileAttributesW(file_path, merged_attributes)
        else:
            # Remove hide attribute from bitarray if it exists
            # Check with bitwise AND; Remove with bitwise XOR
            # 0b00000100 -> 0b00000100 ---- 0b00000110 -> 0b00000100
            # Only Truthy returns (which contain the hidden attribute) will subtract from the bitarray
            is_hidden = bool(current_attributes & win32con.FILE_ATTRIBUTE_HIDDEN)
            if is_hidden:
                subtracted_attributes: int = current_attributes ^ win32con.FILE_ATTRIBUTE_HIDDEN
                return windll.kernel32.SetFileAttributesW(file_path, subtracted_attributes)


def patch_windows_taskbar_icon(app_id: str = '') -> int | None:
    """Override Python's default Windows taskbar icon with the custom one set by the app window.

    See https://docs.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-setcurrentprocessexplicitappusermodelid for more information.

    :param app_id: Pointer to the AppUserModelID to assign to the current process.
    :return: None if not on Windows, S_OK if this function succeeds. Otherwise, it returns an HRESULT error code.
    """
    import sys

    if sys.platform == 'win32':
        from ctypes import windll
        return windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


def unique_values(data: Iterable) -> set:
    """Recursively get all values in any Iterables. For Mappings, ignore keys and only remember values.

    :return Set containing all unique non-iterable values.
    """
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
