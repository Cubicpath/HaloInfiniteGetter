###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Package for managing outgoing requests for hi_getter."""

__all__ = (
    'NetworkSession',
)

import datetime
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any
from typing import TypeAlias

from PySide6.QtCore import *
from PySide6.QtNetwork import *

from ..models import DeferredCallable
from .structures import CaseInsensitiveDict
from .utils import dict_to_query

_NetworkReplyConsumer: TypeAlias = Callable[[QNetworkReply], None]


class NetworkSession:
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

        # Match the known-header's value name and translate value to that type.
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

    def clear_cookies(self, domain: str | None = None, path: str | None = None, name: str | None = None, /) -> bool:
        """Clear some cookies. Functionally equivalent to http.cookiejar.clear.

        Invoking this method without arguments will clear all cookies.  If
        given a single argument, only cookies belonging to that domain will be
        removed.  If given two arguments, cookies belonging to the specified
        path within that domain are removed.  If given three arguments, then
        the cookie with the specified name, path and domain is removed.

        :return: True if a cookie was deleted, otherwise False.
        """

        def deletion_predicate(cookie: QNetworkCookie):
            if name is not None:  # 3 args
                return cookie.name().toStdString() == name and cookie.domain() == domain and cookie.path() == path
            elif path is not None:  # 2 args
                return cookie.domain() == domain and cookie.path() == path
            elif domain is not None:  # 1 arg
                return cookie.domain() == domain
            else:  # No args
                return True

        results = []
        for _cookie in self.manager.cookieJar().allCookies():
            if deletion_predicate(_cookie):
                results.append(self.manager.cookieJar().deleteCookie(_cookie))

        return any(results)

    def set_cookie(self, name: str, value: str, domain: str, path: str | None = None) -> bool:
        """Create a new cookie with the given date.

        Replaces a pre-existing cookie with the same identifier if it exists.
        """
        cookie = QNetworkCookie(name=name.encode('utf8'), value=value.encode('utf8'))
        cookie.setDomain(domain)
        cookie.setPath(path or '/')
        return self.manager.cookieJar().insertCookie(cookie)

    def request(self, method: str, url: QUrl | str,
                params: dict[str, str] | None = None,
                data: bytes | None = None,
                headers: dict[str, Any] | None = None,
                cookies: dict[str, str] | None = None,
                # TODO: Finish requests-like implementation
                # files: dict[str, Any] | None = None,
                # auth: tuple[str, str] | None = None,
                # timeout: float | tuple[float, float] | None = None,
                # allow_redirects: bool = True,
                # proxies: dict[str, str] | None = None,
                # hooks: dict[str, Callable | Iterable[Callable]] | None = None,
                # stream: bool | None = None,
                # verify: bool | str | None = None,
                # cert: str | tuple[str, str] | None = None,
                # json: dict[str, Any] | None = None,
                finished: _NetworkReplyConsumer | None = None):
        """Send an HTTP request to the given URL with the given data."""
        params = {} if params is None else params
        headers = {} if headers is None else headers
        cookies = {} if cookies is None else cookies

        url = QUrl(url)
        url.setQuery(dict_to_query(params))

        original_cookies: QNetworkCookieJar = self.manager.cookieJar()
        if cookies:
            self.manager.setCookieJar(QNetworkCookieJar())

            for name, value in cookies:
                self.set_cookie(name, value, url.host())

        request = QNetworkRequest(url)

        for name, value in headers.items():
            if name in self.KNOWN_HEADERS:
                value: Any = self._translate_header_value(name, value)
                request.setHeader(header=self.KNOWN_HEADERS[name][0], value=value)
                continue

            try:
                encoded_value = bytes(value) if not isinstance(value, str) else value.encode('utf8')
            except TypeError:
                encoded_value = str(value).encode('utf8')

            request.setRawHeader(headerName=name.encode('utf8'), value=encoded_value)

        io_data = QBuffer(self.manager)
        io_data.open(QBuffer.ReadWrite)
        io_data.write(data)
        io_data.seek(0)

        reply: QNetworkReply = self.manager.sendCustomRequest(request, method.encode('utf8'), data=io_data)
        if finished is not None:
            reply.finished.connect(DeferredCallable(finished, reply))

        self.manager.setCookieJar(original_cookies)

        return reply

    def get(self, url: QUrl | str, **kwargs):
        """Create and send a request with the GET HTTP method."""
        return self.request(method='GET', url=url, **kwargs)

    def head(self, url: QUrl | str, **kwargs):
        """Create and send a request with the HEAD HTTP method."""
        return self.request(method='HEAD', url=url, **kwargs)

    def post(self, url: QUrl | str, **kwargs):
        """Create and send a request with the POST HTTP method."""
        return self.request(method='POST', url=url, **kwargs)

    def put(self, url: QUrl | str, **kwargs):
        """Create and send a request with the PUT HTTP method."""
        return self.request(method='PUT', url=url, **kwargs)

    def delete(self, url: QUrl | str, **kwargs):
        """Create and send a request with the DELETE HTTP method."""
        return self.request(method='DELETE', url=url, **kwargs)

    def patch(self, url: QUrl | str, **kwargs):
        """Create and send a request with the PATCH HTTP method."""
        return self.request(method='PATCH', url=url, **kwargs)
