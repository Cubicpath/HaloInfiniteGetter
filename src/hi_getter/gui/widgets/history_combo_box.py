###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""HistoryComboBox implementation."""
from __future__ import annotations

__all__ = (
    'HistoryComboBox',
)

from collections.abc import Sequence

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .paste_line_edit import PasteLineEdit


class HistoryComboBox(QComboBox):
    """Editable :py:class:`QComboBox` acting as a history wrapper over :py:class:`BetterLineEdit`; has no duplicate values."""
    line_edit_class = PasteLineEdit

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

    def addItems(self, texts: Sequence[str], **_) -> None:
        """self.addItem for text in texts."""
        for text in texts:
            self.addItem(text)
