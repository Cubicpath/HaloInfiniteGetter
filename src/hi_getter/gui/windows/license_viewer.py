###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing implementation of all GUI elements.

Yes, putting this into one file is hideous, but it's the only supported way to completely prevent circular imports.
"""
from __future__ import annotations

__all__ = (
    'LicenseViewer',
)

from typing import Final

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ...utils.gui import scroll_to_top
from ...utils.package import current_requirement_licenses
from ..app import app
from ..app import tr
from ..widgets import ExternalTextBrowser


# noinspection PyArgumentList
class LicenseViewer(QWidget):
    """Widget that formats and shows the project's (and all of its requirements') license files."""
    LICENSE_DATA: Final[dict[str, tuple[str, str]]] = current_requirement_licenses(HI_PACKAGE_NAME, include_extras=True)

    def __init__(self, *args, **kwargs) -> None:
        """Create a new LicenseViewer. Gets license from the HI_RESOURCE_PATH/LICENSE file

        Has a fixed size of 750x380.
        """
        super().__init__(*args, **kwargs)
        self.setWindowTitle(tr('gui.license_viewer.title'))
        self.setWindowIcon(app().icon_store['copyright'])
        self.resize(QSize(750, 550))
        self.current_license_index = 0

        self.license_label:       QLabel
        self.license_index_label: QLabel
        self.license_text_edit:   ExternalTextBrowser
        self.next_license_button: QPushButton
        self.prev_license_button: QPushButton
        self._init_ui()

    def _init_ui(self) -> None:
        self.license_label:       QLabel = QLabel(self)
        self.license_index_label: QLabel = QLabel(f'{self.current_license_index + 1} of {len(self.LICENSE_DATA)}', self)
        self.license_text_edit:   ExternalTextBrowser = ExternalTextBrowser(self)
        self.next_license_button: QPushButton = QPushButton(tr('gui.license_viewer.next'), clicked=self.next_license)
        self.prev_license_button: QPushButton = QPushButton(tr('gui.license_viewer.previous'), clicked=self.prev_license)

        self.license_text_edit.connect_key_to(Qt.Key_Left, self.prev_license)
        self.license_text_edit.connect_key_to(Qt.Key_Right, self.next_license)
        self.view_package(HI_PACKAGE_NAME)

        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        layout.addLayout(top)
        top.addWidget(self.license_label)
        top.addWidget(self.prev_license_button)
        top.addWidget(self.next_license_button)
        top.addWidget(self.license_index_label)
        layout.addWidget(self.license_text_edit)

        cursor = self.license_text_edit.textCursor()
        cursor.clearSelection()
        cursor.select(QTextCursor.SelectionType.Document)
        self.next_license_button.setMaximumWidth(100)
        self.prev_license_button.setMaximumWidth(100)
        self.license_index_label.setMaximumWidth(50)
        self.license_text_edit.setFont(QFont('consolas', 11))
        self.license_text_edit.setOpenExternalLinks(True)

    def next_license(self) -> None:
        """View the next license."""
        self.current_license_index += 1
        if self.current_license_index + 1 > len(self.LICENSE_DATA):
            self.current_license_index = 0
        self.view_current_index()

    def prev_license(self) -> None:
        """View the previous license."""
        self.current_license_index -= 1
        if self.current_license_index < 0:
            self.current_license_index = len(self.LICENSE_DATA) - 1
        self.view_current_index()

    def view_current_index(self) -> None:
        """Views the license data at the current index."""
        self.view_package(tuple(self.LICENSE_DATA)[self.current_license_index])

    def view_package(self, package: str) -> None:
        """Views the license data of the given package name."""
        license_text = self.LICENSE_DATA[package][1] or tr('gui.license_viewer.not_found')
        self.current_license_index = tuple(self.LICENSE_DATA).index(package)
        self.license_label.setText(f'{package} -- "{self.LICENSE_DATA[package][0]}" {tr("gui.license_viewer.license")}')
        self.license_index_label.setText(f'{self.current_license_index + 1} of {len(self.LICENSE_DATA)}')

        output = license_text
        replaced = set()
        for match in HI_URL_PATTERN.finditer(license_text):
            match = match[0]
            if match not in replaced:
                output = output.replace(match, f'<a href="{match}" style="color: #2A5DB0">{match}</a>')
                replaced.add(match)

        stripped_output = ''
        for line in output.splitlines():
            stripped_output += line.strip() + '\n'
        stripped_output = stripped_output.strip()
        self.license_text_edit.setHtml(
            f'<body style="white-space: pre-wrap">'
            f'<center>{stripped_output}</center>'
            f'</body>'
        )

        scroll_to_top(self.license_text_edit)
