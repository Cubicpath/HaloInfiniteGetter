###################################################################################################
#                              MIT Licence (C) 2023 Cubicpath@Github                              #
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
from shiboken6 import Shiboken


class _SignalHolder(QObject):
    exceptionRaised = Signal(Exception)
    valueReturned = Signal(object)


class _Worker(QRunnable):
    _signal_holder: type[_SignalHolder] = _SignalHolder

    def __init__(self, **kwargs: Callable | Slot) -> None:
        super().__init__()
        self.signals = self._signal_holder()

        # Connect signals from keyword arguments
        for kw, val in kwargs.items():
            if hasattr(self.signals, kw) and isinstance((signal := getattr(self.signals, kw)), SignalInstance):
                signal.connect(val)
            else:
                raise TypeError(f'"{kw}" is not a valid kwarg or signal name.')

    # pylint: disable=no-self-use
    def _dummy_method(self) -> None:
        return

    def _run(self) -> None:
        raise NotImplementedError

    # pylint: disable=broad-except
    @Slot()
    def run(self) -> None:
        """Ran by the :py:class:`QThreadPool`.

        Sends non-``None`` return values through the ``valueReturned`` signal.
            - If you need to return ``None``, I suggest creating a separate object to represent it.

        Sends any uncaught :py:class:`Exception`'s through the ``exceptionRaised`` signal.

        :raises RuntimeError: If worker started before application instance is defined.
        """
        if (app := QCoreApplication.instance()) is None:
            raise RuntimeError('Worker started before application instance is defined.')

        # Workaround for application deadlock (issue #31)
        app.aboutToQuit.connect(  # pyright: ignore[reportGeneralTypeIssues]
            self._dummy_method, Qt.ConnectionType.BlockingQueuedConnection
        )

        try:
            # Emit non-None return values through the `valueReturned` signal.
            if (ret_val := self._run()) is not None:
                self.signals.valueReturned.emit(ret_val)

        except Exception as e:
            # This occurs when the application is exiting and an internal C++ object is being read after it is deleted.
            # So, return quietly and allow the process to exit with no errors.
            if not Shiboken.isValid(self.signals):
                return

            self.signals.exceptionRaised.emit(e)

        # Disconnect deadlock safeguard if successful to avoid possible leak
        app.aboutToQuit.disconnect(self._dummy_method)  # pyright: ignore[reportGeneralTypeIssues]

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
        """Create a new :py:class:`ExportData` worker to run with the given ``base`` path and ``dest`` file."""
        super().__init__(**kwargs)
        self.base = base
        self.dest = dest

    def _run(self) -> None:
        # This implicitly raises ValueError if the destination suffix is not a valid extension format.
        temp_archive_path: str = shutil.make_archive(
            base_name=QDir.tempPath() + f'/{self.dest.stem}',
            format=self.EXTENSION_FORMATS.get(self.dest.suffix, f'.{self.dest.suffix}'),
            root_dir=self.base.parent,
            base_dir=f'./{self.base.name}'
        )

        shutil.move(
            src=temp_archive_path,
            dst=self.dest
        )


class ImportData(_Worker):
    """Extract from archive into a directory."""

    def __init__(self, archive: Path, dest: Path, **kwargs: Callable | Slot) -> None:
        """Create a new :py:class:`ImportData` worker to run with the given ``archive`` file and ``dest`` path."""
        super().__init__(**kwargs)
        self.archive = archive
        self.dest = dest

    def _run(self) -> None:
        shutil.unpack_archive(str(self.archive), extract_dir=self.dest)
