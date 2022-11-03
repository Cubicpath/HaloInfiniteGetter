###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""ReadmeViewer implementation."""
from __future__ import annotations

__all__ = (
    'ChangelogViewer',
)

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtNetwork import *
from PySide6.QtWidgets import *

from ...utils.gui import init_layouts
from ...utils.gui import init_objects
from ..app import app
from ..app import tr
from ..widgets import ExternalTextBrowser


class ChangelogViewer(QWidget):
    """Widget that formats and shows the project's README.md, stored in the projects 'Description' metadata tag."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle(tr('gui.changelog_viewer.title'))
        self.setWindowIcon(app().get_theme_icon('message_information') or self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.resize(QSize(750, 750))

        self.changelog_url: str = 'https://raw.githubusercontent.com/Cubicpath/HaloInfiniteGetter/master/CHANGELOG.md'
        self.text_browser: ExternalTextBrowser
        self._init_ui()

    def _init_ui(self) -> None:
        self.text_browser = ExternalTextBrowser(self)

        init_objects({
            self.text_browser: {
                'font': QFont(self.text_browser.font().family(), 10),
                'openExternalLinks': True
            }
        })

        app().init_translations({
            self.setWindowTitle: 'gui.changelog_viewer.title'
        })

        init_layouts({
            # Main layout
            QVBoxLayout(self): {
                'items': [self.text_browser]
            }
        })

        self.text_browser.inject_markdown_anchors = False
        self.update_changelog()

    def update_changelog(self) -> None:
        """Updates the displayed text to the data from the changelog url."""

        def handle_reply(reply: QNetworkReply):
            text: str = reply.readAll().data().decode('utf8')
            # Add separators between versions and remove primary header
            text = '## ' + '\n-----\n## '.join(text.split('\n## ')[1:])

            # The Markdown Renderer doesn't accept headers with ref_links, so remove them
            new_lines = []
            for line in text.splitlines():
                if line.startswith('## '):
                    line = line.replace('[', '', 1).replace(']', '', 1)

                new_lines.append(line)
            text = '\n'.join(new_lines)

            self.text_browser.set_hot_reloadable_text(text, 'markdown')
            reply.deleteLater()

        app().session.get(self.changelog_url, finished=handle_reply)
