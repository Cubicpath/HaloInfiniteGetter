###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utility functions for hi_getter."""
from __future__ import annotations

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
        # Don't include testing extras
        if include_extras and requirement.split('extra ==')[-1].strip().strip('"') in ('dev', 'develop', 'development', 'test', 'testing'):
            continue

        split_char = 0
        for char in requirement:
            if not char.isalnum() and char not in ('-', '_'):
                break
            split_char += 1

        req_names.append(requirement[:split_char])

    return req_names


def current_requirement_versions(package: str, include_extras: bool = False) -> dict[str, str]:
    """Return the current versions of the installed requirements for the given package.

    :param package: Package name to search
    :param include_extras: Whether to include packages installed with extras
    :return: dict mapping package names to their version string.
    """
    from importlib.metadata import version

    return {name: version(name) for name in current_requirement_names(package, include_extras) if has_package(name)}


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
        with path.open(mode='w', encoding=encoding or default_encoding) as file:
            json.dump(data, file, indent=2)


def get_desktop_path() -> Path | None:
    """Cross-platform utility to obtain the path to the desktop.

    This function is cached after the first call.

    * On Windows, this returns the path found in the registry, or the default ~/Desktop if the registry could not be read from.

    * On Linux and macOS, this returns the DESKTOP value in ~/.config/user-dirs.dirs file, or the default ~/Desktop.

    :return: Path to the user's desktop or None if not found.
    """
    import os
    import sys

    # Assume that once found, the desktop path does not change
    if hasattr(get_desktop_path, '__cached__'):
        return get_desktop_path.__cached__

    platform: str = sys.platform.lower()
    desktop:  Path | None = None

    if platform == 'win32':
        shell_folder_key: str = r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
        desktop = Path.home() / 'Desktop'

        try:
            val = get_winreg_value(shell_folder_key, 'Desktop')

            # Make sure the path is resolved
            desktop = Path(val).resolve(strict=True).absolute()

        except (ImportError, OSError):
            pass  # Return the default windows path if the registry couldn't be read.

    elif platform.startswith('linux') or platform == 'darwin':
        home: Path = Path.home() or Path(os.getenv('HOME', None))
        desktop: Path = home / 'Desktop'

        # If desktop is defined in user's config, use that
        dir_file: Path = home / '.config/user-dirs.dirs'
        if dir_file.is_file():
            with dir_file.open(mode='r', encoding='utf8') as f:
                text: list[str] = f.readlines()

            for line in text:
                # Read the DESKTOP variable's value and evaluate it
                if 'DESKTOP' in line:
                    line = line.replace('$HOME', str(home))[:-1]
                    config_val = line.split('=')[1].strip('\'\"')
                    desktop = Path(config_val)

    get_desktop_path.__cached__ = desktop
    return desktop


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


def get_start_menu_path() -> Path | None:
    """Cross-platform utility to obtain the path to the Start Menu or equivalent.

    This function is cached after the first call.

    * On Windows, this returns the main Start Menu folder, so it is recommended that you use the "Programs" sub-folder for adding shortcuts.

    * On Linux, this returns the ~/.local/share/applications directory.

    * On macOS, this returns None.

    :return: Path to the Start Menu or None if not found.
    """
    import os
    import sys

    # Assume that once found, the start menu path does not change
    if hasattr(get_start_menu_path, '__cached__'):
        return get_start_menu_path.__cached__

    platform:   str = sys.platform.lower()
    start_menu: Path | None = None

    if platform == 'win32':
        shell_folder_key: str = r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
        start_menu = Path.home() / 'AppData/Roaming/Microsoft/Windows/Start Menu'

        try:
            val = get_winreg_value(shell_folder_key, 'Start Menu')

            # Make sure the path is resolved
            start_menu = Path(val).resolve(strict=True).absolute()

        except (ImportError, OSError):
            pass  # Return the default windows path if the registry couldn't be read.

    elif platform.startswith('linux'):
        home: Path = Path.home() or Path(os.getenv('HOME', None))

        start_menu = home / '.local/share/applications'

    get_start_menu_path.__cached__ = start_menu
    return start_menu


def get_winreg_value(key_name: str, value_name: str) -> str | int | bytes | list | None:
    """Get a value from the Windows registry.

    :param key_name: The registry key to read. The parent key must be the name of a defined winreg constant.
    :param value_name: The value to read.
    :return: The value, or None if not found.
    :raises AttributeError: If the parent_key is not a defined winreg constant.
    :raises ImportError: If winreg is not available.
    :raises OSError: If the registry key could not be read.
    """
    from os.path import expandvars

    try:
        import winreg
    except ImportError as e:
        raise ImportError('winreg is required to use this function.') from e

    parent_key: int = getattr(winreg, key_name.split('\\')[0])
    sub_key:    str = '\\'.join(key_name.split('\\')[1:])
    if not isinstance(parent_key, int):
        raise AttributeError('parent_key is not a defined winreg constant.')

    reg_key = winreg.OpenKey(parent_key, sub_key, 0, winreg.KEY_QUERY_VALUE)
    val, reg_type = winreg.QueryValueEx(reg_key, value_name)

    reg_key.Close()

    # Expand environment variables
    if reg_type == winreg.REG_EXPAND_SZ:
        val = expandvars(val)

    return val


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
        from ctypes import windll

        # File flags are a 32-bit bitarray, the "hidden" attribute is the 2nd least significant bit
        FILE_ATTRIBUTE_HIDDEN = 0b00000000000000000000000000000010

        # bitarray for boolean flags representing file attributes
        current_attributes: int = windll.kernel32.GetFileAttributesW(file_path)
        if not unhide:
            # Add hide attribute to bitarray using bitwise OR
            # 0b00000000 -> 0b00000010 ---- 0b00000110 -> 0b00000110
            merged_attributes: int = current_attributes | FILE_ATTRIBUTE_HIDDEN
            return windll.kernel32.SetFileAttributesW(file_path, merged_attributes)
        else:
            # Remove hide attribute from bitarray if it exists
            # Check with bitwise AND; Remove with bitwise XOR
            # 0b00000100 -> 0b00000100 ---- 0b00000110 -> 0b00000100
            # Only Truthy returns (which contain the hidden attribute) will subtract from the bitarray
            is_hidden = bool(current_attributes & FILE_ATTRIBUTE_HIDDEN)
            if is_hidden:
                subtracted_attributes: int = current_attributes ^ FILE_ATTRIBUTE_HIDDEN
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
