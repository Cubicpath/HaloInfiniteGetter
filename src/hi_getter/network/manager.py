###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Package for managing outgoing requests for hi_getter."""

__all__ = (
    'NetworkWrapper',
)

import datetime
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any
from typing import TypeAlias

from PySide6.QtCore import *
from PySide6.QtNetwork import *

from .structures import CaseInsensitiveDict


_NetworkReplyConsumer: TypeAlias = Callable[[QNetworkReply], None]


class NetworkWrapper:
    """Wrapper for the QNetworkAccessManager."""
    KNOWN_HEADERS: CaseInsensitiveDict[tuple[QNetworkRequest.KnownHeaders, type]] = CaseInsensitiveDict({
        'Content-Disposition':  (QNetworkRequest.ContentDispositionHeader, str),
        'Content-Length':       (QNetworkRequest.ContentLengthHeader, str),
        'Content-Type':         (QNetworkRequest.ContentTypeHeader, bytes),
        'Cookie':               (QNetworkRequest.CookieHeader, QNetworkCookie),
        'ETag':                 (QNetworkRequest.ETagHeader, str),
        'If-Match':             (QNetworkRequest.IfMatchHeader, QStringListModel),
        'If-Modified-Since':    (QNetworkRequest.IfModifiedSinceHeader, QDateTime),
        'If-None-Match':        (QNetworkRequest.IfNoneMatchHeader, QStringListModel),
        'Last-Modified':        (QNetworkRequest.LastModifiedHeader, QDateTime),
        'Location':             (QNetworkRequest.LocationHeader, QUrl),
        'Server':               (QNetworkRequest.ServerHeader, str),
        'Set-Cookie':           (QNetworkRequest.SetCookieHeader, QNetworkCookie),
        'User-Agent':           (QNetworkRequest.UserAgentHeader, str),
    })

    def __init__(self):
        """Initialize the NetworkWrapper."""
        self.manager = QNetworkAccessManager(None)

    def _translate_header_value(self, header: str, value: Any):
        old_value = value
        match self.KNOWN_HEADERS[header][1].__name__:
            case 'str':
                value = str(old_value)

            case 'bytes':
                if isinstance(old_value, str):
                    value = old_value.encode('utf8')

            case 'QDateTime':
                value = QDateTime()
                if isinstance(old_value, (datetime.datetime, datetime.date, datetime.time)):
                    # Translate datetime objects to a string
                    if not isinstance(old_value, datetime.datetime):
                        date: datetime.date = datetime.datetime.now().date() if isinstance(old_value, datetime.time) else old_value
                        time: datetime.time = datetime.datetime.now().time() if isinstance(old_value, datetime.date) else old_value
                        old_value = datetime.datetime.fromisoformat(f'{date.isoformat()}T{time.isoformat()}')

                    old_value = old_value.isoformat()
                # Translate string to QDateTime object
                value.fromString(str(old_value), Qt.DateFormat.ISODateWithMs)

            case 'QNetworkCookie':
                cookie_list: list[QNetworkCookie] = list()
                match old_value[0] if old_value else None:
                    # Translate dictionaries
                    case Mapping():
                        for cookie in old_value:
                            for name, _value in cookie.items():
                                cookie_list.append(QNetworkCookie(name.encode('utf8'), _value.encode('utf8')))
                    # Translate tuples, lists, etc. that contain two strings (name and value)
                    case Sequence():
                        for cookie in old_value:
                            cookie_list.append(QNetworkCookie(cookie[0].encode('utf8'), cookie[1].encode('utf8')))
                value = cookie_list

            case 'QStringListModel':
                value = [str(item) for item in old_value]

            case 'QUrl':
                if not isinstance(old_value, QUrl):
                    value = QUrl(str(old_value))
        return value

    def request(self, method: str, url: QUrl | str,
                # params: dict | None = None,
                data: bytes | None = None,
                headers: dict | None = None,
                finished: _NetworkReplyConsumer | None = None):
        """Send an HTTP request to the given URL with the given data."""
        headers = headers if headers is not None else {}

        url = QUrl(url)
        request = QNetworkRequest(url)

        for name, value in headers.items():
            if name in self.KNOWN_HEADERS:
                value = self._translate_header_value(name, value)
                request.setHeader(header=self.KNOWN_HEADERS[name][0], value=value)
                continue
            request.setRawHeader(headerName=name, value=value)

        io_data = QBuffer(self.manager)
        io_data.open(QBuffer.ReadWrite)
        io_data.write(data)
        io_data.seek(0)

        reply = self.manager.sendCustomRequest(request, method.encode('utf8'), data=io_data)
        if finished is not None:
            reply.finished.connect(finished)
        return reply

    def get(self, url: QUrl | str, **kwargs):
        """Create and send a request with the GET HTTP method."""
        return self.request(method='GET', url=url, **kwargs)
