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

from PySide6.QtWidgets import *

from ..lang import Translator


def _return_arg(__arg: ..., /) -> ...:
    """Return the singular argument unchanged."""
    return __arg


def init_widgets(widget_data: dict[QWidget: dict[str: str | Iterable[str] | Callable]], translator: Translator | None = None) -> None:
    """Initialize widgets with the given data. Translation key strings are evaluated using the given translator, if provided.

    widget_data should be a dictionary structured like this::

        {
            widget1: {'text': 'some.translation.key', 'clicked': on_click},
            widget2: {'text': 'some.translation.key'},
            widget3: {'text': string_value, 'pasted': on_paste, 'returnPressed': on_return},
            widget4: {'activated': when_activated, 'items': (
                f'The Number "{i}"' for i in range(1, 11)
            )}
        }

    :param widget_data: Dictionary containing data used to initialize basic widget values.
    :param translator: Translator used for translation key evaluation.
    """
    if not translator:
        # If translator is unavailable, return any string/key unchanged.
        translator = _return_arg

    for widget, data in widget_data.items():
        # Translate widget texts
        if data.get('text') is not None:
            widget.setText(translator(data['text']))
        # Translate dropdown items
        if data.get('items') is not None:
            widget.addItems(translator(key) for key in data['items'])
        # Connect any slots with their respective function call
        for signal in ('activated', 'clicked', 'pasted', 'returnPressed'):
            if data.get(signal) is not None:
                getattr(widget, signal).connect(data[signal])


def scroll_to_top(widget: QTextEdit) -> None:
    """Move text cursor to top of text editor."""
    cursor = widget.textCursor()
    cursor.setPosition(0)
    widget.setTextCursor(cursor)
