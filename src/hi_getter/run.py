###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Initialize values and runs the application. :py:func:`main` acts as an entry-point."""
from __future__ import annotations

__all__ = (
    'main',
)

import sys
from typing import Final

from PySide6.QtCore import *

from ._version import __version__
from .exceptions import ExceptionHook
from .gui import AppWindow
from .gui import GetterApp
from .utils.system import patch_windows_taskbar_icon


def main(*args, **kwargs) -> int:
    """Run the program. GUI script entrypoint.

    Args are passed to a QApplication instance.
    Kwargs are handled here.
    """
    patch_windows_taskbar_icon(f'cubicpath.{__package__}.app.{__version__}')

    with ExceptionHook():
        APP:        Final[GetterApp] = GetterApp(list(args))
        SIZE:       Final[QSize] = QSize(
            # Size to use, with a minimum of 100x100.
            max(kwargs.pop('x_size', APP.settings['gui/window/x_size']), 100),
            max(kwargs.pop('y_size', APP.settings['gui/window/y_size']), 100)
        )
        WINDOW:     Final[AppWindow] = AppWindow(SIZE)
        WINDOW.show()
        return APP.exec()


if __name__ == '__main__':
    main(*sys.argv)
