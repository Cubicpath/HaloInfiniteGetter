###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing utils for GUI elements."""

__all__ = (
    'init_widgets',
    'scroll_to_top',
)

from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Sequence
from typing import Annotated

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ..lang import Translator


def _return_arg(__arg: ..., /) -> ...:
    """Return the singular argument unchanged."""
    return __arg


def init_widgets(widget_data: dict[QWidget, dict[str, str | bool | int | Iterable[str] | Callable | dict[str, QSize | Annotated[Sequence[int | None], 2]]]],
                 translator: Translator | None = None) -> None:
    """Initialize widgets with the given data. Translation key strings are evaluated using the given translator, if provided.

    widget_data should be a dictionary structured like this::

        {
            widget1: {'text': 'some.translation.key', 'clicked': on_click},
            widget2: {'text': 'some.translation.key', 'size': {'fixed': (None, 400)}},
            widget3: {'text': string_value, 'pasted': on_paste, 'returnPressed': on_return},
            widget4: {'activated': when_activated, 'size': widget_size, 'items': (
                f'The Number "{i}"' for i in range(1, 11)
            )}
        }

    :param widget_data: Dictionary containing data used to initialize basic widget values.
    :param translator: Translator used for translation key evaluation.
    """
    if not translator:
        # If translator is unavailable, return any string/key unchanged.
        translator = _return_arg

    # Initialize widget attributes
    for widget, data in widget_data.items():
        disabled, size, font, text, items = data.get('disabled'), data.get('size'), data.get('font'), data.get('text'), data.get('items')

        # Disable widget
        if disabled is not None:
            widget.setDisabled(data['disabled'])

        # Set size
        if size is not None:
            for s_type in ('minimum', 'maximum', 'fixed'):
                if size.get(s_type) is not None:
                    if isinstance(size.get(s_type), QSize):
                        # For PySide6.QtCore.QSize objects
                        getattr(widget, f'set{s_type.title()}Size')(size[s_type][0])
                    elif isinstance(size.get(s_type), Sequence):
                        # For lists, tuples, etc. Set width and height separately.
                        # None can be used rather than int to skip a dimension.
                        if size.get(s_type)[0]:
                            getattr(widget, f'set{s_type.title()}Width')(size[s_type][0])
                        if size.get(s_type)[1]:
                            getattr(widget, f'set{s_type.title()}Height')(size[s_type][1])

        # Change font
        if font is not None and hasattr(widget, 'setFont'):
            widget.setFont(font)

        # Translate widget texts
        if text is not None and hasattr(widget, 'setText'):
            widget.setText(translator(text))

        # Translate dropdown items
        if items is not None and hasattr(widget, 'addItems'):
            widget.addItems(translator(key) for key in items)

        # Connect any slots with their respective function call
        for signal in ('activated', 'clicked', 'pasted', 'returnPressed'):
            if data.get(signal) is not None:
                getattr(widget, signal).connect(data[signal])


def scroll_to_top(widget: QTextEdit) -> None:
    """Move text cursor to top of text editor."""
    cursor = widget.textCursor()
    cursor.setPosition(0)
    widget.setTextCursor(cursor)
