###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Defines the HaloInfiniteGetter HTTP Client."""
from __future__ import annotations

__all__ = (
    'Client',
    'TOKEN_PATH',
    'WEB_DUMP_PATH',
    'WPAUTH_PATH',
)

import json
import os
from pathlib import Path
from typing import Any
from typing import Final

from PySide6.QtCore import *
from PySide6.QtNetwork import *

from ..constants import *
from ..models import CaseInsensitiveDict
from ..utils.common import dump_data
from ..utils.network import decode_url
from ..utils.network import guess_json_utf
from ..utils.network import is_error_status
from ..utils.network import wait_for_reply
from ..utils.system import hide_windows_file
from .manager import NetworkSession

WEB_DUMP_PATH: Final[Path] = HI_CACHE_PATH / 'cached_requests'
TOKEN_PATH: Final[Path] = HI_CONFIG_PATH / '.token'
WPAUTH_PATH: Final[Path] = HI_CONFIG_PATH / '.wpauth'


class Client(QObject):
    """Asynchronous HTTP REST Client that interfaces with Halo Waypoint to get data."""
    receivedData = Signal(str, bytes, name='receivedData')
    receivedError = Signal(str, int, name='receivedError')
    receivedJson = Signal(str, dict, name='receivedJson')

    def __init__(self, parent: QObject, **kwargs) -> None:
        """Initializes Halo Waypoint Client

        token is first taken from token kwarg, then HI_SPARTAN_AUTH environment variable, then from user's .token file.
        wpauth is first taken from wpauth kwarg, then HI_WAYPOINT_AUTH environment variable, then from the user's .wpauth file.

        :keyword token: Token to authenticate self to 343 API.
        :keyword wpauth: Halo Waypoint authentication key, allows for creation of 343 auth tokens.
        """
        super().__init__(parent)
        self.SVC_HOST: str = 'svc.halowaypoint.com'
        self.WEB_HOST: str = 'www.halowaypoint.com'
        self.parent_path: str = '/hi/'
        self.sub_host: str = 'gamecms-hacs-origin'  # Must be defined before session headers
        self.searched_paths: set[str] = set()

        self._token: str | None = kwargs.pop('token', os.getenv('HI_SPARTAN_AUTH', None))
        if self._token is None and TOKEN_PATH.is_file():
            self._token = TOKEN_PATH.read_text(encoding='utf8').strip()

        self._wpauth: str | None = kwargs.pop('wpauth', os.getenv('HI_WAYPOINT_AUTH', None))
        if self._wpauth is None and WPAUTH_PATH.is_file():
            self._wpauth = WPAUTH_PATH.read_text(encoding='utf8').strip()

        self.api_session: NetworkSession = NetworkSession(self)
        self.api_session.headers = CaseInsensitiveDict({
            'Accept': ', '.join(('application/json', 'text/plain', '*/*')),
            # 'Accept-Encoding': ', '.join(('gzip', 'deflate', 'br')),
            'Accept-Language': 'en-US',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'DNT': '1',
            'Host': self.host,
            'Origin': 'https://www.halowaypoint.com',
            'Pragma': 'no-cache',
            'Referer': 'https://www.halowaypoint.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Sec-GPC': '1',
            'TE': 'trailers',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0',
        })
        self.web_session: NetworkSession = NetworkSession(self)
        self.web_session.headers = self.api_session.headers | {
            'Accept': ','.join(('text/html', 'application/xhtml+xml', 'application/xml;q=0.9', 'image/avif', 'image/webp', '*/*;q=0.8')),
            'Host': self.WEB_HOST,
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }

        if self.wpauth:
            self.set_cookie('wpauth', self.wpauth)
            if not self.token:
                self.refresh_auth()

        if self.token:
            self.api_session.headers['x-343-authorization-spartan'] = self.token
            self.set_cookie('343-spartan-token', self.token)

    def get(self, path: str, update_auth_on_401: bool = True, **kwargs) -> QNetworkReply:
        """Get a :py:class:`Response` from HaloWaypoint.

        :param path: path to append to the API root
        :param update_auth_on_401: run self._refresh_auth if response status code is 401 Unauthorized
        :param kwargs: Key word arguments to pass to the requests GET Request.
        """
        reply: QNetworkReply = self.api_session.get(self.api_root + path.strip(), **kwargs)
        wait_for_reply(reply)

        # None is returned if the request was aborted
        status_code: int | None = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code and is_error_status(status_code):
            # Handle errors
            if status_code == 401 and update_auth_on_401 and self.wpauth is not None:
                self.refresh_auth()
                reply = self.get(path, False, **kwargs)

        return reply

    def get_hi_data(self, path: str, dump_path: Path = WEB_DUMP_PATH) -> dict[str, Any] | bytes | int:
        """Returns data from a path. Return type depends on the resource.

        :return: dict for JSON objects, bytes for media, int for error codes.
        :raises ValueError: If the response is not JSON or a supported image type.
        """
        os_path: Path = self.to_os_path(path, parent=dump_path)
        data: dict[str, Any] | bytes

        if not os_path.is_file():
            reply: QNetworkReply = self.get(path)
            encoded_data: bytes = reply.readAll().data()
            status_code: int | None = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            content_type: str = reply.header(QNetworkRequest.ContentTypeHeader) or ''

            if status_code and is_error_status(status_code):
                self.receivedError.emit(path, status_code)
                return status_code

            if 'json' in content_type:
                data = json.loads(encoded_data.decode(guess_json_utf(encoded_data)))
                self.receivedJson.emit(path, data)
            elif content_type in SUPPORTED_IMAGE_MIME_TYPES:
                data = encoded_data
                self.receivedData.emit(path, data)
            else:
                raise ValueError(f'Unsupported content type received: {content_type}')

            print(f"DOWNLOADED {path} >>> {content_type}")
            dump_data(os_path, data)

            reply.deleteLater()

        else:
            print(path)
            data = os_path.read_bytes()
            if os_path.suffix == '.json':
                data = json.loads(data.decode(guess_json_utf(data)))
                self.receivedJson.emit(path, data)
            else:
                self.receivedData.emit(path, data)

        return data

    def hidden_key(self) -> str:
        """:return: The first and last 3 characters of the waypoint token, seperated by periods."""
        key = self.wpauth
        if key is not None and len(key) > 6:
            return f'{key[:3]}{"." * 50}{key[-3:]}'
        return 'None'

    def to_os_path(self, path: str, parent: Path = WEB_DUMP_PATH) -> Path:
        """Translate a given GET path to the equivalent cache location."""
        return parent / self.sub_host.replace('-', '_') / self.parent_path.strip('/') / path.replace('/file/', '/').lower()

    def to_get_path(self, path: str) -> str:
        """Translate a given cache location to the equivalent GET path."""
        resource = path.split(self.parent_path, maxsplit=1)[1]
        pre, post = resource.split("/", maxsplit=1)
        return f'{pre}/file/{post}'

    def refresh_auth(self) -> None:
        """Refreshes authentication to Halo Waypoint servers.

        wpauth MUST have a value for this to work. A lone 343 spartan token is not enough to generate a new one.
        """
        reply: QNetworkReply = self.web_session.get('https://www.halowaypoint.com/')
        wait_for_reply(reply)

        wpauth: str = decode_url(self.web_session.cookies.get('wpauth') or '')
        token: str = decode_url(self.web_session.cookies.get('343-spartan-token') or '')

        if wpauth and self.wpauth != wpauth:
            self.wpauth = wpauth
        if token:
            self.token = token

    def delete_cookie(self, name: str) -> None:
        """Delete given cookie if cookie exists."""
        self.web_session.clear_cookies(self.WEB_HOST, '/', name)

    def set_cookie(self, name: str, value: str) -> None:
        """Set cookie value in Cookie jar. Defaults cookie domain as the WEB_HOST."""
        self.web_session.set_cookie(name, value, self.WEB_HOST)

    @property
    def token(self) -> str | None:
        """343 auth token to authenticate self to API endpoints."""
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        value = decode_url(value)
        key_start_index = value.find('v4=')
        if key_start_index == -1:
            raise ValueError('token value is missing version identifier ("v4=") to signify start.')

        self._token = value[key_start_index:].rstrip()
        self.set_cookie('343-spartan-token', self._token)
        self.api_session.headers['x-343-authorization-spartan'] = self._token

        hide_windows_file(TOKEN_PATH, unhide=True)
        TOKEN_PATH.write_text(self._token, encoding='utf8')
        hide_windows_file(TOKEN_PATH)

    @token.deleter
    def token(self) -> None:
        self._token = None
        self.delete_cookie('343-spartan-token')
        if 'x-343-authorization-spartan' in self.api_session.headers:
            self.api_session.headers.pop('x-343-authorization-spartan')
        if TOKEN_PATH.is_file():
            TOKEN_PATH.unlink()

    @property
    def wpauth(self) -> str | None:
        """Halo Waypoint auth key to create 343 spartan tokens."""
        return self._wpauth

    @wpauth.setter
    def wpauth(self, value: str) -> None:
        value = decode_url(value)
        self._wpauth = value.split(':')[-1].strip()
        self.set_cookie('wpauth', self._wpauth)

        hide_windows_file(WPAUTH_PATH, unhide=True)
        WPAUTH_PATH.write_text(self._wpauth, encoding='utf8')
        hide_windows_file(WPAUTH_PATH)

    @wpauth.deleter
    def wpauth(self) -> None:
        self._wpauth = None
        self.delete_cookie('wpauth')
        if WPAUTH_PATH.is_file():
            WPAUTH_PATH.unlink()

    @property
    def api_root(self) -> str:
        """Root of sent API requests."""
        return f'https://{self.host}{self.parent_path}'

    @property
    def host(self) -> str:
        """Host to send to."""
        return f'{self.sub_host}.{self.SVC_HOST}'

    @host.setter
    def host(self, value: str) -> None:
        self.sub_host = value
