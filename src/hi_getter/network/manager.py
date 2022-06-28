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
from json import dumps as json_dumps
from pathlib import Path
from typing import Any
from typing import TypeAlias

from PySide6.QtCore import *
from PySide6.QtNetwork import *

from ..models import DeferredCallable
from .structures import CaseInsensitiveDict
from .utils import dict_to_query
from .utils import encode_url_params
from .utils import query_to_dict

_NetworkReplyConsumer: TypeAlias = Callable[[QNetworkReply], None]


class NetworkSession:
    """Requests-like wrapper over a QNetworkAccessManager."""
    KNOWN_HEADERS: CaseInsensitiveDict[tuple[QNetworkRequest.KnownHeaders, type]] = CaseInsensitiveDict({
        'Content-Disposition':  (QNetworkRequest.ContentDispositionHeader, str),
        'Content-Type':         (QNetworkRequest.ContentTypeHeader, str),
        'Content-Length':       (QNetworkRequest.ContentLengthHeader, bytes),
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
        """Initialize the NetworkSession."""
        self._headers:                 CaseInsensitiveDict[Any] = CaseInsensitiveDict()
        self.manager:                  QNetworkAccessManager = QNetworkAccessManager(None)
        self.default_redirect_policy:  QNetworkRequest.RedirectPolicy = QNetworkRequest.ManualRedirectPolicy

    @property
    def cookies(self) -> dict[str, str]:
        """Dictionary representation of the internal :py:class:`QNetworkCookieJar`."""
        return {cookie.name().toStdString(): cookie.value().toStdString() for cookie in self.manager.cookieJar().allCookies()}

    @cookies.deleter
    def cookies(self) -> None:
        """Clear cookies on delete."""
        self.clear_cookies()

    @property
    def headers(self) -> CaseInsensitiveDict[Any]:
        """Dictionary containing the default session headers."""
        return self._headers

    @headers.setter
    def headers(self, value: Mapping) -> None:
        """Translate any mapping value to a CaseInsensitiveDict for use as headers."""
        if not isinstance(value, Mapping):
            raise TypeError(f'NetworkSession headers must be a Mapping, not {type(value)}')

        self._headers = CaseInsensitiveDict(value)

    @headers.deleter
    def headers(self) -> None:
        """Clear headers on delete."""
        self._headers.clear()

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

    def clear_cookies(self, domain: str | None = None, path: str | None = None, name: str | None = None) -> bool:
        """Clear some cookies. Functionally equivalent to http.cookiejar.clear.

        Invoking this method without arguments will clear all cookies.  If
        given a single argument, only cookies belonging to that domain will be
        removed.  If given two arguments, cookies belonging to the specified
        path within that domain are removed.  If given three arguments, then
        the cookie with the specified name, path and domain is removed.

        :return: True if a cookie was deleted.
        """

        def deletion_predicate(cookie: QNetworkCookie):
            if name is not None:      # 3 args
                return cookie.name().toStdString() == name and cookie.domain() == domain and cookie.path() == path
            elif path is not None:    # 2 args
                return cookie.domain() == domain and cookie.path() == path
            elif domain is not None:  # 1 arg
                return cookie.domain() == domain
            else:                     # 0 args
                return True

        results = []
        for _cookie in self.manager.cookieJar().allCookies():
            if deletion_predicate(_cookie):
                results.append(self.manager.cookieJar().deleteCookie(_cookie))

        return any(results)

    def set_cookie(self, name: str, value: str, domain: str, path: str | None = None) -> bool:
        """Create a new cookie with the given date.

        Replaces a pre-existing cookie with the same identifier if it exists.

        :return: True if the cookie was set.
        """
        cookie = QNetworkCookie(name=name.encode('utf8'), value=value.encode('utf8'))
        cookie.setDomain(domain)
        cookie.setPath(path or '/')
        return self.manager.cookieJar().insertCookie(cookie)

    def request(self, method: str, url: QUrl | str,
                params: dict[str, str] | list[tuple[str, str]] | None = None,
                data: bytes | dict[str, str] | list[tuple[str, str]] | None = None,
                headers: dict[str, Any] | list[tuple[str, Any]] | None = None,
                cookies: dict[str, str] | list[tuple[str, str]] | None = None,
                # TODO: Finish requests-like implementation
                # files: dict[str, Any] | None = None,
                # auth: tuple[str, str] | None = None,
                # timeout: float | tuple[float, float] | None = None,
                allow_redirects: bool = True,
                proxies: dict[str, str] | None = None,
                # hooks: dict[str, Callable | Iterable[Callable]] | None = None,
                # stream: bool | None = None,
                verify: bool | str | None = None,
                cert: str | tuple[str, str] | None = None,
                json: dict[str, Any] | None = None,
                finished: _NetworkReplyConsumer | None = None):
        """Send an HTTP request to the given URL with the given data."""

        # Setup values for the request

        params = {} if params is None else params
        headers = {} if headers is None else headers
        cookies = {} if cookies is None else cookies

        # Translate dictionary-compatible tuple pair lists to dictionaries
        # Ex: [('name', 'value'), ('key': 'value')] -> {'name': 'value', 'key': 'value'}
        for tuple_list in ('params', 'data', 'headers', 'cookies'):
            if isinstance(vars()[tuple_list], list):
                vars()[tuple_list] = {key: value for key, value in vars()[tuple_list]}

        request_url:     QUrl = QUrl(url)                                              # Ensure url is of type QUrl
        request_params:  dict[str, str] = query_to_dict(request_url.query()) | params  # Override QUrl params with params argument
        request_headers: CaseInsensitiveDict = self.headers.copy() | headers           # Override session headers with headers argument
        request_cookies: dict[str, str] = self.cookies | cookies                       # Override session cookies with cookies argument

        request_url.setQuery(dict_to_query(request_params))

        # HTTP Body

        content_type = None
        body = None

        if data:
            if isinstance(data, dict):
                body = encode_url_params(data).encode('utf8')
                content_type = 'application/x-www-form-urlencoded'

            elif isinstance(data, bytes):
                body = data

        elif json is not None:
            body = json_dumps(json, allow_nan=False).encode('utf8')
            content_type = 'application/json'

        if content_type and 'Content-Type' not in headers:
            headers['Content-Type'] = content_type

        # Cookies

        original_cookie_jar: QNetworkCookieJar = self.manager.cookieJar()
        if cookies:
            self.manager.setCookieJar(QNetworkCookieJar(self.manager))

            for name, value in request_cookies:
                self.set_cookie(name, value, request_url.host())

        request = QNetworkRequest(request_url)

        # SSL Configuration

        ssl_config = QSslConfiguration.defaultConfiguration()

        if isinstance(verify, str):
            ssl_config.setCaCertificates(QSslCertificate.fromPath(verify))

        if isinstance(cert, str):
            ssl_config.setLocalCertificateChain(QSslCertificate.fromPath(cert))
        elif isinstance(cert, tuple):
            # cert is a tuple of (cert_path, key_path)
            ssl_config.setLocalCertificateChain(QSslCertificate.fromPath(cert[0]))
            ssl_config.setPrivateKey(QSslKey(Path(cert[1]).read_bytes(), QSsl.Rsa, QSsl.Pem, QSsl.PrivateKey))

        request.setSslConfiguration(ssl_config)

        # Headers

        for name, value in request_headers.items():
            if name in self.KNOWN_HEADERS:
                value = self._translate_header_value(name, value)
                request.setHeader(self.KNOWN_HEADERS[name][0], value)
                continue

            try:
                encoded_value = bytes(value) if not isinstance(value, str) else value.encode('utf8')
            except TypeError:
                encoded_value = str(value).encode('utf8')

            request.setRawHeader(name.encode('utf8'), encoded_value)

        # Other

        if not allow_redirects:
            self.manager.setRedirectPolicy(QNetworkRequest.ManualRedirectPolicy)

        if proxies is not None:
            for protocol, proxy_url in proxies.items():
                proxy_type: QNetworkProxy.ProxyType
                match protocol:
                    case '':
                        proxy_type = QNetworkProxy.NoProxy
                    case 'ftp':
                        proxy_type = QNetworkProxy.FtpCachingProxy
                    case 'http':
                        proxy_type = QNetworkProxy.HttpProxy
                    case 'socks5':
                        proxy_type = QNetworkProxy.Socks5Proxy
                    case other:
                        raise ValueError(f'proxy protocol "{other}" is not supported.')

                proxy_url = QUrl(proxy_url)
                proxy = QNetworkProxy(proxy_type, proxy_url.host(), proxy_url.port())
                self.manager.setProxy(proxy)

        # Handle Reply
        # Since this is an asynchronous request, we don't immediately have the reply data.

        reply: QNetworkReply = self.manager.sendCustomRequest(request, method.encode('utf8'), data=body)

        if verify is False:
            reply.ignoreSslErrors()

        if finished is not None:
            reply.finished.connect(DeferredCallable(finished, reply))

        if self.manager.cookieJar() is not original_cookie_jar:
            self.manager.setCookieJar(original_cookie_jar)
        if self.manager.redirectPolicy() != self.default_redirect_policy:
            self.manager.setRedirectPolicy(self.default_redirect_policy)

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
