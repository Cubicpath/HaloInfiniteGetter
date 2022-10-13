###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""CacheExplorer implementation."""
from __future__ import annotations

__all__ = (
    'CacheExplorer',
)

from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ...models import DeferredCallable
from ...utils.gui import init_objects
from ..app import app
from ..app import tr


class _CachedFileContextMenu(QMenu):
    """Context menu that shows actions to manipulate files."""

    def __init__(self, parent: CacheExplorer, index: QModelIndex):
        super().__init__(parent)

        file_path = Path(parent.model().filePath(index))
        if not (dir_path := file_path).is_dir():
            dir_path = file_path.parent

        init_objects({
            (open_in_view := QAction(self)): {
                'text': tr('gui.menus.cache_explorer.open_in_view'),
                'icon': self.style().standardIcon(QStyle.SP_DesktopIcon),
                'triggered': DeferredCallable(
                    parent.openFileInView.emit, file_path.as_posix()
                )
            },

            (open_in_default_app := QAction(self)): {
                'text': tr('gui.menus.cache_explorer.open_in_default_app'),
                'icon': self.style().standardIcon(QStyle.SP_DesktopIcon),
                'triggered': DeferredCallable(
                    QDesktopServices.openUrl, QUrl(file_path.as_uri())
                )
            },

            (open_in_explorer := QAction(self)): {
                'text': tr('gui.menus.cache_explorer.view_in_explorer'),
                'icon': app().get_theme_icon('dialog_open') or app().icon_store['folder'],
                'triggered': DeferredCallable(
                    QDesktopServices.openUrl, QUrl(dir_path.as_uri())
                )
            },
        })

        section_map = {
            'Open': (open_in_view, open_in_default_app, open_in_explorer)
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)


class CacheExplorer(QTreeView):
    """:py:class:`QTreeView` used to interact with the app's cache directory.

    Has a native :py:class:`QFileSystemModel` and item context menu.
    """
    openFileInView = Signal(str, name='openFileInView')

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.customContextMenuRequested.connect(self.on_custom_context_menu)
        self.doubleClicked.connect(self.on_double_click)
        self.openFileInView.connect(print)

        init_objects({
            (model := QFileSystemModel(self)): {
                'readOnly': True,
                'rootPath': str(HI_CACHE_PATH.absolute()),
                'nameFilters': [f'*.{ext}' for ext in SUPPORTED_IMAGE_EXTENSIONS],
                'nameFilterDisables': True
            },

            self: {
                'model': model,
                'rootIndex': model.index(str(HI_CACHE_PATH.absolute())),
                'contextMenuPolicy': Qt.CustomContextMenu
            }
        })

        for index in (1, 2, 3):  # SIZE, FILE TYPE, DATE MODIFIED
            self.hideColumn(index)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Resize "Name" column on click/expansion."""
        super().mousePressEvent(event)
        self.resizeColumnToContents(0)

    def on_custom_context_menu(self, point: QPoint) -> None:
        """Function called when the customContextMenuRequested signal is emitted.

        :param point: The point to place the context menu.
        """
        index = self.indexAt(point)

        if index.isValid():
            menu = _CachedFileContextMenu(self, index)
            menu.setAttribute(Qt.WA_DeleteOnClose)

            menu.move(self.viewport().mapToGlobal(point))
            menu.show()

    def on_double_click(self, index: QModelIndex) -> None:
        """Function called when the doubleClicked signal is emitted.

        :param index: The model index which was double-clicked.
        """
        if index.isValid():
            self.openFileInView.emit(self.model().filePath(index))
