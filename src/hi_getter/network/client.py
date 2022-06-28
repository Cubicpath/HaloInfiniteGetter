###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Defines the HaloInfiniteGetter HTTP Client."""

__all__ = (
    'Client',
    'TOKEN_PATH',
    'WPAUTH_PATH',
)

import json
import os
import random
import time
from pathlib import Path
from typing import Any
from typing import Final

from PySide6.QtCore import *
from PySide6.QtNetwork import *
from PySide6.QtWidgets import *

from ..constants import *
from ..utils import dump_data
from ..utils import hide_windows_file
from ..utils import unique_values
from .manager import NetworkSession
from .structures import CaseInsensitiveDict
from .utils import decode_url
from .utils import guess_json_utf
from .utils import is_error_status

TOKEN_PATH:  Final[Path] = HI_CONFIG_PATH / '.token'
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
        self.SVC_HOST:       str = 'svc.halowaypoint.com'
        self.WEB_HOST:       str = 'www.halowaypoint.com'
        self.parent_path:    str = '/hi/'
        self.sub_host:       str = 'gamecms-hacs-origin'  # Must be defined before session headers
        self.searched_paths: dict = {}

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
        self.web_session.headers = self.api_session.headers.copy() | {
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
        while not reply.isFinished():
            QApplication.processEvents()

        status_code: int = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if is_error_status(status_code):
            if status_code == 401 and update_auth_on_401 and self.wpauth is not None:
                self.refresh_auth()
                reply = self.get(path, False, **kwargs)
        return reply

    def get_hi_data(self, path: str, dump_path: Path = HI_CACHE_PATH, micro_sleep: bool = True) -> dict[str, Any] | bytes | int:
        """Returns data from a path. Return type depends on the resource.

        :return: dict for JSON objects, bytes for media, int for error codes.
        """
        os_path: Path = self.os_path(path, parent=dump_path)
        data: dict[str, Any] | bytes

        if not os_path.is_file():
            reply:        QNetworkReply = self.get(path)
            encoded_data: bytes = reply.readAll().data()
            status_code:  int = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            content_type: str = reply.header(QNetworkRequest.ContentTypeHeader) or ''

            if is_error_status(status_code):
                self.receivedError.emit(path, status_code)
                return status_code

            if 'json' in content_type:
                data = json.loads(encoded_data.decode(guess_json_utf(encoded_data)))
                self.receivedJson.emit(path, data)
            else:
                data = encoded_data
                self.receivedData.emit(path, data)

            print(f"DOWNLOADED {path} >>> {content_type}")
            dump_data(os_path, data)

            reply.deleteLater()
            if micro_sleep:
                time.sleep(random.randint(100, 200) / 750)

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

    def os_path(self, path: str, parent: Path = HI_CACHE_PATH) -> Path:
        """Translate a given GET path to the equivalent cache location."""
        return parent / self.sub_host.replace('-', '_') / self.parent_path.strip('/') / path.replace('/file/', '/').lower()

    def recursive_search(self, search_path: str) -> None:
        """Recursively get Halo Waypoint files linked to the search_path through Mapping keys."""
        if self.searched_paths.get(search_path, 0) >= 2:
            return

        data: dict[str, Any] | bytes | int = self.get_hi_data(search_path)
        if isinstance(data, (bytes, int)):
            return

        for value in unique_values(data):
            if isinstance(value, str):
                if '/' not in value:
                    continue

                end = value.split('.')[-1].lower()
                if end in ('json',):
                    path = 'progression/file/' + value
                    self.searched_paths.update({path: self.searched_paths.get(path, 0) + 1})
                    self.recursive_search(path)
                elif end in ('png', 'jpg', 'jpeg', 'webp', 'gif'):
                    self.get_hi_data('images/file/' + value)

    def refresh_auth(self) -> None:
        """Refreshes authentication to Halo Waypoint servers.

        wpauth MUST have a value for this to work. A lone 343 spartan token is not enough to generate a new one.
        """
        reply: QNetworkReply = self.web_session.get('https://www.halowaypoint.com/')

        # TODO: After moving client to separate thread, remove this and QtWidgets import.
        while not reply.isFinished():
            QApplication.processEvents()

        wpauth: str = decode_url(self.web_session.cookies.get('wpauth') or '')
        token:  str = decode_url(self.web_session.cookies.get('343-spartan-token') or '')

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
