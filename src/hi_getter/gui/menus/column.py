###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Column menu implementation."""
from __future__ import annotations

__all__ = (
    'ColumnContextMenu',
)

from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...models import DeferredCallable
from ...utils.gui import add_menu_items
from ...utils.gui import init_objects
from ..app import app


class ColumnContextMenu(QMenu):
    """A general context menu for hiding/unhiding columns in a :py:class:`QTreeView`."""

    def __init__(self, parent: QTreeView, disabled_indices: set[int] | None = None):
        super().__init__(parent)

        disabled_indices = set() if disabled_indices is None else disabled_indices

        icons = (
            # Not Hidden
            app().get_theme_icon('checkbox_checked') or
            self.style().standardIcon(QStyle.SP_DialogApplyButton),

            # Hidden
            app().get_theme_icon('checkbox_unchecked') or
            self.style().standardIcon(QStyle.SP_DialogCancelButton),
        )

        items: list[str | QAction] = ['Columns']
        for i, hidden in enumerate([parent.isColumnHidden(count) for count in range(parent.model().columnCount())]):
            init_objects({
                (action := QAction(self)): {
                    'disabled': i in disabled_indices,
                    'text': parent.model().headerData(i, Qt.Orientation.Horizontal),
                    'icon': icons[hidden],
                    'triggered': DeferredCallable(parent.setColumnHidden, i, not hidden)
                }
            })

            items.append(action)

        add_menu_items(self, items)
