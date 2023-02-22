###################################################################################################
#                              MIT Licence (C) 2023 Cubicpath@Github                              #
###################################################################################################
"""ScanSelectorDialog implementation."""
from __future__ import annotations

__all__ = (
    'ScanSelectorDialog',
)

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
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
        self.do_recursive = QCheckBox(self)

        init_objects({
            self: {
                'size': {'fixed': (500, 100)},
                'windowFlags': Qt.WindowType.Dialog,
                'windowModality': Qt.WindowModality.ApplicationModal,
                'windowIcon': self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView),
            },

            self.filepaths_input: {
                'maxLength': (2 ** 31) - 1,  # Max int for shiboken
            },

            (filepaths_selector := QPushButton(self)): {
                'clicked': self.select_files
            },

            self.do_recursive: {
                'checked': True
            },

            self.scan_button: {
                'clicked': self.scan_files,
            },

            (cancel_button := QPushButton(self)): {
                'clicked': self.close,
            }
        })

        app().init_translations({
            self.setWindowTitle: 'gui.scan_selector_dialog.title',
            self.filepaths_input.setPlaceholderText: 'gui.scan_selector_dialog.filepaths_placeholder',
            filepaths_selector.setText: 'gui.scan_selector_dialog.select_files',
            self.do_recursive.setText: 'gui.scan_selector_dialog.do_recursive',

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
                'items': (input_layout, self.do_recursive, bottom)
            }
        })

    def _reset_widgets(self) -> None:
        self.filepaths_input.clear()

    # noinspection PyProtectedMember
    # pylint: disable=protected-access
    def scan_files(self) -> None:
        """Parse the input for paths, then read json data and tell the application's Client to scan it.

        :raises Exception: If an exception occurs when searching files, it is handled then reraised.
        """
        # If no filenames are selected, do nothing.
        if not (user_input := self.filepaths_input.text()):
            return

        app().warn_for('warnings.photosensitivity.scan')
        paths: tuple[Path] = tuple(Path(name.strip(' \'\",')) for name in user_input.split(', '))

        # Disconnect _on_finished_search so searched_paths isn't cleared prematurely
        app().client.finishedSearch.disconnect(app().client._on_finished_search)
        try:
            for i, path in enumerate(paths):
                path = path.expanduser().resolve(strict=True)
                data: dict[str, Any] = json.loads(path.read_bytes())

                if i == len(paths) - 1:
                    app().client.finishedSearch.connect(app().client._on_finished_search)

                app().client.start_handle_json(data, self.do_recursive.isChecked())

        # If an exception occurs, reconnect the _on_finished_search method and reraise
        except Exception as e:
            app().client.finishedSearch.connect(app().client._on_finished_search)
            raise e

        self.close()

    def select_files(self) -> None:
        """Select JSON files to scan through a file dialog."""
        names: list[str] = QFileDialog.getOpenFileNames(self, caption=tr('gui.scan_selector_dialog.select_files'),
                                                        dir=str(HI_WEB_DUMP_PATH),
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
