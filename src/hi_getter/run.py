###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Initialize values and runs the application."""
import os
import sys
from sys import platform
from typing import Final

import toml
from PySide6.QtCore import *
from toml.decoder import CommentValue

from ._version import __version__
from .client import Client
from .constants import *
from .gui import AppWindow
from .gui import GetterApp
from .tomlfile import *

__all__ = (
    'run',
)

# TODO: Add ability to run using pyw


def _make_comment_val(val: TOML_VALUE, comment: str, new_line=False) -> CommentValue:
    return CommentValue(val=val, comment=f'# {comment}', beginline=new_line, _dict=dict)


SETTINGS_PATH = (CONFIG_PATH / 'settings.toml')

DEFAULT_SETTINGS = {
    'language': 'en-US',
    'gui': {
        'window': {
            'x_size': _make_comment_val(900, 'Minimum value of 100'),
            'y_size': _make_comment_val(500, 'Minimum value of 100')
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
            'aspect_ratio_mode': _make_comment_val(1, '0: Ignore | 1: Keep | 2: Expanding'),
            'transformation_mode': _make_comment_val(0, '0: Fast | 1: Smooth')
        },
        'text_output': {
            'line_wrap_mode': _make_comment_val(1, '0: No Wrap | 1: Widget | 2: Fixed Pixel | 4: Fixed Column')
        }
    }
}
"""Default settings to use in config."""


def _create_new_paths() -> None:
    """Create files and paths if they do not exist."""
    if not CONFIG_PATH.is_dir():
        os.makedirs(CONFIG_PATH)
    if not SETTINGS_PATH.is_file():
        with SETTINGS_PATH.open(mode='w', encoding='utf8') as file:
            toml.dump(DEFAULT_SETTINGS, file, encoder=BetterTomlEncoder())


def _patch_windows_taskbar_icon() -> None:
    """Override Python's default Windows taskbar icon with the custom one set by the app window."""
    if platform == 'win32':
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(f'cubicpath.hi_getter.app.{__version__}')


def run(*args, **kwargs) -> int:
    """Run the program.

    Args are passed to a QApplication instance.
    Kwargs are handled here.
    """
    _create_new_paths()
    _patch_windows_taskbar_icon()

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
