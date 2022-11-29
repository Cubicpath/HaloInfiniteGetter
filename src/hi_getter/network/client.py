###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Defines the HaloInfiniteGetter HTTP Client."""
from __future__ import annotations

__all__ = (
    'Client',
)

import json
import os
from pathlib import Path
from typing import Any
from typing import Final

from PySide6.QtCore import *

from ..constants import *
from ..models import CaseInsensitiveDict
from ..utils import dump_data
from ..utils import decode_url
from ..utils import guess_json_utf
from ..utils import hide_windows_file
from .manager import NetworkSession
from .manager import Response

_ENDPOINT_PATH: Final[Path] = HI_RESOURCE_PATH / 'wp_endpoint_hosts.json'


class Client(QObject):
    """Asynchronous HTTP REST Client that interfaces with Halo Waypoint to get data."""

    receivedData = Signal(str, bytes, name='receivedData')
    receivedError = Signal(str, int, name='receivedError')
    receivedJson = Signal(str, dict, name='receivedJson')

    def __init__(self, parent: QObject, **kwargs) -> None:
        """Initialize Halo Waypoint Client.

        token is first taken from token kwarg, then HI_SPARTAN_AUTH environment variable, then from user's .token file.
        wpauth is first taken from wpauth kwarg, then HI_WAYPOINT_AUTH environment variable, then from the user's .wpauth file.

        :keyword token: Token to authenticate self to 343 API.
        :keyword wpauth: Halo Waypoint authentication key, allows for creation of 343 auth tokens.
        """
        super().__init__(parent)
        self.endpoints: dict[str, Any] = json.loads(_ENDPOINT_PATH.read_text(encoding='utf8'))

        self.parent_path: str = '/hi/'
        self.sub_host: str = self.endpoints['endpoints']['gameCmsService']['subdomain']  # Must be defined before session headers
        self.searched_paths: set[str] = set()

        self._token: str | None = kwargs.pop('token', os.getenv('HI_SPARTAN_AUTH', None))
        if self._token is None and HI_TOKEN_PATH.is_file():
            self._token = HI_TOKEN_PATH.read_text(encoding='utf8').strip()

        self._wpauth: str | None = kwargs.pop('wpauth', os.getenv('HI_WAYPOINT_AUTH', None))
        if self._wpauth is None and HI_WPAUTH_PATH.is_file():
            self._wpauth = HI_WPAUTH_PATH.read_text(encoding='utf8').strip()

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
            'Host': self.endpoints['webHost'],
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

    def _get(self, path: str, update_auth_on_401: bool = True, **kwargs) -> Response:
        """Get a :py:class:`Response` from HaloWaypoint.

        :param path: path to append to the API root
        :param update_auth_on_401: run self._refresh_auth if response status code is 401 Unauthorized
        :param kwargs: Key word arguments to pass to the requests GET Request.
        """
        response: Response = self.api_session.get(self.api_root + path.strip(), wait_until_finished=True, **kwargs)

        if response.code and not response.ok:
            # Handle errors
            if response.code == 401 and update_auth_on_401 and self.wpauth is not None:
                self.refresh_auth()
                response = self._get(path, False, **kwargs)

        return response

    def get_hi_data(self, path: str, dump_path: Path = HI_WEB_DUMP_PATH) -> dict[str, Any] | bytes | int:
        """Return data from a path. Return type depends on the resource.

        :return: dict for JSON objects, bytes for media, int for error codes.
        :raises ValueError: If the response is not JSON or a supported image type.
        """
        os_path: Path = self.to_os_path(path, parent=dump_path)
        data: dict[str, Any] | bytes

        if not os_path.is_file():
            response: Response = self._get(path)
            content_type: str | None = response.headers.get('Content-Type')

            if response.code and not response.ok:
                print(f'ERROR [{response.code}] for {path} ')
                self.receivedError.emit(path, response.code)
                return response.code

            if not content_type:
                raise ValueError('Successful status code but no Content-Type header.')

            if 'json' in content_type:
                data = response.json
                self.receivedJson.emit(path, data)
            elif content_type in SUPPORTED_IMAGE_MIME_TYPES:
                data = response.data
                self.receivedData.emit(path, data)
            else:
                raise ValueError(f'Unsupported content type received: {content_type}')

            print(f'DOWNLOADED {path} >>> {content_type}')
            dump_data(os_path, data)

        else:
            print(path)
            data = os_path.read_bytes()
            if os_path.suffix == '.json':
                data = json.loads(data.decode(encoding=guess_json_utf(data) or 'utf8'))
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

    def to_os_path(self, path: str, parent: Path = HI_WEB_DUMP_PATH) -> Path:
        """Translate a given GET path to the equivalent cache location."""
        return parent / self.sub_host.replace('-', '_') / self.parent_path.strip('/') / path.replace('/file/', '/').lower()

    def to_get_path(self, path: str) -> str:
        """Translate a given cache location to the equivalent GET path."""
        resource = path.split(self.parent_path, maxsplit=1)[1]
        pre, post = resource.split('/', maxsplit=1)
        return f'{pre}/file/{post}'

    def refresh_auth(self) -> None:
        """Refresh authentication to Halo Waypoint servers.

        wpauth MUST have a value for this to work. A lone 343 spartan token is not enough to generate a new one.
        """
        self.web_session.get('https://www.halowaypoint.com/', wait_until_finished=True)

        wpauth: str = decode_url(self.web_session.cookies.get('wpauth') or '')
        token: str = decode_url(self.web_session.cookies.get('343-spartan-token') or '')

        if wpauth and self.wpauth != wpauth:
            self.wpauth = wpauth
        if token:
            self.token = token

    def delete_cookie(self, name: str) -> None:
        """Delete given cookie if cookie exists."""
        self.web_session.clear_cookies(self.endpoints['webHost'], '/', name)

    def set_cookie(self, name: str, value: str) -> None:
        """Set cookie value in Cookie jar. Defaults cookie domain as the WEB_HOST."""
        self.web_session.set_cookie(name, value, self.endpoints['webHost'])

    @property
    def token(self) -> str | None:
        """343 auth token to authenticate self to API endpoints.

        :raises ValueError: If the value being set doesn't contain the version identifier ("v4=").
        """
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        value = decode_url(value)
        if (key_start_index := value.find('v4=')) == -1:
            raise ValueError('token value is missing version identifier ("v4=") to signify start.')

        self._token = value[key_start_index:].rstrip()
        self.set_cookie('343-spartan-token', self._token)
        self.api_session.headers['x-343-authorization-spartan'] = self._token

        hide_windows_file(HI_TOKEN_PATH, unhide=True)
        HI_TOKEN_PATH.write_text(self._token, encoding='utf8')
        hide_windows_file(HI_TOKEN_PATH)

    @token.deleter
    def token(self) -> None:
        self._token = None
        self.delete_cookie('343-spartan-token')
        if 'x-343-authorization-spartan' in self.api_session.headers:
            self.api_session.headers.pop('x-343-authorization-spartan')
        if HI_TOKEN_PATH.is_file():
            HI_TOKEN_PATH.unlink()

    @property
    def wpauth(self) -> str | None:
        """Halo Waypoint auth key to create 343 spartan tokens."""
        return self._wpauth

    @wpauth.setter
    def wpauth(self, value: str) -> None:
        value = decode_url(value)
        self._wpauth = value.split(':')[-1].strip()
        self.set_cookie('wpauth', self._wpauth)

        hide_windows_file(HI_WPAUTH_PATH, unhide=True)
        HI_WPAUTH_PATH.write_text(self._wpauth, encoding='utf8')
        hide_windows_file(HI_WPAUTH_PATH)

    @wpauth.deleter
    def wpauth(self) -> None:
        self._wpauth = None
        self.delete_cookie('wpauth')
        if HI_WPAUTH_PATH.is_file():
            HI_WPAUTH_PATH.unlink()

    @property
    def api_root(self) -> str:
        """Root of sent API requests."""
        return f'https://{self.host}{self.parent_path}'

    @property
    def host(self) -> str:
        """Host to send to."""
        return f'{self.sub_host}.{self.endpoints["svcHost"]}'

    @host.setter
    def host(self, value: str) -> None:
        self.sub_host = value
