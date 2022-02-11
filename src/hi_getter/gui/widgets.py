###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing miscellaneous :py:class:`QWidget` Widgets."""
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ..constants import *

__all__ = (
    'LicenseViewer',
)


class LicenseViewer(QWidget):
    """Widget that formats and shows the project's license file."""

    def __init__(self) -> None:
        """Create a new LicenseViewer. Gets license from the RESOURCE_PATH/LICENSE file

        Has a fixed size of 750x380.
        """
        super().__init__()
        self.setWindowTitle('License Viewer')
        self.setWindowIcon(QIcon(str(RESOURCE_PATH / 'icons/copyright.ico')))
        self.resize(QSize(750, 380))
        self.setFixedSize(self.size())

        with (RESOURCE_PATH / 'LICENSE').open(mode='r', encoding='utf8') as file:
            license_text = QTextEdit()
            for line in file.readlines():
                license_text.append(line)

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(license_text)

        block_format = QTextBlockFormat()
        block_format.setLineHeight(40, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        cursor = license_text.textCursor()
        cursor.clearSelection()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(block_format)
        license_text.setFont(QFont('consolas', 12))
        license_text.setDisabled(True)
