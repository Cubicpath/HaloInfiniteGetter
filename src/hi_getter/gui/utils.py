###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing utils for GUI elements."""

__all__ = (
    'delete_layout_widgets',
    'icon_from_bytes',
    'init_objects',
    'PARENT_PACKAGE',
    'scroll_to_top',
    'set_or_swap_icon',
)

from collections.abc import Iterable
from collections.abc import Sequence
from typing import Any
from typing import Final

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..lang import Translator

PARENT_PACKAGE: Final[str] = __package__.split('.', maxsplit=1)[0]


def _return_arg(__arg: ..., /) -> ...:
    """Return the singular positional argument unchanged."""
    return __arg


def delete_layout_widgets(layout: QLayout) -> None:
    """Delete all widgets in a layout."""
    while (item := layout.takeAt(0)) is not None:
        item.widget().deleteLater()


def icon_from_bytes(data: bytes) -> QIcon:
    """Create a :py:class:`QIcon` from bytes using a :py:class:`QPixmap` as a proxy."""
    pixmap = QPixmap()
    pixmap.loadFromData(data)
    icon = QIcon(pixmap)
    return icon


# noinspection PyUnresolvedReferences
def init_objects(object_data: dict[QObject, dict[str, Any]], translator: Translator | None = None) -> None:
    """Initialize :py:class:`QObject` attributes with the given data.

    Translation key strings are evaluated using the given translator, if provided.

    widget_data should be a dictionary structured like this::

        {
            widget1: {'text': 'some.translation.key', 'clicked': on_click},
            widget2: {'text': 'some.translation.key', 'size': {'fixed': (None, 400)}},
            widget3: {'text': string_value, 'pasted': on_paste, 'returnPressed': on_return},
            widget4: {'activated': when_activated, 'size': widget_size, 'items': (
                f'The Number "{i}"' for i in range(1, 11)
            )}
        }

    :param object_data: Dictionary containing data used to initialize basic QObject values.
    :param translator: Translator used for translation key evaluation.
    """
    if not translator:
        # If translator is unavailable, return any string/key unchanged.
        translator = _return_arg

    # Initialize widget attributes
    for obj, data in object_data.items():
        special_keys = ('items', 'size', 'text',)
        items, size_dict, text = (data.get(key) for key in special_keys)

        # Find setter method for all non specially-handled keys
        for key, val in data.items():
            if key in special_keys:
                continue  # Skip special keys

            # Check if key is a signal on widget
            # If so, connect it to the given function
            if hasattr(obj, key):
                if isinstance((attribute := getattr(obj, key)), SignalInstance):
                    if isinstance(val, Iterable):
                        for slot in val:
                            attribute.connect(slot)
                    else:
                        attribute.connect(val)
                    continue

            # Else call setter to update value
            # Capitalize first character of key
            setter_name: str = f'set{key[0].upper()}{key[1:]}'
            getattr(obj, setter_name)(val)

        # Translate dropdown items
        if items is not None:
            obj.addItems(translator(key) for key in items)

        # Set size
        if size_dict is not None:
            for size_type in ('minimum', 'maximum', 'fixed'):
                if size_dict.get(size_type) is not None:
                    size: QSize | Sequence[int] = size_dict.get(size_type)
                    if isinstance(size, QSize):
                        # For PySide6.QtCore.QSize objects
                        getattr(obj, f'set{size_type.title()}Size')(size)
                    elif isinstance(size, Sequence):
                        # For lists, tuples, etc. Set width and height separately.
                        # None can be used rather than int to skip a dimension.
                        if size[0]:
                            getattr(obj, f'set{size_type.title()}Width')(size[0])
                        if size[1]:
                            getattr(obj, f'set{size_type.title()}Height')(size[1])

        # Translate widget texts
        if text is not None:
            obj.setText(text)


def scroll_to_top(widget: QTextEdit) -> None:
    """Move text cursor to top of text editor."""
    cursor = widget.textCursor()
    cursor.setPosition(0)
    widget.setTextCursor(cursor)


def set_or_swap_icon(mapping: dict[str, QIcon], key: str, value: QIcon):
    """Given a mapping, replace a QIcon value mapped to the given key with data from another, while keeping the same object references."""
    if key in mapping:
        mapping[key].swap(value)
    else:
        mapping[key] = value
