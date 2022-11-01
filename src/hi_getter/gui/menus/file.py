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
from ..workers import ExportData
from ..workers import ImportData

# Default file extension is .7z
_ARCHIVE_FILTER: str = ';;'.join(('Archive Files (*.7z *.zip *.piz *.tar *.tar.gz *.tgz *.tar.bz2 *.tbz2 *.tar.xz *.txz)', 'All files (*.*)'))


def export_data() -> None:
    """Export cached_requests to an archive file selected by a :py:class:`QFileDialog`.

    The following archive types are supported::

        7z, tar, zip, gztar, bztar, xztar
    """
    # noinspection PyTypeChecker
    export_dest = Path(QFileDialog.getSaveFileName(None, caption=tr('gui.menus.file.export'),
                                                   dir=str(Path.home()), filter=_ARCHIVE_FILTER)[0])
    # Return early if no file selected
    if export_dest.is_dir():
        return

    if ExportData.EXTENSION_FORMATS.get(export_dest.suffix) is None:
        app().show_dialog('errors.unsupported_archive_type', description_args=(export_dest, export_dest.suffix,))
        return

    app().start_worker(ExportData(base=HI_CACHE_PATH / 'cached_requests', dest=export_dest))


def import_data() -> None:
    """Import data from an archive file selected by a :py:class:`QFileDialog`.

    The following archive extensions are supported::

        .7z .zip .piz .tar .tar.gz .tgz .tar.bz2 .tbz2 .tar.xz .txz
    """
    # noinspection PyTypeChecker
    archive_file = Path(QFileDialog.getOpenFileName(None, caption=tr('gui.menus.file.import'),
                                                    dir=str(Path.home() / 'Downloads'), filter=_ARCHIVE_FILTER)[0])
    # Return early if no file selected
    if archive_file.is_dir():
        return

    # Attempt to unpack file into temp dir
    app().start_worker(ImportData(archive=archive_file, dest=HI_CACHE_PATH, exceptionRaised=lambda e: app().show_dialog(
        'errors.cache_import_failure', description_args=(archive_file, e,)
    )))


class FileContextMenu(QMenu):
    """Context menu that shows actions to manipulate files."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`FileContextMenu`."""
        super().__init__(parent)

        cached_requests = HI_CACHE_PATH / 'cached_requests'

        init_objects({
            (open_explorer := QAction(self)): {
                'text': tr('gui.menus.file.open'),
                'icon': app().get_theme_icon('dialog_open') or app().icon_store['folder'],
                'triggered': DeferredCallable(
                    QDesktopServices.openUrl, QUrl(HI_CACHE_PATH.as_uri())
                )
            },

            (flush_cache := QAction(self)): {
                # DISABLED IF EMPTY DIRECTORY
                'disabled': not any(HI_CACHE_PATH.iterdir()),
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
                # DISABLED IF EMPTY DIRECTORY OR NOT DIRECTORY
                'disabled': True if (cached_requests.is_dir() and not any(cached_requests.iterdir())) else not cached_requests.is_dir(),
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
            HI_CACHE_PATH.mkdir(exist_ok=True)
