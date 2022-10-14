###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utilities for GUI elements."""
from __future__ import annotations

__all__ = (
    'add_menu_items',
    'delete_layout_widgets',
    'icon_from_bytes',
    'init_objects',
    'scroll_to_top',
    'set_or_swap_icon',
)

from collections.abc import Iterable
from collections.abc import Sequence
from typing import Any

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


_menu_type_map = {
    str: QMenu.addSection,
    QMenu: QMenu.addMenu,
    QAction: QMenu.addAction,
}


def add_menu_items(menu: QMenu, items: Sequence[str | QAction | QMenu]) -> None:
    """Add items to the given menu.

    This uses the associated :py:class:`QMenu` methods for each object's type::

        str: QMenu.addSection,
        QMenu: QMenu.addMenu,
        QAction: QMenu.addAction,


    :param menu: The menu to add items to.
    :param items: The items to add to the menu.
    """
    for obj in items:
        # Find the item's type and associated method.
        for item_type, meth in _menu_type_map.items():

            if isinstance(obj, item_type):
                # Run method and go to next item.
                meth(menu, obj)
                break


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
def init_objects(object_data: dict[QObject, dict[str, Any]]) -> None:
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
    """
    # Initialize widget attributes
    for obj, data in object_data.items():
        special_keys = ('items', 'size')
        items, size_dict = (data.get(key) for key in special_keys)

        # Find setter method for all non specially-handled keys
        for key, val in data.items():
            if key in special_keys:
                continue  # Skip special keys

            if hasattr(obj, key):
                # Check if key is a signal on widget
                # If so, connect it to the given function
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

        if items is not None:
            if not isinstance(obj, QComboBox):
                # Set directly for non-dropdowns
                obj.setItems(items)
            else:
                if hasattr(obj, 'addItems'):
                    obj.addItems(items)
                else:
                    for key in items:
                        obj.addItem(key)

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
