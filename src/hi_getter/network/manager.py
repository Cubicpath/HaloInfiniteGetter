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
from warnings import warn

from PySide6.QtCore import *
from PySide6.QtNetwork import *

from ..models import DeferredCallable
from .structures import CaseInsensitiveDict
from .utils import dict_to_query
from .utils import encode_url_params
from .utils import query_to_dict

_NetworkReplyConsumer: TypeAlias = Callable[[QNetworkReply], None]


class NetworkSession:
    """Requests-like wrapper over a QNetworkAccessManager.

    The following convenience methods are supported:
        - get
        - head
        - post
        - put
        - delete
        - patch
    """
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

    def __init__(self, manager_parent: QObject = None) -> None:
        """Initialize the NetworkSession.

        :param manager_parent: Parent of the QNetworkAccessManager.
        """
        self._headers:                 CaseInsensitiveDict[Any] = CaseInsensitiveDict()
        self.manager:                  QNetworkAccessManager = QNetworkAccessManager(manager_parent)
        self.default_redirect_policy:  QNetworkRequest.RedirectPolicy = QNetworkRequest.ManualRedirectPolicy

    @property
    def cookies(self) -> dict[str, str]:
        """:return: Dictionary representation of the internal QNetworkCookieJar"""
        return {cookie.name().toStdString(): cookie.value().toStdString() for cookie in self.manager.cookieJar().allCookies()}

    @cookies.deleter
    def cookies(self) -> None:
        """Clear all cookies on delete."""
        self.clear_cookies()

    @property
    def headers(self) -> CaseInsensitiveDict[Any]:
        """:return: Dictionary containing the default session headers."""
        return self._headers

    @headers.setter
    def headers(self, value: Mapping) -> None:
        """Translate any mapping value to a CaseInsensitiveDict for use as headers.

        :param value: Mapping to copy into a CaseInsensitiveDict.
        :raises TypeError: If the value is not a Mapping.
        """
        if not isinstance(value, Mapping):
            raise TypeError(f'NetworkSession headers must be a Mapping, not {type(value)}')

        self._headers = CaseInsensitiveDict(value)

    @headers.deleter
    def headers(self) -> None:
        """Clear headers on delete."""
        self._headers.clear()

    @staticmethod
    def _check_method_kwargs(method: str, **kwargs) -> None:
        """Check that the given keyword arguments are valid for the given HTTP method.

        If some arguments are invalid, a warning is emitted.

        :param method: HTTP method to check.
        :param kwargs: Keyword arguments to check.
        """

        if method in ('GET', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE'):
            if any((kwargs.get('data'), kwargs.get('files'), kwargs.get('json'))):
                warn(UserWarning(f'{method} requests do not support data attached to the request body. This data is likely to be ignored.'))

    def _translate_header_value(self, header: str, value: Any) -> str | bytes | QDateTime | list[QNetworkCookie] | list[str] | QUrl:
        """Translate a header's value to it's appropriate type for use in QNetworkRequest.setHeader.

        Values are translated to their appropriate type based on the type defined in KNOWN_HEADERS next to the header enum value.

        The following types are supported:
            - str: Given value is translated into a str.
            - bytes: Translates string value into a utf8 encoded version.
            - QDateTime: Translates string and datetime values into a QDateTime.
            - QNetworkCookie: Translates string pairs into a QNetworkCookie list. The first value is the cookie name, the second is the cookie value.
            - QStringListModel: Iterates over value and translates all inner-values to strings. Returns a list of the translated strings.
            - QUrl: Calls the QUrl constructor on value and returns result.

        :param header: Header defined in KNOWN_HEADERS.
        :param value: Value to translate into an accepted type.
        :return: Transformed value.
        """
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

        :param domain: The domain of the cookie to remove.
        :param path: The path of the cookie to remove.
        :param name: The name of the cookie to remove.
        :return: True if any cookies were removed, False otherwise.
        :raises ValueError: If name is provided, must provide path. If path is provided, must provide domain. Raise otherwise.
        """

        def deletion_predicate(cookie: QNetworkCookie) -> bool:
            """Return whether the cookie should be deleted.

            :param cookie: The cookie to check.
            :return: True if the cookie should be removed, False otherwise.
            :raises ValueError: If name is provided, must provide path. If path is provided, must provide domain. Raise otherwise.
            """
            # 3 args -- Delete the specific cookie which matches all information.
            if name is not None:
                if domain is None or path is None:
                    raise ValueError('Must specify domain and path if specifying name')

                return cookie.name().toStdString() == name and cookie.domain() == domain and cookie.path() == path

            # 2 args -- Delete all cookies with the given domain and path.
            elif path is not None:
                if path is None:
                    raise ValueError('Must specify domain if specifying path')

                return cookie.domain() == domain and cookie.path() == path

            # 1 arg -- Delete all cookies in the given domain.
            elif domain is not None:
                return cookie.domain() == domain

            # 0 args -- Delete all cookies
            else:
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
        :raises: ValueError if name and value are not strings.
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
                proxies: dict[str, str] | list[tuple[str, str]] | None = None,
                # hooks: dict[str, Callable | Iterable[Callable]] | None = None,
                # stream: bool | None = None,
                verify: bool | str | None = None,
                cert: str | tuple[str, str] | None = None,
                json: dict[str, Any] | None = None,
                finished: _NetworkReplyConsumer | None = None) -> QNetworkReply:
        """Send an HTTP request to the given URL with the given data.

        :param method: HTTP method/verb to use for the request. Case-sensitive.
        :param url: URL to send the request to. Could be a string or QUrl. Case-sensitive.
        :param params: URL parameters to attach to the URL. If url is a QUrl, overrides the QUrl's query. Case-sensitive.
        :param data: Bytes to send in the request body. If a string-pair, will be encoded to bytes as a form-encoded request body.
        :param headers: Headers to use for the request. Non-string values should ONLY be used for KNOWN_HEADERS. Case-insensitive.
        :param cookies: Cookies to use for the request. Case-sensitive.
        :param allow_redirects: If False, do not follow any redirect requests.
        :param proxies: String-pairs mapping protocol to the URL of the proxy. Supported protocols are 'ftp', 'http', 'socks5'.
        :param verify: If False, ignore all SSL errors. If a string, interpret verify as a path to the CA bundle to verify certificates against.
        :param cert: If a string, interpret cert as a path to a certificate to use for SSL client authentication. Else, interpret cert as a (cert, key) pair.
        :param json: JSON data to send in the request body. Automatically encodes to bytes and updates Content-Type header. Do NOT use with data param.
        :param finished: Consumer to call when the request finishes, with request supplied as an argument.
        :return: QNetworkReply object, which is not guaranteed to be finished.
        :raises ValueError: If string pair tuples ( list[tuple[str, str]] ) don't contain exactly 2 items.
        """

        # Setup values for the request

        params = {} if params is None else params
        headers = {} if headers is None else headers
        cookies = {} if cookies is None else cookies

        # Translate dictionary-compatible tuple pair lists to dictionaries
        # Ex: [('name', 'value'), ('key': 'value')] -> {'name': 'value', 'key': 'value'}
        for tuple_list in ('params', 'data', 'headers', 'cookies', 'proxies'):
            if isinstance(vars()[tuple_list], list):
                vars()[tuple_list] = {key: value for key, value in vars()[tuple_list]}

        request_url:     QUrl = QUrl(url)                                              # Ensure url is of type QUrl
        request_params:  dict[str, str] = query_to_dict(request_url.query()) | params  # Override QUrl params with params argument
        request_headers: CaseInsensitiveDict = self.headers.copy() | headers           # Update session headers with headers argument
        request_cookies: dict[str, str] = self.cookies | cookies                       # Update session cookies with cookies argument

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
        """Create and send a request with the GET HTTP method.

        GET is the general method used to get a resource from a server. It is the most commonly used method, with GET requests being used
        by web browsers to download HTML pages, images, and other resources.

        :param url: URL to send the request to. Could be a string or QUrl. Case-sensitive.
        :keyword params: URL parameters to attach to the URL. If url is a QUrl, overrides the QUrl's query. Case-sensitive.
        :keyword data: Bytes to send in the request body. If a string-pair, will be encoded to bytes as a form-encoded request body.
        :keyword headers: Headers to use for the request. Non-string values should ONLY be used for KNOWN_HEADERS. Case-insensitive.
        :keyword cookies: Cookies to use for the request. Case-sensitive.
        :keyword allow_redirects: If False, do not follow any redirect requests.
        :keyword proxies: String-pairs mapping protocol to the URL of the proxy. Supported protocols are 'ftp', 'http', 'socks5'.
        :keyword verify: If False, ignore all SSL errors. If a string, interpret verify as a path to the CA bundle to verify certificates against.
        :keyword cert: If a string, interpret cert as a path to a certificate to use for SSL client authentication. Else, interpret cert as a (cert, key) pair.
        :keyword json: JSON data to send in the request body. Automatically encodes to bytes and updates Content-Type header. Do NOT use with data param.
        :keyword finished: Consumer to call when the request finishes, with request supplied as an argument.
        :return: QNetworkReply object, which is not guaranteed to be finished."""
        method: str = 'GET'
        self._check_method_kwargs(method, **kwargs)

        return self.request(method=method, url=url, **kwargs)

    def head(self, url: QUrl | str, **kwargs) -> QNetworkReply:
        """Create and send a request with the HEAD HTTP method.

        HEAD requests are used to retrieve information about a resource without actually fetching the resource itself.
        This is useful for checking if a resource exists, or for getting the size of a resource before downloading it.

        :param url: URL to send the request to. Could be a string or QUrl. Case-sensitive.
        :keyword params: URL parameters to attach to the URL. If url is a QUrl, overrides the QUrl's query. Case-sensitive.
        :keyword data: Bytes to send in the request body. If a string-pair, will be encoded to bytes as a form-encoded request body.
        :keyword headers: Headers to use for the request. Non-string values should ONLY be used for KNOWN_HEADERS. Case-insensitive.
        :keyword cookies: Cookies to use for the request. Case-sensitive.
        :keyword allow_redirects: If False, do not follow any redirect requests.
        :keyword proxies: String-pairs mapping protocol to the URL of the proxy. Supported protocols are 'ftp', 'http', 'socks5'.
        :keyword verify: If False, ignore all SSL errors. If a string, interpret verify as a path to the CA bundle to verify certificates against.
        :keyword cert: If a string, interpret cert as a path to a certificate to use for SSL client authentication. Else, interpret cert as a (cert, key) pair.
        :keyword json: JSON data to send in the request body. Automatically encodes to bytes and updates Content-Type header. Do NOT use with data param.
        :keyword finished: Consumer to call when the request finishes, with request supplied as an argument.
        :return: QNetworkReply object, which is not guaranteed to be finished."""
        method: str = 'HEAD'
        self._check_method_kwargs(method, **kwargs)

        return self.request(method=method, url=url, **kwargs)

    def post(self, url: QUrl | str, **kwargs) -> QNetworkReply:
        """Create and send a request with the POST HTTP method.

        POST is the general method used to send data to a server. It does not require a resource to previously exist, nor does it require one to not exist.
        This makes it very common for servers to accept POST requests for a multitude of things.

        :param url: URL to send the request to. Could be a string or QUrl. Case-sensitive.
        :keyword params: URL parameters to attach to the URL. If url is a QUrl, overrides the QUrl's query. Case-sensitive.
        :keyword data: Bytes to send in the request body. If a string-pair, will be encoded to bytes as a form-encoded request body.
        :keyword headers: Headers to use for the request. Non-string values should ONLY be used for KNOWN_HEADERS. Case-insensitive.
        :keyword cookies: Cookies to use for the request. Case-sensitive.
        :keyword allow_redirects: If False, do not follow any redirect requests.
        :keyword proxies: String-pairs mapping protocol to the URL of the proxy. Supported protocols are 'ftp', 'http', 'socks5'.
        :keyword verify: If False, ignore all SSL errors. If a string, interpret verify as a path to the CA bundle to verify certificates against.
        :keyword cert: If a string, interpret cert as a path to a certificate to use for SSL client authentication. Else, interpret cert as a (cert, key) pair.
        :keyword json: JSON data to send in the request body. Automatically encodes to bytes and updates Content-Type header. Do NOT use with data param.
        :keyword finished: Consumer to call when the request finishes, with request supplied as an argument.
        :return: QNetworkReply object, which is not guaranteed to be finished."""
        method: str = 'POST'
        self._check_method_kwargs(method, **kwargs)

        return self.request(method=method, url=url, **kwargs)

    def put(self, url: QUrl | str, **kwargs) -> QNetworkReply:
        """Create and send a request with the PUT HTTP method.

        PUT is a method for completely updating a resource on a server. The data sent by PUT should be the full content of the resource.

        :param url: URL to send the request to. Could be a string or QUrl. Case-sensitive.
        :keyword params: URL parameters to attach to the URL. If url is a QUrl, overrides the QUrl's query. Case-sensitive.
        :keyword data: Bytes to send in the request body. If a string-pair, will be encoded to bytes as a form-encoded request body.
        :keyword headers: Headers to use for the request. Non-string values should ONLY be used for KNOWN_HEADERS. Case-insensitive.
        :keyword cookies: Cookies to use for the request. Case-sensitive.
        :keyword allow_redirects: If False, do not follow any redirect requests.
        :keyword proxies: String-pairs mapping protocol to the URL of the proxy. Supported protocols are 'ftp', 'http', 'socks5'.
        :keyword verify: If False, ignore all SSL errors. If a string, interpret verify as a path to the CA bundle to verify certificates against.
        :keyword cert: If a string, interpret cert as a path to a certificate to use for SSL client authentication. Else, interpret cert as a (cert, key) pair.
        :keyword json: JSON data to send in the request body. Automatically encodes to bytes and updates Content-Type header. Do NOT use with data param.
        :keyword finished: Consumer to call when the request finishes, with request supplied as an argument.
        :return: QNetworkReply object, which is not guaranteed to be finished."""
        method: str = 'PUT'
        self._check_method_kwargs(method, **kwargs)

        return self.request(method=method, url=url, **kwargs)

    def delete(self, url: QUrl | str, **kwargs) -> QNetworkReply:
        """Create and send a request with the DELETE HTTP method.

        DELETE is used to delete a specified resource.

        :param url: URL to send the request to. Could be a string or QUrl. Case-sensitive.
        :keyword params: URL parameters to attach to the URL. If url is a QUrl, overrides the QUrl's query. Case-sensitive.
        :keyword data: Bytes to send in the request body. If a string-pair, will be encoded to bytes as a form-encoded request body.
        :keyword headers: Headers to use for the request. Non-string values should ONLY be used for KNOWN_HEADERS. Case-insensitive.
        :keyword cookies: Cookies to use for the request. Case-sensitive.
        :keyword allow_redirects: If False, do not follow any redirect requests.
        :keyword proxies: String-pairs mapping protocol to the URL of the proxy. Supported protocols are 'ftp', 'http', 'socks5'.
        :keyword verify: If False, ignore all SSL errors. If a string, interpret verify as a path to the CA bundle to verify certificates against.
        :keyword cert: If a string, interpret cert as a path to a certificate to use for SSL client authentication. Else, interpret cert as a (cert, key) pair.
        :keyword json: JSON data to send in the request body. Automatically encodes to bytes and updates Content-Type header. Do NOT use with data param.
        :keyword finished: Consumer to call when the request finishes, with request supplied as an argument.
        :return: QNetworkReply object, which is not guaranteed to be finished."""
        method: str = 'DELETE'
        self._check_method_kwargs(method, **kwargs)

        return self.request(method=method, url=url, **kwargs)

    def patch(self, url: QUrl | str, **kwargs) -> QNetworkReply:
        """Create and send a request with the PATCH HTTP method.

        PATCH is used to send a partial update of an existing resource.

        :param url: URL to send the request to. Could be a string or QUrl. Case-sensitive.
        :keyword params: URL parameters to attach to the URL. If url is a QUrl, overrides the QUrl's query. Case-sensitive.
        :keyword data: Bytes to send in the request body. If a string-pair, will be encoded to bytes as a form-encoded request body.
        :keyword headers: Headers to use for the request. Non-string values should ONLY be used for KNOWN_HEADERS. Case-insensitive.
        :keyword cookies: Cookies to use for the request. Case-sensitive.
        :keyword allow_redirects: If False, do not follow any redirect requests.
        :keyword proxies: String-pairs mapping protocol to the URL of the proxy. Supported protocols are 'ftp', 'http', 'socks5'.
        :keyword verify: If False, ignore all SSL errors. If a string, interpret verify as a path to the CA bundle to verify certificates against.
        :keyword cert: If a string, interpret cert as a path to a certificate to use for SSL client authentication. Else, interpret cert as a (cert, key) pair.
        :keyword json: JSON data to send in the request body. Automatically encodes to bytes and updates Content-Type header. Do NOT use with data param.
        :keyword finished: Consumer to call when the request finishes, with request supplied as an argument.
        :return: QNetworkReply object, which is not guaranteed to be finished.
        """
        method: str = 'PATCH'
        self._check_method_kwargs(method, **kwargs)

        return self.request(method=method, url=url, **kwargs)
