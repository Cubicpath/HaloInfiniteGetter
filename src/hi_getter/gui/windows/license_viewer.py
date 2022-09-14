###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""LicenseViewer implementation."""
from __future__ import annotations

__all__ = (
    'LicenseViewer',
)

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ...utils.gui import init_objects
from ...utils.gui import scroll_to_top
from ...utils.package import current_requirement_licenses
from ..app import app
from ..app import tr
from ..widgets import ExternalTextBrowser


# noinspection PyArgumentList
class LicenseViewer(QWidget):
    """Widget that formats and shows the project's (and all of its requirements') license files."""

    def __init__(self, *args, **kwargs) -> None:
        """Create a new LicenseViewer."""
        super().__init__(*args, **kwargs)
        self.setWindowTitle(tr('gui.license_viewer.title'))
        self.setWindowIcon(app().icon_store['copyright'])
        self.resize(QSize(750, 800))

        self.license_dropdown:    QComboBox
        self.license_index_label: QLabel
        self.license_text_edit:   ExternalTextBrowser
        self.next_license_button: QPushButton
        self.prev_license_button: QPushButton

        self.license_data: list[tuple[str, str, str]] = []
        for pkg, licenses in current_requirement_licenses(HI_PACKAGE_NAME, recursive=True, include_extras=True).items():
            for title, text in licenses:
                self.license_data.append((pkg, title, text))

        self._init_ui()

    def _init_ui(self) -> None:
        self.license_dropdown:    QComboBox = QComboBox(self)
        self.license_index_label: QLabel = QLabel(self)
        self.license_text_edit:   ExternalTextBrowser = ExternalTextBrowser(self)
        self.next_license_button: QPushButton = QPushButton(self)
        self.prev_license_button: QPushButton = QPushButton(self)

        init_objects({
            self.license_dropdown: {
                'size': {'fixed': (300, 26)},
                'activated': lambda i: self.view_index(i),
                'items': (
                    f'{pkg[0]}/{pkg[1]}' for pkg in self.license_data
                )
            },

            self.license_index_label: {
                'size': {'maximum': (50, None)},
                'text': tr(
                    'gui.license_viewer.current_index', self.license_dropdown.currentIndex() + 1, len(self.license_data)
                )
            },

            self.license_text_edit: {
                'font': QFont('consolas', 11),
                'openExternalLinks': True,
            },

            self.next_license_button: {
                'size': {'fixed': (100, None)},
                'clicked': self.next_license,
            },

            self.prev_license_button: {
                'size': {'fixed': (100, None)},
                'clicked': self.prev_license,
            }
        })

        app().init_translations({
            self.setWindowTitle: 'gui.license_viewer.title',

            self.next_license_button.setText: 'gui.license_viewer.next',
            self.prev_license_button.setText: 'gui.license_viewer.previous',
        })

        self.license_text_edit.connect_key_to(Qt.Key_Left, self.prev_license)
        self.license_text_edit.connect_key_to(Qt.Key_Right, self.next_license)
        self.view_current_index()

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top_right = QHBoxLayout()

        layout.addLayout(top)
        top.addWidget(self.license_dropdown)
        top.addLayout(top_right)
        top_right.setAlignment(Qt.AlignRight)
        top_right.addWidget(self.prev_license_button)
        top_right.addWidget(self.next_license_button)
        top_right.addWidget(self.license_index_label)
        layout.addWidget(self.license_text_edit)

        cursor = self.license_text_edit.textCursor()
        cursor.clearSelection()
        cursor.select(QTextCursor.SelectionType.Document)

    def next_license(self) -> None:
        """View the next license."""
        index = self.license_dropdown.currentIndex() + 1
        if index + 1 > self.license_dropdown.count():
            index = 0
        self.view_index(index)

    def prev_license(self) -> None:
        """View the previous license."""
        index = self.license_dropdown.currentIndex() - 1
        if index < 0:
            index = self.license_dropdown.count() - 1
        self.view_index(index)

    def view_index(self, index: int) -> None:
        """View the license at the given index."""
        self.license_dropdown.setCurrentIndex(index)
        self.view_current_index()

    def view_current_index(self) -> None:
        """Views the license data at the current index."""
        current_data: tuple[str, str, str] = self.license_data[self.license_dropdown.currentIndex()]

        license_text = current_data[2] or tr('gui.license_viewer.not_found')
        self.license_index_label.setText(tr(
            'gui.license_viewer.current_index', self.license_dropdown.currentIndex() + 1, len(self.license_data)
        ))

        # Use Regex & HTML to make links clickable
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