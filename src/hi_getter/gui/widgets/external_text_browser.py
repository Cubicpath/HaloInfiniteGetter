###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""ExternalTextBrowser implementation."""
from __future__ import annotations

__all__ = (
    'ExternalTextBrowser',
)

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...models import DeferredCallable
from ..app import app


# FIXME: Add a timer for hot reloading
class ExternalTextBrowser(QTextBrowser):
    """:py:class:`QTextBrowser` with ability to map keys to :py:class:`Callable`'s.

    Also supports external image loading and caching.
    """
    remote_image_cache: dict[str, bytes] = {}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.anchorClicked.connect(lambda url: self.scrollToAnchor(url.toDisplayString().lstrip('#')))

        # default factory producing empty DeferredCallables
        self.key_callable_map: defaultdict[int, Callable] = defaultdict(DeferredCallable)
        self.cached_text: str = ''
        self.cached_type: str = ''

    def hot_reload(self) -> None:
        """Reload cached text using the cached type's function."""
        # Remember scroll position
        scroll = self.verticalScrollBar().sliderPosition()

        # Reload all resources and replace text with cached text
        self.clear()
        match self.cached_type:
            case 'markdown':
                self.setMarkdown(self.cached_text)
            case 'html':
                self.setHtml(self.cached_text)
            case 'text':
                self.setPlainText(self.cached_text)
        self.verticalScrollBar().setSliderPosition(scroll)

    def set_hot_reloadable_text(self, text: str, text_type: str) -> None:
        """Set text that is designated to be hot-reloadable."""

        # Inject html anchors to markdown headers to allow relative linking.
        if text_type == 'markdown':
            lines:     list[str] = text.splitlines()
            lines_new: list[str] = []

            # Find headers and add relative anchors
            for i, line in enumerate(lines):
                simple_str: str = line.strip().replace(' ', '-').replace(':', '').lstrip('#').strip('-').lower()

                has_hashtag:   bool = line.strip().startswith('#')
                has_underline: bool = line and (i < len(lines) - 1) and any(
                    # Line must end and begin with the respective underline
                    lines[i + 1].strip().startswith(a) and
                    lines[i + 1].strip().endswith(a) for a in ('-', '=')
                )

                # If line has a header marker, append it with an anchor tag and add it to the new list.
                # Otherwise, append the unchanged line to the new list.
                if has_hashtag or has_underline:
                    lines_new.append(f'{line} <a name="{simple_str}" href="#{simple_str}">§</a>')
                    continue
                lines_new.append(line)

            text = '\n'.join(lines_new)

        self.cached_text = text
        self.cached_type = text_type
        self.hot_reload()

    def loadResource(self, resource_type: QTextDocument.ResourceType, url: QUrl) -> Any:
        """Load a resource from an url.

        If resource type is an image and the url is external, download it using requests and cache it.
        """
        if resource_type == QTextDocument.ResourceType.ImageResource and not url.isLocalFile():
            image:      QImage = QImage()
            url_string: str = url.toDisplayString()
            if url_string not in self.remote_image_cache:
                reply = app().session.get(url)

                def handle_reply():
                    data: bytes = reply.readAll()
                    image.loadFromData(data)
                    self.remote_image_cache[url_string] = data

                    if self.cached_type:
                        self.hot_reload()
                    reply.deleteLater()

                reply.finished.connect(handle_reply)
            else:
                image.loadFromData(self.remote_image_cache[url_string])
            return image

        return super().loadResource(int(resource_type), url)

    def setLineWrapMode(self, mode: int | QTextEdit.LineWrapMode) -> None:
        """Set the line wrap mode. Allows use of ints."""
        super().setLineWrapMode(QTextEdit.LineWrapMode(mode))

    # noinspection PyTypeChecker
    def connect_key_to(self, key: Qt.Key, func: Callable) -> None:
        """Connect a :py:class:`Callable` to a key press."""
        self.key_callable_map[int(key)] = func

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Execute :py:class:`Callable` mapped to the key press."""
        super().keyPressEvent(event)
        self.key_callable_map[event.key()]()
        event.accept()
