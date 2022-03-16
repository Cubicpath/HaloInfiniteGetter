###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing miscellaneous :py:class:`QWidget` Widgets."""

__all__ = (
    'BetterLineEdit',
    'HistoryComboBox',
    'LicenseViewer',
)

from collections.abc import Callable
from collections.abc import Sequence

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..constants import *


class BetterLineEdit(QLineEdit):
    """A :py:class:`QLineEdit` with an added paste listener."""

    def __init__(self, *args, pasted: Callable | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if pasted is not None:
            vars(self)['pasted'] = pasted

    def pasted(self):
        """Function called when a paste key combo is detected."""

    def keyPressEvent(self, event):
        """Call self.pasted on paste."""
        super().keyPressEvent(event)
        if event.matches(QKeySequence.Paste):
            self.pasted()


class HistoryComboBox(QComboBox):
    """Editable :py:class:`QComboBox` acting as a history wrapper over :py:class:`BetterLineEdit`; has no duplicate values."""
    line_edit_class = BetterLineEdit

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setEditable(True)
        self.setDuplicatesEnabled(False)
        self.setLineEdit(self.line_edit_class(parent=self))

    # noinspection PyTypeChecker
    def addItem(self, text: str, **kwargs) -> None:
        """Filters already-present strings from being added using addItem.

        addItem(self,
        icon: Union[PySide6.QtGui.QIcon, PySide6.QtGui.QPixmap],
        text: str,
        userData: Any = Invalid(typing.Any)
        ) -> None
        addItem(self,
        text: str,
        userData: Any = Invalid(typing.Any)
        ) -> None"""
        result = self.findText(text, Qt.MatchFlag.MatchFixedString)
        if result != -1:
            self.removeItem(result)

        super().addItem(text, **kwargs)

    def addItems(self, texts: Sequence[str]) -> None:
        """self.addItem for text in texts."""
        for text in texts:
            self.addItem(text)


class LicenseViewer(QWidget):
    """Widget that formats and shows the project's license file."""

    def __init__(self, *args, **kwargs) -> None:
        """Create a new LicenseViewer. Gets license from the HI_RESOURCE_PATH/LICENSE file

        Has a fixed size of 750x380.
        """
        super().__init__(*args, **kwargs)
        self.setWindowTitle('License Viewer')
        self.setWindowIcon(QIcon(str(HI_RESOURCE_PATH / 'icons/copyright.ico')))
        self.resize(QSize(750, 380))
        self.setFixedSize(self.size())

        with (HI_RESOURCE_PATH / 'LICENSE').open(mode='r', encoding='utf8') as file:
            license_text = QTextEdit()
            for line in file.readlines():
                license_text.append(line)

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(license_text)

        block_format = QTextBlockFormat()
        block_format.setLineHeight(40, QTextBlockFormat.LineHeightTypes.ProportionalHeight)
        cursor = license_text.textCursor()
        cursor.clearSelection()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(block_format)
        license_text.setFont(QFont('consolas', 12))
        license_text.setDisabled(True)
