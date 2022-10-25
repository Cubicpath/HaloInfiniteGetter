###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""File menu implementation."""
from __future__ import annotations

__all__ = (
    'export_data',
    'FileContextMenu',
    'import_data',
)

import shutil
from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ...models import DeferredCallable
from ...utils.common import get_weakref_object
from ...utils.gui import add_menu_items
from ...utils.gui import init_objects
from ..app import app
from ..app import tr

# Default file extension is .7z
_ARCHIVE_FILTER:       str = ';;'.join(('Archive Files (*.7z *.zip *.piz *.tar *.tar.gz *.tgz *.tar.bz2 *.tbz2 *.tar.xz *.txz)', 'All files (*.*)'))
_EXPORT_EXTENSION_MAP: dict[str, str] = {
    '.7z': '7z',
    '.tar': 'tar',
    '.zip': 'zip', '.piz': 'zip',
    '.tar.gz': 'gztar', '.tgz': 'gztar',
    '.tar.bz2': 'bztar', '.tbz2': 'bztar',
    '.tar.xz': 'xztar', '.txz': 'xztar'
}


def export_data() -> None:
    """Export cached_requests to an archive file selected by a :py:class:`QFileDialog`.

    The following archive types are supported::

        7z, tar, zip, gztar, bztar, xztar
    """
    export_file = Path(QFileDialog.getSaveFileName(get_weakref_object(app().windows['app']), caption=tr('gui.menus.file.export'),
                                                   dir=str(Path.home()), filter=_ARCHIVE_FILTER)[0])
    if export_file.is_dir():
        return

    archive_format = _EXPORT_EXTENSION_MAP.get(export_file.suffix)

    if archive_format is None:
        app().show_dialog('test')
        return

    shutil.make_archive(str(export_file.with_name(export_file.stem)), archive_format, root_dir=HI_CACHE_PATH, base_dir='./cached_requests')


def import_data() -> None:
    """Import data from an archive file selected by a :py:class:`QFileDialog`.

    The following archive extensions are supported::

        .7z .zip .piz .tar .tar.gz .tgz .tar.bz2 .tbz2 .tar.xz .txz
    """
    archive_file = Path(QFileDialog.getOpenFileName(get_weakref_object(app().windows['app']), caption=tr('gui.menus.file.import'),
                                                    dir=str(Path.home()), filter=_ARCHIVE_FILTER)[0])

    if archive_file.is_dir():
        return

    shutil.unpack_archive(str(archive_file), extract_dir=HI_CACHE_PATH)


class FileContextMenu(QMenu):
    """Context menu that shows actions to manipulate files."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`FileContextMenu`."""
        super().__init__(parent)

        init_objects({
            (open_explorer := QAction(self)): {
                'text': tr('gui.menus.file.open'),
                'icon': app().get_theme_icon('dialog_open') or app().icon_store['folder'],
                'triggered': DeferredCallable(
                    QDesktopServices.openUrl, QUrl(HI_CACHE_PATH.as_uri())
                )
            },

            (flush_cache := QAction(self)): {
                'disabled': not tuple(HI_CACHE_PATH.iterdir()),  # Set disabled if HI_CACHE_PATH directory is empty
                'text': tr('gui.menus.file.flush'),
                'icon': app().get_theme_icon('dialog_discard') or self.style().standardIcon(QStyle.SP_DialogDiscardButton),
                'triggered': self.flush_cache
            },

            (import_from := QAction(self)): {
                'text': tr('gui.menus.file.import'),
                'icon': app().icon_store['import'],
                'triggered': import_data
            },

            (export_to := QAction(self)): {
                'text': tr('gui.menus.file.export'),
                'icon': app().icon_store['export'],
                'triggered': export_data
            }
        })

        add_menu_items(self, [
            'Files', open_explorer, flush_cache,
            'Import/Export', import_from, export_to
        ])

    def flush_cache(self) -> None:
        """Remove all data from cache."""
        do_flush: bool = app().show_dialog(
            'warnings.delete_cache', self,
            QMessageBox.Ok | QMessageBox.Cancel,
            default_button=QMessageBox.Cancel
        ).role == QMessageBox.AcceptRole

        if do_flush:
            QDir(HI_CACHE_PATH).removeRecursively()
            HI_CACHE_PATH.mkdir()
