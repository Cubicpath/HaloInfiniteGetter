###################################################################################################
#                              MIT Licence (C) 2023 Cubicpath@Github                              #
###################################################################################################
"""ScanSelectorDialog implementation."""
from __future__ import annotations

__all__ = (
    'ScanSelectorDialog',
)

from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...utils import init_layouts
from ...utils import init_objects
from ..aliases import app
from ..aliases import tr


_SCAN_FILTER: str = ';;'.join((
    'JSON Files (*.json)',
    'All files (*.*)'
))


class ScanSelectorDialog(QWidget):
    """A :py:class:`ScanSelectorDialog` which allows you to select JSON files to scan."""

    def __init__(self) -> None:
        """Create a new :py:class:`SignInDialog`."""
        super().__init__(None)

        self._init_ui()

    def _init_ui(self) -> None:
        self.filepaths_input = QLineEdit(self)
        self.scan_button = QPushButton(self)

        init_objects({
            self: {
                'size': {'fixed': (500, 100)},
                'windowFlags': Qt.WindowType.Dialog,
                'windowModality': Qt.WindowModality.ApplicationModal,
                'windowIcon': self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView),
            },

            (filepaths_selector := QPushButton(self)): {
                'clicked': self.select_files
            },

            self.scan_button: {
                # 'clicked': start_sign_in,
            },

            (cancel_button := QPushButton(self)): {
                'clicked': self.close,
            }
        })

        app().init_translations({
            self.setWindowTitle: 'gui.scan_selector_dialog.title',
            self.filepaths_input.setPlaceholderText: 'gui.scan_selector_dialog.filepaths_placeholder',
            filepaths_selector.setText: 'gui.scan_selector_dialog.select_files',

            self.scan_button.setText: 'gui.scan_selector_dialog.scan',
            cancel_button.setText: 'gui.scan_selector_dialog.cancel'
        })

        init_layouts({
            (input_layout := QHBoxLayout()): {
                'items': (self.filepaths_input, filepaths_selector)
            },

            (bottom := QHBoxLayout()): {
                'items': (self.scan_button, cancel_button)
            },

            # Main layout
            QVBoxLayout(self): {
                'items': (input_layout, bottom)
            }
        })

    def _reset_widgets(self) -> None:
        self.filepaths_input.clear()

        self.scan_button.setDisabled(True)

    def select_files(self) -> None:
        """Select JSON files to scan through a file dialog."""
        names: list[str] = QFileDialog.getOpenFileNames(self, caption=tr('gui.scan_selector_dialog.select_files'),
                                                        dir=str(Path.home() / 'Downloads'),
                                                        filter=_SCAN_FILTER)[0]
        # If no filenames are selected, do nothing.
        if not names:
            return

        # Override input text with a string representation of selected files
        self.filepaths_input.setText(', '.join(f'"{Path(file)}"' for file in names))

    def showEvent(self, event: QShowEvent) -> None:
        """Reset widgets when dialog is shown to user."""
        super().showEvent(event)
        self._reset_widgets()
