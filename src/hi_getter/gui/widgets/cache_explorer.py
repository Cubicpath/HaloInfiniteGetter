###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""CacheExplorer implementation."""
from __future__ import annotations

__all__ = (
    'CacheExplorer',
)

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ...constants import *
from ...utils.gui import init_objects


class CacheExplorer(QTreeView):
    """:py:class:`QTreeView` used to interact with the app's cache directory.

    Has a native :py:class:`QFileSystemModel` and item context menu.
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.customContextMenuRequested.connect(self.on_custom_context_menu)
        self.doubleClicked.connect(self.on_double_click)

        init_objects({
            (model := QFileSystemModel(self)): {
                'readOnly': True,
                'rootPath': str(HI_CACHE_PATH.absolute()),
                'nameFilters': [f'*.{ext}' for ext in SUPPORTED_IMAGE_EXTENSIONS],
                'nameFilterDisables': True
            },

            self: {
                'model': model,
                'rootIndex': model.index(str(HI_CACHE_PATH.absolute())),
                'contextMenuPolicy': Qt.CustomContextMenu
            }
        })

        for index in (1, 2):  # SIZE and FILE TYPE
            self.hideColumn(index)

    def on_custom_context_menu(self, point: QPoint) -> None:
        """Function called when the customContextMenuRequested signal is emitted.

        :param point: The point to place the context menu.
        """

    def on_double_click(self, model_index: QModelIndex) -> None:
        """Function called when the doubleClicked signal is emitted.

        :param model_index: The model index which was double-clicked.
        """
