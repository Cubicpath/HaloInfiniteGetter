###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Relative package containing all things handling GUI elements."""
# TODO: Create custom QMessageBox implementation for selectable text
# TODO: Add relative anchors for ReadmeViewer
# TODO: Add fading in/out animations to menus

__all__ = (
    'AppWindow',
    'ExceptionLogger',
    'ExceptionReporter',
    'ExternalTextBrowser',
    'FileContextMenu',
    'GetterApp',
    'HelpContextMenu',
    'HistoryComboBox',
    'LicenseViewer',
    'PasteLineEdit',
    'ReadmeViewer',
    'SettingsWindow',
    'Theme',
    'ToolsContextMenu',
)

from .app import GetterApp
from .app import Theme
from .menus import FileContextMenu
from .menus import HelpContextMenu
from .menus import ToolsContextMenu
from .widgets import ExceptionLogger
from .widgets import ExternalTextBrowser
from .widgets import HistoryComboBox
from .widgets import PasteLineEdit
from .windows import AppWindow
from .windows import ExceptionReporter
from .windows import LicenseViewer
from .windows import ReadmeViewer
from .windows import SettingsWindow
