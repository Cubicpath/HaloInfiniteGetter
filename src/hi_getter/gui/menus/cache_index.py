###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""CacheExplorer implementation."""
from __future__ import annotations

__all__ = (
    'CacheIndexContextMenu',
    'file_to_clipboard',
)

from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ...models import DeferredCallable
from ...utils.gui import add_menu_items
from ...utils.gui import init_objects
from ..app import app
from ..app import tr
from ..widgets.cache_explorer import CacheExplorer


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


# noinspection PyProtectedMember
class CacheIndexContextMenu(QMenu):
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
                'icon': parent.model().iconProvider()._fallback_provider.icon(parent.model().fileInfo(index)),
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
