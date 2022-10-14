###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""ComboBox implementations."""
from __future__ import annotations

__all__ = (
    'ComboBox',
    'HistoryComboBox',
    'TranslatableComboBox',
)

from collections.abc import Iterable

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...utils.gui import init_objects
from ..app import tr
from .paste_line_edit import PasteLineEdit


class ComboBox(QComboBox):
    """Iterable :py:class:`QComboBox`."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._iter_index = -1

    def __iter__(self) -> Iterable[tuple[str, str]]:
        self._iter_index = -1
        return self

    def __next__(self) -> tuple[str, str]:
        """Returns the next item and its data.

        :return: display text and key, packaged into a tuple.
        :raises StopIteration: When iteration index reaches the last item.
        """
        self._iter_index += 1

        if self._iter_index <= self.count() - 1:
            return self.itemText(self._iter_index), self.itemData(self._iter_index)

        raise StopIteration

    def addItems(self, texts: Iterable[str], *args, **kwargs) -> None:
        """self.addItem for text in texts."""
        for text in texts:
            self.addItem(text, *args, **kwargs)


class HistoryComboBox(ComboBox):
    """Editable :py:class:`ComboBox` acting as a history wrapper over :py:class:`PasteLineEdit`; has no duplicate values."""
    line_edit_class = PasteLineEdit

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        init_objects({
            self: {
                'editable': True,
                'duplicatesEnabled': False,
                'lineEdit': self.line_edit_class(parent=self)
            }
        })

    # noinspection PyTypeChecker
    def addItem(self, text: str, *args, **kwargs) -> None:
        """Filters already-present strings from being added using addItem."""
        result = self.findText(text, Qt.MatchFlag.MatchFixedString)
        if result != -1:
            self.removeItem(result)

        super().addItem(text, *args, **kwargs)


class TranslatableComboBox(ComboBox):
    """:py:class:`ComboBox` with translatable items."""

    def translate_items(self, *_) -> None:
        """Translate all items with their respective key."""
        items = tuple(key for _, key in self)
        self.clear()
        self.addItems(items)

    # noinspection PyTypeChecker
    def addItem(self, text: str, *args, **kwargs) -> None:
        """Translates strings from being added using addItem."""
        super().addItem(tr(text), *args, userData=text, **kwargs)
