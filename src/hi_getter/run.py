###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Initialize values and runs the application. :py:func:`main` acts as an entry-point."""

__all__ = (
    'DEFAULT_SETTINGS',
    'main',
)

import os
import sys
from pathlib import Path
from typing import Final

import toml
from PySide6.QtCore import *

from ._version import __version__
from .constants import *
from .exceptions import ExceptionHook
from .gui import *
from .tomlfile import *
from .utils import *

_DEFAULTS_FILE: Final[Path] = HI_RESOURCE_PATH / 'default_settings.toml'
_LAUNCHED_FILE: Final[Path] = HI_CONFIG_PATH / '.LAUNCHED'
_SETTINGS_FILE: Final[Path] = HI_CONFIG_PATH / 'settings.toml'

# Read default settings file
DEFAULT_SETTINGS: Final[TomlTable] = toml.loads(
    _DEFAULTS_FILE.read_text(encoding='utf8').replace(
        '{HI_RESOURCE_PATH}', str(HI_RESOURCE_PATH.resolve()).replace('\\', '\\\\')
    ), decoder=PathTomlDecoder()
)


def _create_paths() -> None:
    """Create files and directories if they do not exist."""
    for dir_path in (HI_CACHE_PATH, HI_CONFIG_PATH):
        if not dir_path.is_dir():
            os.makedirs(dir_path)

    if not _LAUNCHED_FILE.is_file():
        # Create first-launch marker
        _LAUNCHED_FILE.touch()
        hide_windows_file(_LAUNCHED_FILE)

    if not _SETTINGS_FILE.is_file():
        # Write default_settings to user's SETTINGS_FILE
        with _SETTINGS_FILE.open(mode='w', encoding='utf8') as file:
            toml.dump(DEFAULT_SETTINGS, file, encoder=PathTomlEncoder())


def main(*args, **kwargs) -> int:
    """Run the program. GUI script entrypoint.

    Args are passed to a QApplication instance.
    Kwargs are handled here.
    """
    # Check if launched marker exists
    first_launch = not _LAUNCHED_FILE.is_file()

    _create_paths()
    patch_windows_taskbar_icon(f'cubicpath.{__package__}.app.{__version__}')

    with ExceptionHook():
        APP:        Final[GetterApp] = GetterApp(list(args), TomlFile(_SETTINGS_FILE, default=DEFAULT_SETTINGS), first_launch=first_launch)
        APP.load_env(verbose=True)

        SIZE:       Final[QSize] = QSize(
            # Size to use, with a minimum of 100x100.
            max(kwargs.pop('x_size', APP.settings['gui/window/x_size']), 100),
            max(kwargs.pop('y_size', APP.settings['gui/window/y_size']), 100)
        )
        WINDOW:     Final[AppWindow] = AppWindow(SIZE)
        WINDOW.show()
        return APP.exec()


if __name__ == '__main__':
    main(sys.argv)
