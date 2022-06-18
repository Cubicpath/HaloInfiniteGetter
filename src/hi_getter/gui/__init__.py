###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Relative package containing custom GUI elements."""
# TODO: Create custom QMessageBox implementation for selectable text
# TODO: Move each independent widget to its own module, grouping them in packages by functionality
# TODO: Add relative anchors for ReadmeViewer
# TODO: Zoom In/Out Buttons for LicenseViewer
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

from .app import *
from .menus import *
from .widgets import *
from .windows import *
