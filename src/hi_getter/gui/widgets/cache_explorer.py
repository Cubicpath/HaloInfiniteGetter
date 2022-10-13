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


class _ColumnContextMenu(QMenu):
    def __init__(self, parent: CacheExplorer):
        super().__init__(parent)

        enabled_map = [parent.isColumnHidden(i) for i in range(parent.model().columnCount())]

        icons = (
            # Not Hidden
            app().get_theme_icon('checkbox_checked') or
            self.style().standardIcon(QStyle.SP_DialogApplyButton),

            # Hidden
            app().get_theme_icon('checkbox_unchecked') or
            self.style().standardIcon(QStyle.SP_DialogCancelButton),
        )

        init_objects({
            (name := QAction(self)): {
                'disabled': not parent.isColumnHidden(0),
                'text': tr('gui.cache_explorer.columns.name'),
                'icon': icons[enabled_map[0]],
                'triggered': DeferredCallable(parent.setColumnHidden, 0, not parent.isColumnHidden(0))
            },

            (file_size := QAction(self)): {
                'text': tr('gui.cache_explorer.columns.file_size'),
                'icon': icons[enabled_map[1]],
                'triggered': DeferredCallable(parent.setColumnHidden, 1, not parent.isColumnHidden(1))
            },

            (file_type := QAction(self)): {
                'text': tr('gui.cache_explorer.columns.file_type'),
                'icon': icons[enabled_map[2]],
                'triggered': DeferredCallable(parent.setColumnHidden, 2, not parent.isColumnHidden(2))
            },

            (date_modified := QAction(self)): {
                'text': tr('gui.cache_explorer.columns.date_modified'),
                'icon': icons[enabled_map[3]],
                'triggered': DeferredCallable(parent.setColumnHidden, 3, not parent.isColumnHidden(3))
            },
        })

        section_map = {
            'Columns': (name, file_size, file_type, date_modified),
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)


class _CachedFileContextMenu(QMenu):
    """Context menu that shows actions to manipulate files."""

    def __init__(self, parent: CacheExplorer, index: QModelIndex):
        super().__init__(parent)

        file_path = Path(parent.model().filePath(index))
        if not (dir_path := file_path).is_dir():
            dir_path = file_path.parent

        init_objects({
            (open_in_view := QAction(self)): {
                'disabled': file_path.is_dir(),
                'text': tr('gui.menus.cache_explorer.open_in_view'),
                'icon': self.style().standardIcon(QStyle.SP_DesktopIcon),
                'triggered': DeferredCallable(
                    parent.openFileInView.emit, file_path.as_posix()
                )
            },

            (open_in_default_app := QAction(self)): {
                'disabled': file_path.is_dir(),
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

            (expand_this := QAction(self)): {
                'disabled': file_path.is_file(),
                'text': tr('gui.menus.cache_explorer.expand_this'),
                'triggered': DeferredCallable(parent.expand, index)
            },

            (expand_recursively := QAction(self)): {
                'disabled': file_path.is_file(),
                'text': tr('gui.menus.cache_explorer.expand_recursively'),
                'triggered': DeferredCallable(parent.expandRecursively, index)
            },

            (expand_all := QAction(self)): {
                'text': tr('gui.menus.cache_explorer.expand_all'),
                'triggered': parent.expandAll
            },

            (collapse_this := QAction(self)): {
                'disabled': file_path.is_file(),
                'text': tr('gui.menus.cache_explorer.collapse_this'),
                'triggered': DeferredCallable(parent.collapse, index)
            },

            (collapse_all := QAction(self)): {
                'text': tr('gui.menus.cache_explorer.collapse_all'),
                'triggered': parent.collapseAll
            },
        })

        section_map = {
            'Open': (open_in_view, open_in_default_app, open_in_explorer),
            'Expand': (expand_this, expand_recursively, expand_all),
            'Collapse': (collapse_this, collapse_all)
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
                'indentation': 12,
                'contextMenuPolicy': Qt.CustomContextMenu,
                'customContextMenuRequested': self.on_custom_context_menu,
                'doubleClicked': self.on_double_click
            },

            self.header(): {
                'size': {'fixed': (None, 26)},
                'sectionsClickable': True,
                'contextMenuPolicy': Qt.CustomContextMenu,
                'customContextMenuRequested': self.on_header_custom_context_menu
            }
        })

        for index in (1, 2, 3):  # SIZE, FILE TYPE, DATE MODIFIED
            self.hideColumn(index)

    def expandAll(self) -> None:
        """Call super().expandall ~50 times."""
        timer = QTimer(self)
        timer.timeout.connect(DeferredCallable(super().expandAll))
        timer.start(5)

        timer2 = QTimer(self)
        timer2.setSingleShot(True)
        timer2.timeout.connect(timer.stop)
        timer2.start(500)

    def expandRecursively(self, *args, **kwargs) -> None:
        """Call super().expandRecursively ~50 times."""
        timer = QTimer(self)
        timer.timeout.connect(DeferredCallable(super().expandRecursively, *args, **kwargs))
        timer.start(5)

        timer2 = QTimer(self)
        timer2.setSingleShot(True)
        timer2.timeout.connect(timer.stop)
        timer2.start(500)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Resize "Name" column on click/expansion."""
        super().mousePressEvent(event)
        self.resizeColumnToContents(0)

    def on_header_custom_context_menu(self, point: QPoint) -> None:
        """Function called when the customContextMenuRequested signal is emitted.

        :param point: The point to place the context menu.
        """
        index = self.indexAt(point)

        if index.isValid():
            menu = _ColumnContextMenu(self)
            menu.setAttribute(Qt.WA_DeleteOnClose)

            menu.move(self.viewport().mapToGlobal(point))
            menu.show()

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
