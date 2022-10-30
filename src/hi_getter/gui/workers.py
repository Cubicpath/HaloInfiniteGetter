###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Implementations for worker-thread runnables."""
from __future__ import annotations

__all__ = (
    'ExportData',
    'ImportData',
)

import shutil
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import *


class _Worker(QRunnable):
    def _run(self) -> None:
        raise NotImplementedError

    @Slot()
    def run(self) -> None:
        """Called by the :py:class:`QThreadPool`."""
        self._run()


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

    def __init__(self, base: Path, dest: Path) -> None:
        super().__init__()
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
    def __init__(self, archive: Path, dest: Path, on_error: Callable[[BaseException], None] | None = None) -> None:
        super().__init__()
        self.archive = archive
        self.dest = dest
        self.on_error = on_error

    def _run(self) -> None:
        try:
            shutil.unpack_archive(str(self.archive), extract_dir=self.dest)
        except (OSError, ValueError) as e:
            self.on_error(e)
