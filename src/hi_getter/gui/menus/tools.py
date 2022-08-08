###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Tools menu implementation."""
from __future__ import annotations

__all__ = (
    'ToolsContextMenu',
)

import sys
from pathlib import Path

from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ...utils.system import create_shortcut
from ..app import app
from ..app import tr


# noinspection PyArgumentList
class ToolsContextMenu(QMenu):
    """Context menu for tools."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`ToolsContextMenu`."""
        super().__init__(parent)

        shortcut_tool: QAction = QAction(
            self.style().standardIcon(QStyle.SP_DesktopIcon),
            tr('gui.menus.tools.create_shortcut'), self, triggered=self.create_app_shortcut
        )

        exception_reporter: QAction = QAction(
            parent.exception_reporter.logger.icon(),
            tr('gui.menus.tools.exception_reporter'), self, triggered=parent.exception_reporter.show
        )

        section_map = {
            'Tools': (shortcut_tool, exception_reporter)
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

    @staticmethod
    def create_app_shortcut() -> None:
        """Create shortcut for starting program."""
        exec_path = Path(sys.executable)

        desktop_button = QPushButton(tr('gui.menus.tools.create_shortcut.only_desktop'))
        start_menu_button = QPushButton(tr('gui.menus.tools.create_shortcut.only_start_menu'))
        both_button = QPushButton(tr('gui.menus.tools.create_shortcut.both'))

        if (response := app().show_dialog(
            'questions.create_shortcut', None, [
                    (desktop_button, QMessageBox.AcceptRole),
                    (start_menu_button, QMessageBox.AcceptRole),
                    (both_button, QMessageBox.AcceptRole),
                    QMessageBox.StandardButton.Cancel
            ], default_button=QMessageBox.StandardButton.Cancel
        )).role == QMessageBox.RejectRole:
            return

        do_desktop = response.button == desktop_button or response.button == both_button
        do_start_menu = response.button == start_menu_button or response.button == both_button

        name = exec_path.with_suffix('').name
        if not name.endswith('w'):
            name += 'w'
        shortcut_path = exec_path.with_name(f'{name}{exec_path.suffix}')

        create_shortcut(target=shortcut_path, arguments=f'-m {HI_PACKAGE_NAME}',
                        name=tr('app.name'), description=tr('app.description'),
                        icon=HI_RESOURCE_PATH / 'icons/hi.ico', terminal=False,
                        desktop=do_desktop, start_menu=do_start_menu)
