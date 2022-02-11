###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ..constants import *

__all__ = (
    'LicenseViewer',
)


class LicenseViewer(QWidget):
    def __init__(self) -> None:
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

        blockFmt = QTextBlockFormat()
        blockFmt.setLineHeight(40, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        theCursor = license_text.textCursor()
        theCursor.clearSelection()
        theCursor.select(QTextCursor.SelectionType.Document)
        theCursor.mergeBlockFormat(blockFmt)
        license_text.setFont(QFont('consolas', 12))
        license_text.setDisabled(True)
