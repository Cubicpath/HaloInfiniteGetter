###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing utils for GUI elements."""

__all__ = (
    'init_objects',
    'scroll_to_top',
)

from collections.abc import Iterable
from collections.abc import Sequence
from typing import Any

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ..lang import Translator


def _return_arg(__arg: ..., /) -> ...:
    """Return the singular argument unchanged."""
    return __arg


def delete_layout_widgets(layout: QLayout) -> None:
    """Delete all widgets in a layout."""
    while (item := layout.takeAt(0)) is not None:
        item.widget().deleteLater()


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
    for widget, data in object_data.items():
        special_keys = ('items', 'size', 'text',)
        items, size, text = (data.get(key) for key in special_keys)

        # Find setter method for all non specially-handled keys
        for key, val in data.items():
            if key in special_keys:
                continue

            # Check if key is a signal on widget
            # If so, connect it to the given function
            if hasattr(widget, key):
                attribute = getattr(widget, key)
                if isinstance(attribute, SignalInstance):
                    if isinstance(val, Iterable):
                        for slot in val:
                            attribute.connect(slot)
                    else:
                        attribute.connect(val)
                    continue

            # Else call setter to update value
            # Capitalize first character of key
            setter = f'set{key[0].upper()}{key[1:]}'
            getattr(widget, setter)(val)

        # Translate dropdown items
        if items is not None:
            widget.addItems(translator(key) for key in items)

        # Set size
        if size is not None:
            for s_type in ('minimum', 'maximum', 'fixed'):
                if size.get(s_type) is not None:
                    if isinstance(size.get(s_type), QSize):
                        # For PySide6.QtCore.QSize objects
                        getattr(widget, f'set{s_type.title()}Size')(size[s_type])
                    elif isinstance(size.get(s_type), Sequence):
                        # For lists, tuples, etc. Set width and height separately.
                        # None can be used rather than int to skip a dimension.
                        if size.get(s_type)[0]:
                            getattr(widget, f'set{s_type.title()}Width')(size[s_type][0])
                        if size.get(s_type)[1]:
                            getattr(widget, f'set{s_type.title()}Height')(size[s_type][1])

        # Translate widget texts
        if text is not None:
            widget.setText(translator(text))


def scroll_to_top(widget: QTextEdit) -> None:
    """Move text cursor to top of text editor."""
    cursor = widget.textCursor()
    cursor.setPosition(0)
    widget.setTextCursor(cursor)
