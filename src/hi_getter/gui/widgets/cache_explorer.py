###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""CacheExplorer implementation."""
from __future__ import annotations

__all__ = (
    'CacheExplorer',
    'file_to_clipboard',
)

from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ...events import EventBus
from ...models import DeferredCallable
from ...tomlfile import TomlEvents
from ...utils.gui import add_menu_items
from ...utils.gui import init_objects
from ..app import app
from ..app import tr


def file_to_clipboard(file_path: Path):
    """Copy the file's contents to the application's clipboard.

    Works with both images and text.

    :param file_path: File path to read from.
    """
    if str(file_path).endswith(tuple(SUPPORTED_IMAGE_EXTENSIONS)):
        pixmap = QPixmap()
        pixmap.loadFromData(file_path.read_bytes())
        app().clipboard().setImage(pixmap.toImage())
    else:
        app().clipboard().setText(file_path.read_text(encoding='utf8'))


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

        try:
            os_path = app().client.to_get_path(file_path.as_posix())
        except (IndexError, ValueError):
            os_path = ''

        init_objects({
            (folding_submenu := QMenu(self)): {
                'title': tr('gui.menus.cached_file.folding')
            },

            (open_in_view := QAction(self)): {
                'disabled': file_path.is_dir(),
                'text': tr('gui.menus.cached_file.open_in_view'),
                'icon': self.style().standardIcon(QStyle.SP_DesktopIcon),
                'triggered': DeferredCallable(
                    parent.openFileInView.emit, file_path.as_posix()
                )
            },

            (open_in_default_app := QAction(self)): {
                'disabled': file_path.is_dir(),
                'text': tr('gui.menus.cached_file.open_in_default_app'),
                'icon': self.style().standardIcon(QStyle.SP_DesktopIcon),
                'triggered': DeferredCallable(
                    QDesktopServices.openUrl, QUrl(file_path.as_uri())
                )
            },

            (open_in_explorer := QAction(self)): {
                'text': tr('gui.menus.cached_file.view_in_explorer'),
                'icon': app().get_theme_icon('dialog_open') or app().icon_store['folder'],
                'triggered': DeferredCallable(
                    QDesktopServices.openUrl, QUrl(dir_path.as_uri())
                )
            },

            (expand_this := QAction(self)): {
                'disabled': file_path.is_file(),
                'text': tr('gui.menus.cached_file.folding.expand_this'),
                'triggered': DeferredCallable(parent.expand, index)
            },

            (expand_recursively := QAction(self)): {
                'disabled': file_path.is_file(),
                'text': tr('gui.menus.cached_file.folding.expand_recursively'),
                'triggered': DeferredCallable(parent.expandRecursively, index)
            },

            (expand_all := QAction(self)): {
                'text': tr('gui.menus.cached_file.folding.expand_all'),
                'triggered': parent.expandAll
            },

            (collapse_this := QAction(self)): {
                'disabled': file_path.is_file(),
                'text': tr('gui.menus.cached_file.folding.collapse_this'),
                'triggered': DeferredCallable(parent.collapse, index)
            },

            (collapse_all := QAction(self)): {
                'text': tr('gui.menus.cached_file.folding.collapse_all'),
                'triggered': parent.collapseAll
            },

            (copy_full_path := QAction(self)): {
                'text': tr('gui.menus.cached_file.copy_full_path'),
                'triggered': DeferredCallable(app().clipboard().setText, str(file_path))
            },

            (copy_endpoint_path := QAction(self)): {
                'disabled': not os_path,
                'text': tr('gui.menus.cached_file.copy_endpoint_path'),
                'triggered': DeferredCallable(app().clipboard().setText, os_path)
            },

            (copy_contents := QAction(self)): {
                'disabled': file_path.is_dir(),
                'text': tr('gui.menus.cached_file.copy_contents'),
                'triggered': DeferredCallable(file_to_clipboard, file_path)
            },

            (delete := QAction(self)): {
                'text': tr('gui.menus.cached_file.delete', 'Folder' if file_path.is_dir() else 'File'),
                'icon': app().get_theme_icon('dialog_cancel') or self.style().standardIcon(QStyle.SP_DialogCancelButton),
                'triggered': DeferredCallable(parent.delete_index, index)
            },
        })

        add_menu_items(folding_submenu, [
            'Expand', expand_this, expand_recursively, expand_all,
            'Collapse', collapse_this, collapse_all,
        ])

        add_menu_items(self, [
            'Open', open_in_view, open_in_default_app, open_in_explorer,
            'Folding', folding_submenu,
            'Copy', copy_full_path, copy_endpoint_path, copy_contents,
            'Delete', delete
        ])


class _IconProvider(QAbstractFileIconProvider):
    NULL_ICON = QIcon()

    def __init__(self, cache_explorer: CacheExplorer):
        super().__init__()
        self._cache_explorer = cache_explorer
        self._icon_mode: int = app().settings['gui/cache_explorer/icon_mode']
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
        if self._icon_mode == 0:
            return _IconProvider.NULL_ICON

        if isinstance(info, QFileInfo):
            if info.isDir() and info.fileName() == 'cached_requests':
                return self._cache_explorer.style().standardIcon(QStyle.SP_DialogSaveButton)

            # Preview images
            if self._icon_mode == 2:
                if info.isFile() and info.suffix().lstrip('.') in SUPPORTED_IMAGE_EXTENSIONS:
                    icon = QIcon()
                    icon.addFile(info.filePath(), QSize(24, 24))
                    return icon

        return self._fallback_provider.icon(info)

    def on_mode_change(self, event: TomlEvents.Set):
        """Set the icon mode to the one selected in settings."""
        self._icon_mode = event.new
        self._cache_explorer.model().setIconProvider(self)


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
                'rootPath': HI_CACHE_PATH.absolute().as_posix(),
                'iconProvider': _IconProvider(self),
                'nameFilters': [f'*.{ext}' for ext in SUPPORTED_IMAGE_EXTENSIONS],
                'nameFilterDisables': True
            },

            self: {
                'model': model,
                'rootIndex': model.index(HI_CACHE_PATH.absolute().as_posix()),
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

        # Hide all but Name by default
        for index in (1, 2, 3):  # SIZE, FILE TYPE, DATE MODIFIED
            self.hideColumn(index)

    def delete_index(self, index: QModelIndex) -> None:
        """Deletes a given index from the file system after prompting the user.

        If the path resolves to a directory, all items in the directory are recursively removed.

        :param index: The index to get the filepath from and delete.
        """
        file_path: Path = Path(self.model().filePath(index))
        path_type: str = 'Folder' if file_path.is_dir() else 'File'

        consent: bool = app().show_dialog(
            'warnings.delete_path', self, (
                QMessageBox.Ok | QMessageBox.Cancel
            ), default_button=QMessageBox.Cancel,
            title_args=(path_type,),
            description_args=(path_type, file_path)
        ).role == QMessageBox.AcceptRole

        if consent:
            if file_path.is_dir():
                QDir(file_path).removeRecursively()
            else:
                file_path.unlink()

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

    def model(self) -> QFileSystemModel:
        """:return: The file system model for the CacheExplorer."""
        # pylint: disable=useless-super-delegation
        return super().model()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Map keys to actions."""
        super().keyPressEvent(event)

        match event.key():
            case Qt.Key_Delete:
                # Delete Path at Selected Index
                for i in self.selectedIndexes():
                    self.delete_index(i)

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
