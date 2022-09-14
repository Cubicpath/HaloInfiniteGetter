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
from ...utils.gui import init_objects
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

    def _init_ui(self) -> None:
        self.readme_viewer = ExternalTextBrowser(self)

        init_objects({
            (close_button := QPushButton(self)): {
                'size': {'minimum': (None, 40)},
                'font': QFont(close_button.font().family(), 16),
                'clicked': self.close
            },

            self.readme_viewer: {
                'font': QFont(self.readme_viewer.font().family(), 10),
                'openExternalLinks': True
            }
        })

        app().init_translations({
            self.setWindowTitle: 'gui.readme_viewer.title',

            close_button.setText: 'gui.readme_viewer.close'
        })

        layout = QVBoxLayout(self)
        layout.addWidget(self.readme_viewer)
        layout.addWidget(close_button)

        self.readme_viewer.set_hot_reloadable_text(self.README_TEXT, 'markdown')