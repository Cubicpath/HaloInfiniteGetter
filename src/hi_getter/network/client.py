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
from collections.abc import Callable
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
from ..utils import unique_values
from .manager import NetworkSession
from .manager import Response

_ENDPOINT_PATH: Final[Path] = HI_RESOURCE_PATH / 'wp_endpoint_hosts.json'


class Client(QObject):
    """Asynchronous HTTP REST Client that interfaces with Halo Waypoint to get data."""

    finishedSearch = Signal()
    startedSearch = Signal()

    receivedData = Signal(str, bytes)
    receivedError = Signal(str, int)
    receivedJson = Signal(str, dict)

    def __init__(self, parent: QObject, **kwargs) -> None:
        """Initialize Halo Waypoint Client.

        Order of precedence for token and wpauth values::

            1. token/wpauth kwarg value
            2. HI_SPARTAN_AUTH/HI_WAYPOINT_AUTH environment variables
            3. user's .token/.wpauth config file (Created by application)

        :keyword token: Token to authenticate self to 343 API.
        :keyword wpauth: Halo Waypoint authentication key, allows for creation of 343 auth tokens.
        """
        super().__init__(parent)
        self.endpoints: dict[str, Any] = json.loads(_ENDPOINT_PATH.read_text(encoding='utf8'))
        self._recursive_calls_in_progress: int = 0

        self.parent_path: str = '/hi/'
        self.sub_host: str = self.endpoints['endpoints']['gameCmsService']['subdomain']
        self.searched_paths: set[str] = set()
        self.finishedSearch.connect(self.searched_paths.clear)

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
            'Accept': ','.join(('text/html', 'application/xhtml+xml', 'application/xml;q=0.9',
                                'image/avif', 'image/webp', '*/*;q=0.8')),
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

    def _get(self,
             path: str,
             update_auth_on_401: bool = True,
             finished: Callable[[Response], None] | None = None,
             **kwargs
             ) -> None:
        """Get a :py:class:`Response` from HaloWaypoint.

        :param path: path to append to the API root.
        :param update_auth_on_401: run self._refresh_auth if response status code is 401 Unauthorized.
        :param finished: Callback to send finished request to.
        """
        def handle_reply(response: Response):
            if not response.code or response.headers.get('Content-Type') is not None and not response.data:
                # If response finished but was malformed, wait 500ms and retry.
                print('RETRYING', response.url)
                QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 500)
                self._get(path, update_auth_on_401, finished, **kwargs)

            elif not response.ok:
                # Handle errors
                if response.code == 401 and update_auth_on_401 and self.wpauth is not None:
                    self.refresh_auth()
                    self._get(path, False, finished, **kwargs)

            elif finished is not None:
                # Send OK response to the given consumer
                finished(response)

        self.api_session.get(self.api_root + path.strip(), finished=handle_reply, **kwargs)

    def get_hi_data(self,
                    path: str,
                    consumer: Callable[[str, dict[str, Any] | bytes | int], None] | None = None
                    ) -> None:
        """Get a resource hosted on the HaloWaypoint API.

        Resulting resource is returned via a positional argument in a `received-` signal or the given consumer.

        :param path: Path to get data from.
        :param consumer: Consumer to send received data to.
        :raises ValueError: If the response is not JSON or a supported image type.
        """
        path = self.normalize_search_path(path)
        os_path: Path = self.to_os_path(path, parent=HI_WEB_DUMP_PATH)

        if not os_path.is_file():
            def handle_reply(response: Response):
                if response.code and not response.ok:
                    print(f'ERROR [{response.code}] for {path} ')
                    self.receivedError.emit(path, response.code)
                    if consumer is not None:
                        consumer(path, response.code)
                    return

                content_type: str | None = response.headers.get('Content-Type')
                response_data: dict[str, Any] | bytes

                if not content_type:
                    raise ValueError('Successful status code but no Content-Type header.')

                if 'json' in content_type:
                    response_data = response.json
                    self.receivedJson.emit(path, response_data)
                elif content_type in SUPPORTED_IMAGE_MIME_TYPES:
                    response_data = response.data
                    self.receivedData.emit(path, response_data)
                else:
                    raise ValueError(f'Unsupported content type received: {content_type}')

                print(f'DOWNLOADED {path} >>> {content_type}')
                dump_data(os_path, response_data)
                if consumer is not None:
                    consumer(path, response_data)

            self._get(path, finished=handle_reply)

        else:
            print(path)
            data: dict[str, Any] | bytes = os_path.read_bytes()
            if os_path.suffix.lstrip('.') in SUPPORTED_IMAGE_EXTENSIONS:
                self.receivedData.emit(path, data)
            else:
                # Assume json if not an image
                data = json.loads(data.decode(encoding=guess_json_utf(data) or 'utf8'))
                self.receivedJson.emit(path, data)

            if consumer is not None:
                consumer(path, data)

    def recursive_search(self, path: str) -> None:
        """Get a file and recursively look through its contents for paths.

        :param path: Path to search.
        """
        self._recursive_calls_in_progress += 1
        if self._recursive_calls_in_progress == 1:
            self.startedSearch.emit()

        path = self.normalize_search_path(path)

        # This set is shared between all recursive calls, so no duplicate searches should occur
        self.searched_paths.add(path)
        self.get_hi_data(path, consumer=self.handle_recursive_data)

        self._recursive_calls_in_progress -= 1
        if not self._recursive_calls_in_progress:
            self.finishedSearch.emit()

    def handle_recursive_data(self, _, data: dict[str, Any] | bytes | int) -> None:
        """Recursively look through JSON data for resource paths.

        :param data: Data received from path. If not JSON, return early.
        """
        if isinstance(data, (bytes, int)):
            return

        # Iterate over all values in the JSON data
        # This process ignores already-searched values
        for value in unique_values(data):
            if isinstance(value, str) and (match := HI_PATH_PATTERN.match(value)):
                new_path: str = self.normalize_search_path(match[0])

                # If it's an image, download it then ignore the result
                if match['file_name'].split('.')[-1].lower() in SUPPORTED_IMAGE_EXTENSIONS:
                    if new_path.lower() in self.searched_paths:
                        continue

                    self.searched_paths.add(new_path.lower())
                    self.get_hi_data(new_path)

                # Otherwise, start the process over again
                else:
                    if new_path.lower() in self.searched_paths:
                        continue

                    self.recursive_search(new_path)

    def hidden_key(self) -> str:
        """:return: The first and last 3 characters of the waypoint token, seperated by periods."""
        key = self.wpauth
        if key is not None and len(key) > 6:
            return f'{key[:3]}{"." * 50}{key[-3:]}'
        return 'None'

    def normalize_search_path(self, path: str) -> str:
        """Normalize and expand search paths.

        If path starts with the ``api_root``, assume the contents are already expanded.
        If not explicitly an images file but has an image extension, assume it's from images/file/ directory.
        If not explicitly a progression file but has a json extension, assume it's from progression/file/ directory.

        :param path: Search path to normalize.
        :return: Normalized version of ``path``.
        """
        # Ensure lowercase
        path = path.lower().lstrip('/')
        parent_path = self.parent_path.lower().lstrip('/')
        file_ext = path.split('.')[-1]

        # Expand paths
        if path.startswith(parent_path):
            path = path.removeprefix(parent_path)
        elif not path.startswith('images/file/') and (file_ext in SUPPORTED_IMAGE_EXTENSIONS):
            path = f'images/file/{path}'
        elif not path.startswith('progression/file/') and (file_ext == 'json'):
            path = f'progression/file/{path}'

        return path

    def to_os_path(self, path: str, parent: Path = HI_WEB_DUMP_PATH) -> Path:
        """Translate a given GET path to the equivalent cache location."""
        return (parent /
                self.sub_host.replace('-', '_') /
                self.parent_path.strip('/') /
                path.replace('/file/', '/').lower())

    def to_get_path(self, path: str) -> str:
        """Translate a given cache location to the equivalent GET path."""
        resource = path.split(self.parent_path, maxsplit=1)[1]
        pre, post = resource.split('/', maxsplit=1)
        return f'{pre}/file/{post}'

    def refresh_auth(self) -> None:
        """Refresh authentication to Halo Waypoint servers.

        wpauth MUST have a value for this to work. A lone 343 spartan token is not enough to generate a new one.
        """
        def handle_reply(_: Response):
            wpauth: str = decode_url(self.web_session.cookies.get('wpauth') or '')
            token: str = decode_url(self.web_session.cookies.get('343-spartan-token') or '')

            if wpauth and self.wpauth != wpauth:
                self.wpauth = wpauth
            if token:
                self.token = token

        self.web_session.get('https://www.halowaypoint.com/', finished=handle_reply)

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
