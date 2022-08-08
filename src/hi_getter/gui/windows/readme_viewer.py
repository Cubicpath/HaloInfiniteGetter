###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""ReadmeViewer implementation."""
from __future__ import annotations

__all__ = (
    'ReadmeViewer',
)

from importlib.metadata import metadata
from typing import Final

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ..app import app
from ..app import tr
from ..widgets import ExternalTextBrowser


# noinspection PyArgumentList
class ReadmeViewer(QWidget):
    """Widget that formats and shows the project's README.md, stored in the projects 'Description' metadata tag."""
    README_TEXT: Final[str] = metadata(HI_PACKAGE_NAME)['Description']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle(tr('gui.readme_viewer.title'))
        self.setWindowIcon(app().get_theme_icon('message_information') or self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.resize(QSize(750, 750))
        self.readme_viewer: ExternalTextBrowser
        self._init_ui()

    def _dummy_func(self) -> None:
        """Must exist otherwise ReadmeViewer instances will be garbage collected through Context Menu deletion. Don't ask, just accept."""

    def _init_ui(self) -> None:
        self.readme_viewer = ExternalTextBrowser(self)
        close_button = QPushButton("Close", self, clicked=self.close)

        self.readme_viewer.connect_key_to(Qt.Key_Any, self._dummy_func)  # Refer to self._dummy_func

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        layout.addWidget(self.readme_viewer)
        layout.addWidget(close_button)

        self.readme_viewer.setOpenExternalLinks(True)
        self.readme_viewer.set_hot_reloadable_text(self.README_TEXT, 'markdown')
        self.readme_viewer.setFont(QFont(self.readme_viewer.font().family(), 10))
        close_button.setMinimumHeight(40)
        close_button.setFont(QFont(close_button.font().family(), 16))

    def closeEvent(self, event: QCloseEvent) -> None:
        """Manually signal the readme_viewer for garbage collection."""
        super().closeEvent(event)
        self.readme_viewer.deleteLater()
        event.accept()
