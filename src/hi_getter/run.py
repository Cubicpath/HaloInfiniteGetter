###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Initialize values and runs the application."""

__all__ = (
    'run',
)

import os
import sys
from pathlib import Path
from typing import Final

import toml
from PySide6.QtCore import *

from ._version import __version__
from .client import Client
from .constants import *
from .exceptions import ExceptionHook
from .gui import *
from .tomlfile import *
from .utils import *

DEFAULTS_FILE: Final[Path] = HI_RESOURCE_PATH / 'default_settings.toml'
LAUNCHED_FILE: Final[Path] = HI_CONFIG_PATH / '.LAUNCHED'
SETTINGS_FILE: Final[Path] = HI_CONFIG_PATH / 'settings.toml'

# Read default settings file
default_settings: TomlTable = toml.loads(
    DEFAULTS_FILE.read_text(encoding='utf8').replace(
        '{HI_RESOURCE_PATH}', str(HI_RESOURCE_PATH.resolve()).replace('\\', '\\\\')
    ), decoder=PathTomlDecoder()
)


def _create_paths() -> None:
    """Create files and directories if they do not exist."""
    if not LAUNCHED_FILE.is_file():
        # Create first-launch marker
        LAUNCHED_FILE.touch()
        hide_windows_file(LAUNCHED_FILE)

    for dir_path in (HI_CACHE_PATH, HI_CONFIG_PATH):
        if not dir_path.is_dir():
            os.makedirs(dir_path)

    if not SETTINGS_FILE.is_file():
        # Write default_settings to user's SETTINGS_FILE
        with SETTINGS_FILE.open(mode='w', encoding='utf8') as file:
            toml.dump(default_settings, file, encoder=PathTomlEncoder())


def run(*args, **kwargs) -> int:
    """Run the program. GUI script entrypoint.

    Args are passed to a QApplication instance.
    Kwargs are handled here.
    """
    # Check if launched marker exists
    first_launch = not LAUNCHED_FILE.is_file()

    _create_paths()
    patch_windows_taskbar_icon(f'cubicpath.{__package__}.app.{__version__}')

    with ExceptionHook():
        APP:        Final[GetterApp] = GetterApp(list(args), TomlFile(SETTINGS_FILE, default=default_settings), first_launch=first_launch)
        APP.load_themes()

        CLIENT:     Final[Client] = kwargs.pop('client', Client())
        SIZE:       Final[QSize] = QSize(
            # Size to use, with a minimum of 100x100.
            max(kwargs.pop('x_size', APP.settings['gui/window/x_size']), 100),
            max(kwargs.pop('y_size', APP.settings['gui/window/y_size']), 100)
        )
        WINDOW:     Final[AppWindow] = AppWindow(CLIENT, SIZE)
        WINDOW.show()
        return APP.exec()


if __name__ == '__main__':
    run(sys.argv)
