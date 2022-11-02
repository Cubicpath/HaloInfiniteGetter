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

from ..constants import SUPPORTED_IMAGE_EXTENSIONS
from ..network.client import Client
from ..utils.common import unique_values


class _SignalHolder(QObject):
    exceptionRaised = Signal(Exception, name='exceptionRaised')
    valueReturned = Signal(object, name='valueReturned')


class _Worker(QRunnable):
    _signal_holder = _SignalHolder

    def __init__(self, **kwargs: Callable | Slot):
        super().__init__()
        self.signals = self._signal_holder()

        # Connect signals from keyword arguments
        for kw, val in kwargs.items():
            if hasattr(self.signals, kw) and isinstance((signal := getattr(self.signals, kw)), SignalInstance):
                signal.connect(val)
            else:
                raise TypeError(f'"{kw}" is not a valid kwarg or signal name.')

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
        try:
            if (ret_val := self._run()) is not None:
                self.signals.valueReturned.emit(ret_val)
        except Exception as e:
            self.signals.exceptionRaised.emit(e)

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

    def _recursive_search(self, search_path: str):
        if self.client.searched_paths.get(search_path, 0) >= 2:
            return

        data: dict[str, Any] | bytes | int = self.client.get_hi_data(search_path)
        if isinstance(data, (bytes, int)):
            return

        for value in unique_values(data):
            if isinstance(value, str):
                if '/' not in value:
                    continue

                end = value.split('.')[-1].lower()
                if end in ('json',):
                    path = 'progression/file/' + value
                    self.client.searched_paths.update({path: self.client.searched_paths.get(path, 0) + 1})
                    self._recursive_search(path)
                elif end in SUPPORTED_IMAGE_EXTENSIONS:
                    self.client.get_hi_data('images/file/' + value)
