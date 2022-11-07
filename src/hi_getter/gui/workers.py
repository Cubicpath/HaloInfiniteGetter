###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Implementations for worker-thread runnables."""
from __future__ import annotations

__all__ = (
    'ExportData',
    'ImportData',
    'RecursiveSearch',
)

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import *
from shiboken6 import Shiboken

from ..constants import *
from ..network.client import Client
from ..utils.common import unique_values


class _SignalHolder(QObject):
    exceptionRaised = Signal(Exception, name='exceptionRaised')
    valueReturned = Signal(object, name='valueReturned')


class _Worker(QRunnable):
    _signal_holder = _SignalHolder

    def __init__(self, **kwargs: Callable | Slot) -> None:
        super().__init__()
        self.signals = self._signal_holder()

        # Connect signals from keyword arguments
        for kw, val in kwargs.items():
            if hasattr(self.signals, kw) and isinstance((signal := getattr(self.signals, kw)), SignalInstance):
                signal.connect(val)
            else:
                raise TypeError(f'"{kw}" is not a valid kwarg or signal name.')

    def _dummy_method(self) -> None:
        return

    def _run(self) -> None:
        raise NotImplementedError

    # pylint: disable=broad-except
    @Slot()
    def run(self) -> None:
        """Called by the :py:class:`QThreadPool`.

        Sends non-``None`` return values through the ``valueReturned`` signal.
            - If you need to return ``None``, I suggest creating a separate object to represent it.

        Sends any uncaught :py:class:`Exception`'s through the ``exceptionRaised`` signal.
        """
        # No idea how, but this fixes application deadlock cause by RecursiveSearch (issue #31)
        QCoreApplication.instance().aboutToQuit.connect(self._dummy_method, Qt.BlockingQueuedConnection)

        try:
            # If the return value of the implemented _run function is not None, emit it through the `valueReturned` signal.
            if (ret_val := self._run()) is not None:
                self.signals.valueReturned.emit(ret_val)

        except Exception as e:
            # This occurs when the application is exiting and an internal C++ object is being read after it is deleted.
            # So, return quietly and allow the process to exit with no errors.
            if not Shiboken.isValid(self.signals):
                return

            self.signals.exceptionRaised.emit(e)

        # Disconnect deadlock safeguard if successful to avoid possible leak
        QCoreApplication.instance().aboutToQuit.disconnect(self._dummy_method)

        # Delete if not deleted
        if Shiboken.isValid(self.signals):
            self.signals.deleteLater()


class ExportData(_Worker):
    """Build archive in a temp file then remove .tmp extension when finished."""
    EXTENSION_FORMATS: dict[str, str] = {
        '.7z': '7z',
        '.tar': 'tar',
        '.zip': 'zip', '.piz': 'zip',
        '.tar.gz': 'gztar', '.tgz': 'gztar',
        '.tar.bz2': 'bztar', '.tbz2': 'bztar',
        '.tar.xz': 'xztar', '.txz': 'xztar'
    }

    def __init__(self, base: Path, dest: Path, **kwargs: Callable | Slot) -> None:
        super().__init__(**kwargs)
        self.base = base
        self.dest = dest

    def _run(self) -> None:
        temp_archive_path: str = shutil.make_archive(
            QDir.tempPath() + f'/{self.dest.stem}', self.EXTENSION_FORMATS.get(self.dest.suffix),
            root_dir=self.base.parent, base_dir=f'./{self.base.name}'
        )

        shutil.move(
            src=temp_archive_path,
            dst=self.dest
        )


class ImportData(_Worker):
    """Extract from archive into a directory."""

    def __init__(self, archive: Path, dest: Path, **kwargs: Callable | Slot) -> None:
        super().__init__(**kwargs)
        self.archive = archive
        self.dest = dest

    def _run(self) -> None:
        shutil.unpack_archive(str(self.archive), extract_dir=self.dest)


class RecursiveSearch(_Worker):
    """Recursively get Halo Waypoint files linked to the search_path through Mapping keys."""

    def __init__(self, client: Client, search_path: str, **kwargs: Callable | Slot) -> None:
        super().__init__(**kwargs)
        self.client = client
        self.search_path = search_path

    def _run(self) -> None:
        self._recursive_search(self.search_path)

    def _recursive_search(self, search_path: str) -> None:
        # This set is shared between all recursive calls, so no duplicate searches should occur
        searched: set[str] = self.client.searched_paths
        searched.add(search_path.lower())

        # Get data from Client, and return if it's not JSON
        data: dict[str, Any] | bytes | int = self.client.get_hi_data(search_path)
        if isinstance(data, (bytes, int)):
            return

        # Iterate over all values in the JSON data
        # This process ignores already-searched values
        for value in unique_values(data):
            if isinstance(value, str) and (match := HI_PATH_PATTERN.match(value)):
                path: str = match[0]
                ext: str = match['file_name'].split('.')[-1].lower()
                has_pre_path: bool = match['pre_path'] is not None

                # If a value ends in .json, get the data for that path and start the process over again
                if ext in {'json'}:
                    if not has_pre_path:
                        path = 'progression/file/' + path

                    if path.lower() in searched:
                        continue

                    self._recursive_search(path)

                # If it's an image, download it then ignore the result
                elif ext in SUPPORTED_IMAGE_EXTENSIONS:
                    if not has_pre_path:
                        path = 'images/file/' + path

                    if path.lower() in searched:
                        continue

                    searched.add(path.lower())
                    self.client.get_hi_data(path)
