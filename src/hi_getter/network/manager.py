###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Package for managing outgoing requests for hi_getter."""

__all__ = (
    'NetworkWrapper',
)

from PySide6.QtNetwork import *


class NetworkWrapper:
    """Wrapper for the QNetworkAccessManager."""

    def __init__(self):
        """Initialize the NetworkWrapper."""
        self.manager = QNetworkAccessManager()

    def get(self, url):
        """Get the data from the given URL."""
        reply = self.manager.get(QNetworkRequest(QUrl(url)))
        return reply
