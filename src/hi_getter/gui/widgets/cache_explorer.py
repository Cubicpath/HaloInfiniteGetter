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
from ...events import EventBus
from ...models import DeferredCallable
from ...tomlfile import TomlEvents
from ...utils import init_objects
from ..aliases import app


class _IconProvider(QAbstractFileIconProvider):
    NULL_ICON = QIcon()

    def __init__(self, cache_explorer: CacheExplorer):
        super().__init__()
        self._cache_explorer = cache_explorer
        self._icon_mode: int = app().settings['gui/cache_explorer/icon_mode']  # type: ignore
        self._fallback_provider = QFileIconProvider()

        EventBus['settings'].subscribe(
            self.on_mode_change, TomlEvents.Set,
            event_predicate=lambda event: event.new != event.old and event.key == 'gui/cache_explorer/icon_mode'
        )

    def icon(self, info: QFileInfo | QAbstractFileIconProvider.IconType) -> QIcon:
        """Get the icon for a path using the given information.

        settings['gui/cache_explorer/icon_mode'] changes how this function works.
        0 --- No Icons
        1 --- Default Icons
        2 --- Preview Images

        :param info: File info to associate icon with.
        :return: Icon read from image, or icon from the fallback QFileIconProvider.
        """
        if not self._icon_mode:
            return _IconProvider.NULL_ICON

        if isinstance(info, QFileInfo):
            if info.isDir() and info.fileName() == 'cached_requests':
                return self._cache_explorer.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)

            # Preview images
            if self._icon_mode == 2:
                if info.isFile() and info.suffix().lstrip('.') in SUPPORTED_IMAGE_EXTENSIONS:
                    icon = QIcon()
                    icon.addFile(info.filePath(), QSize(24, 24))
                    return icon

        return self._fallback_provider.icon(info)

    def on_mode_change(self, event: TomlEvents.Set):
        """Set the icon mode to the one selected in settings.

        :raises TypeError: If new value from event is not an int.
        """
        value = event.new
        if not isinstance(value, int):
            raise TypeError(f'Event value "{value}" is not of type {int}.')

        self._icon_mode = value
        self._cache_explorer.model().setIconProvider(self)


class CacheExplorer(QTreeView):
    """:py:class:`QTreeView` used to interact with the app's cache directory.

    Has a native :py:class:`QFileSystemModel` and item context menu.
    """

    openFileInView = Signal(str, name='openFileInView')

    def __init__(self, parent, *args, **kwargs) -> None:
        """Create a new :py:class:`CacheExplorer` widget for viewing cached requests and files."""
        super().__init__(parent, *args, **kwargs)

        init_objects({
            (model := QFileSystemModel(self)): {
                'readOnly': True,
                'rootPath': HI_CACHE_PATH.absolute().as_posix(),
                'iconProvider': _IconProvider(self),
                'nameFilters': [f'*.{ext}' for ext in SUPPORTED_IMAGE_EXTENSIONS],
                'nameFilterDisables': True
            },

            self: {
                'model': model,
                'rootIndex': model.index(HI_CACHE_PATH.absolute().as_posix()),
                'indentation': 12,
                'contextMenuPolicy': Qt.ContextMenuPolicy.CustomContextMenu,
                'customContextMenuRequested': self.on_custom_context_menu,
                'doubleClicked': self.on_double_click
            },

            self.header(): {
                'size': {'fixed': (None, 26)},
                'sectionsClickable': True,
                'contextMenuPolicy': Qt.ContextMenuPolicy.CustomContextMenu,
                'customContextMenuRequested': self.on_header_custom_context_menu
            }
        })

        # Hide all but Name by default
        for index in (1, 2, 3):  # SIZE, FILE TYPE, DATE MODIFIED
            self.hideColumn(index)

    def delete_index(self, index: QModelIndex) -> None:
        """Delete a given index from the file system after prompting the user.

        If the path resolves to a directory, all items in the directory are recursively removed.

        :param index: The index to get the filepath from and delete.
        """
        file_path: Path = Path(self.model().filePath(index))
        path_type: str = 'Folder' if file_path.is_dir() else 'File'

        consent: bool = app().show_dialog(
            'warnings.delete_path', self, (
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            ), default_button=QMessageBox.StandardButton.Cancel,
            title_args=(path_type,),
            description_args=(path_type, file_path)
        ).role == QMessageBox.ButtonRole.AcceptRole

        if consent:
            if file_path.is_dir():
                QDir(file_path).removeRecursively()
            else:
                file_path.unlink()

    def expandAll(self) -> None:
        """Call super().expandall ~50 times."""
        timer = QTimer(self)
        timer.timeout.connect(DeferredCallable(super().expandAll))                           # pyright: ignore[reportGeneralTypeIssues]
        timer.start(5)

        timer2 = QTimer(self)
        timer2.setSingleShot(True)
        timer2.timeout.connect(timer.stop)                                                   # pyright: ignore[reportGeneralTypeIssues]
        timer2.start(500)

    def expandRecursively(self, *args, **kwargs) -> None:
        """Call super().expandRecursively ~50 times."""
        timer = QTimer(self)
        timer.timeout.connect(DeferredCallable(super().expandRecursively, *args, **kwargs))  # pyright: ignore[reportGeneralTypeIssues]
        timer.start(5)

        timer2 = QTimer(self)
        timer2.setSingleShot(True)
        timer2.timeout.connect(timer.stop)                                                   # pyright: ignore[reportGeneralTypeIssues]
        timer2.start(500)

    def model(self) -> QFileSystemModel:
        """:return: The file system model for the CacheExplorer."""
        # pylint: disable=useless-super-delegation
        return super().model()  # type: ignore

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Map keys to actions."""
        super().keyPressEvent(event)

        match event.key():
            case Qt.Key.Key_Delete:
                # Delete Path at Selected Index
                for i in self.selectedIndexes():
                    self.delete_index(i)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Resize "Name" column.py on click/expansion."""
        super().mousePressEvent(event)
        self.resizeColumnToContents(0)

    def on_header_custom_context_menu(self, point: QPoint) -> None:
        """Ran when the customContextMenuRequested signal is emitted.

        :param point: The point to place the context menu.
        """
        from ..menus import ColumnContextMenu

        index = self.indexAt(point)

        if index.isValid():
            menu = ColumnContextMenu(self, {0})
            menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

            menu.exec(self.viewport().mapToGlobal(point))

    def on_custom_context_menu(self, point: QPoint) -> None:
        """Ran when the customContextMenuRequested signal is emitted.

        :param point: The point to place the context menu.
        """
        from ..menus import CacheIndexContextMenu

        index = self.indexAt(point)

        if index.isValid():
            menu = CacheIndexContextMenu(self, index)
            menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

            menu.exec(self.viewport().mapToGlobal(point))

    def on_double_click(self, index: QModelIndex) -> None:
        """Ran when the doubleClicked signal is emitted.

        :param index: The model index which was double-clicked.
        """
        if index.isValid():
            self.openFileInView.emit(self.model().filePath(index))
