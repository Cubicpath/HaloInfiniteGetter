###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Initialize values and runs the application."""
import os
import sys
from typing import Final

import toml
from PySide6.QtCore import *

from ._version import __version__
from .client import Client
from .constants import *
from .gui import *
from .tomlfile import *
from .utils import *

__all__ = (
    'run',
)

SETTINGS_PATH = (CONFIG_PATH / 'settings.toml')

DEFAULT_SETTINGS = {
    'language': 'en-US',
    'gui': {
        'window': {
            'x_size': make_comment_val(900, 'Minimum value of 100'),
            'y_size': make_comment_val(500, 'Minimum value of 100')
        },
        'themes': {
            'selected': 'light',
            'dark': {
                'display_name': 'Breeze Dark',
                'path': RESOURCE_PATH / 'themes/dark'
            },
            'light': {
                'display_name': 'Breeze Light',
                'path': RESOURCE_PATH / 'themes/light'
            }
        },
        'media_output': {
            'aspect_ratio_mode': make_comment_val(1, '0: Ignore | 1: Keep | 2: Expanding'),
            'transformation_mode': make_comment_val(0, '0: Fast | 1: Smooth')
        },
        'text_output': {
            'line_wrap_mode': make_comment_val(1, '0: No Wrap | 1: Widget | 2: Fixed Pixel | 4: Fixed Column')
        }
    }
}
"""Default settings to use in config."""


def _create_paths() -> None:
    """Create files and paths if they do not exist."""
    for dir_path in (CACHE_PATH, CONFIG_PATH):
        if not dir_path.is_dir():
            os.makedirs(dir_path)
    if not SETTINGS_PATH.is_file():
        with SETTINGS_PATH.open(mode='w', encoding='utf8') as file:
            toml.dump(DEFAULT_SETTINGS, file, encoder=BetterTomlEncoder())


def run(*args, **kwargs) -> int:
    """Run the program.

    Args are passed to a QApplication instance.
    Kwargs are handled here.
    """
    _create_paths()
    patch_windows_taskbar_icon(f'cubicpath.{__package__}.app.{__version__}')

    APP:        Final[GetterApp] = GetterApp(list(args), TomlFile(SETTINGS_PATH, default=DEFAULT_SETTINGS))
    APP.load_themes()

    CLIENT:     Final[Client] = kwargs.pop('client', Client())
    SIZE:       Final[QSize] = QSize(
        # Size to use, with a minimum of 100x100.
        max(kwargs.pop('x_size', APP.settings['gui/window/x_size']), 100),
        max(kwargs.pop('y_size', APP.settings['gui/window/y_size']), 100)
    )
    WINDOW:     Final[AppWindow] = AppWindow(CLIENT, APP, SIZE)
    WINDOW.show()
    return APP.exec()


if __name__ == '__main__':
    run(sys.argv)
