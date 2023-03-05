###################################################################################################
#                              MIT Licence (C) 2023 Cubicpath@Github                              #
###################################################################################################
"""Defines the HaloInfiniteGetter HTTP Client."""
from __future__ import annotations

__all__ = (
    'cached_etags',
    'Client',
)

import json
import os
from collections.abc import Callable
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Final
from urllib.parse import quote

from PySide6.QtCore import *

from ..constants import *
from ..models import CaseInsensitiveDict
from ..models import DeferredCallable
from ..utils import dump_data
from ..utils import decode_url
from ..utils import guess_json_utf
from ..utils import hide_windows_file
from ..utils import unique_values
from .manager import NetworkSession
from .manager import Response

_ENDPOINT_PATH: Final[Path] = HI_RESOURCE_PATH / 'wp_endpoint_hosts.json'
_ETAG_PATH: Final[Path] = HI_CACHE_PATH / 'etags.json'


def cached_etags() -> dict[str, Any]:
    """JSON representation of the currently cached etags.

    If etag data is malformed JSON, back it up to ``etags.malformed``.
    """
    if not _ETAG_PATH.is_file():
        _ETAG_PATH.write_text('{}', encoding='utf8')

    data: bytes = _ETAG_PATH.read_bytes()
    etags: dict[str, Any] = {}

    try:
        etags = json.loads(data)
    except json.JSONDecodeError:
        if data:
            _ETAG_PATH.with_suffix('.malformed').write_bytes(data)

        _ETAG_PATH.write_text('{}', encoding='utf8')

    return etags


def save_etags(etags: dict[str, Any]) -> int:
    """Save dictionary representation of etags to ``_ETAGS_PATH``."""
    return _ETAG_PATH.write_text(json.dumps(etags, indent=2))


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
        self.endpoints: dict[str, Any] = json.loads(_ENDPOINT_PATH.read_bytes())
        self.check_etags: bool = True
        self._auth_in_progress: bool = False
        self._emit_received_signals: bool = True
        self._recursive_calls_in_progress: int = 0

        self.etags: dict[str, Any] = cached_etags()
        self.parent_path: str = '/hi/'
        self.sub_host: str = self.endpoints['endpoints']['gameCmsService']['subdomain']
        self.searched_paths: set[str] = set()
        self.finishedSearch.connect(self._on_finished_search)

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0',
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
                print(response, response.get_internal_error())
                print(f'COULDNT GET {response.url}')
                return

            if not response.ok:
                # Handle errors
                if response.code == 401 and update_auth_on_401 and self.wpauth is not None:
                    self.refresh_auth()
                    self._get(path, False, finished, **kwargs)
                elif finished is not None:
                    # Send ERR response to the given consumer
                    finished(response)

            elif finished is not None:
                # Send OK response to the given consumer
                finished(response)

        self.api_session.get(self.api_root + path.strip(), finished=handle_reply, **kwargs)

    def _check_etag(self,
                    path: str,
                    update_auth_on_401: bool = True,
                    consumer: Callable[[str, dict[str, Any] | bytes | int], None] | None = None,
                    **kwargs) -> None:
        def handle_reply(response: Response):
            if not response.code or not (etag := response.headers.get('ETag', '').strip('"')):
                print(f'COULDNT CHECK {response.url}', response.get_internal_error())
                return

            if response.code == 401 and update_auth_on_401 and self.wpauth is not None:
                self.refresh_auth()
                self._check_etag(path, False, consumer, **kwargs)
                return

            path_key: str = f'{self.host}{self.parent_path}{path}'.lower()
            is_new_version: bool = etag not in self.etags.get('paths', {}).get(path_key, {}).get('etags', [])
            self._store_etag(path, etag)

            # If there is a new version available, and we have an old version, download the new version.
            # and cache the old version in a separate directory.
            # If we don't an old version, assume the new version is currently being downloaded by get_hi_data.
            if is_new_version and (cached_path := self.to_os_path(path)).is_file():
                archive_path: Path = self.to_os_path(path, parent=HI_CACHE_PATH / 'old_files').with_stem(
                    f'{cached_path.stem}_etag+{quote(etag, safe="")}'
                )
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                archive_path.write_bytes(cached_path.read_bytes())
                cached_path.unlink()

                self.get_hi_data(path, consumer, check_etag_override=False)

        self.api_session.head(self.api_root + path.strip(), finished=handle_reply, **kwargs)

    def _handle_json(self, data: dict[str, Any], recursive: bool = False):
        """Look through JSON data for resource paths.

        :param data: JSON data to search through for paths.
        :param recursive: Whether to start recursively searching.
        """
        for value in unique_values(data):
            if isinstance(value, str) and (match := HI_PATH_PATTERN.match(value)):
                new_path: str = self.normalize_search_path(match[0])

                if not recursive:
                    self.get_hi_data(
                        new_path,
                        consumer=DeferredCallable(save_etags, self.etags),
                        emit_signals=self._emit_received_signals
                    )
                    continue

                # If it's an image, download it then ignore the result
                if match['file_name'].split('.')[-1].lower() in SUPPORTED_IMAGE_EXTENSIONS:
                    if new_path in self.searched_paths:
                        continue

                    self.searched_paths.add(new_path)
                    self.get_hi_data(
                        new_path,
                        emit_signals=self._emit_received_signals
                    )

                # Otherwise, start the process over again
                else:
                    if new_path in self.searched_paths:
                        continue

                    self.searched_paths.add(new_path)
                    self.recursive_search(new_path)

    def _increment_counter(self):
        self._recursive_calls_in_progress += 1
        if self._recursive_calls_in_progress == 1:
            self.startedSearch.emit()

    def _decrement_counter(self):
        self._recursive_calls_in_progress -= 1
        if not self._recursive_calls_in_progress:
            self.finishedSearch.emit()

    def _on_finished_search(self):
        self._emit_received_signals = True
        self.searched_paths.clear()
        save_etags(self.etags)

    def _store_etag(self, path: str, etag: str):
        path_key: str = f'{self.host}{self.parent_path}{path}'.lower()
        path_etags: list[str] = self.etags.get('paths', {}).get(path_key, {}).get('etags', [])

        # Do this instead of using a set
        # 1 iteration (in) vs 2 (casting to set then back to list for json.dumps)
        if etag not in path_etags:
            path_etags.append(etag)

        self.etags['timestamps'] = self.etags.get('timestamps', {}) | {
            etag: datetime.now(timezone.utc).strftime(HI_DATE_FORMAT)
        }

        self.etags['paths'] = self.etags.get('paths', {}) | {
            path_key: {
                'etags': path_etags
            }
        }

    def get_hi_data(self,
                    path: str,
                    consumer: Callable[[str, dict[str, Any] | bytes | int], None] | None = None,
                    emit_signals: bool = True,
                    check_etag_override: bool | None = None
                    ) -> None:
        """Get a resource hosted on the HaloWaypoint API.

        Resulting resource is returned via a positional argument in a `received-` signal or the given consumer.

        :param path: Path to get data from.
        :param consumer: Consumer to send received data to.
        :param emit_signals: Whether to emit received* signals.
        :param check_etag_override: Whether to call ``_check_etag`` if path is already cached.
        :raises ValueError: If the response is not JSON or a supported image type.
        """
        check_etags = self.check_etags
        if check_etag_override is not None:
            check_etags = check_etag_override

        path = self.normalize_search_path(path)
        os_path: Path = self.to_os_path(path)

        if not os_path.is_file():
            def handle_reply(response: Response):
                if response.code and not response.ok:
                    print(f'ERROR [{response.code}] for {path} ')
                    if emit_signals:
                        self.receivedError.emit(path, response.code)
                    if consumer is not None:
                        consumer(path, response.code)
                    return

                content_type: str | None = response.headers.get('Content-Type')
                response_data: dict[str, Any] | bytes

                if etag := response.headers.get('ETag', '').strip('"'):
                    self._store_etag(path, etag)

                if not content_type:
                    raise ValueError('Successful status code but no Content-Type header.')

                if 'json' in content_type:
                    response_data = response.json
                    if emit_signals:
                        self.receivedJson.emit(path, response_data)
                elif content_type in SUPPORTED_IMAGE_MIME_TYPES:
                    response_data = response.data
                    if emit_signals:
                        self.receivedData.emit(path, response_data)
                else:
                    raise ValueError(f'Unsupported content type received: {content_type}')

                print(f'DOWNLOADED {path} >>> {content_type}')
                dump_data(os_path, response_data)
                if consumer is not None:
                    consumer(path, response_data)

            self._get(path, finished=handle_reply, timeout=120)

        else:
            if check_etags:
                self._check_etag(path, consumer=consumer, timeout=120)

            print(f'READING {path}')
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
        self._emit_received_signals = False
        self._increment_counter()
        self.get_hi_data(
            path,
            consumer=self.handle_recursive_data,
            emit_signals=self._emit_received_signals
        )

    def start_handle_json(self, data: dict[str, Any], recursive: bool = False):
        """Look through JSON data for resource paths.

        Increments and decrements counter to correctly emit the ``finishedSearch`` signal.

        :param data: JSON data to search through for paths.
        :param recursive: Whether to start recursively searching.
        """
        if recursive:
            self._increment_counter()

        self._handle_json(data, recursive)

        if recursive:
            self._decrement_counter()

    def handle_recursive_data(self, path: str, data: dict[str, Any] | bytes | int) -> None:
        """Recursively look through JSON data for resource paths, decrementing counter when finished.

        :param path: Path data is from.
        :param data: Data received from path. If not JSON, return early.
        """
        # This set is shared between all recursive calls, so no duplicate searches should occur
        self.searched_paths.add(path)

        if isinstance(data, (bytes, int)):
            # Return early, decrementing counter
            self._decrement_counter()
            return

        # Iterate over all values in the JSON data
        # This process ignores already-searched values
        self._handle_json(data, recursive=True)
        self._decrement_counter()

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
        path = path.lower().strip().lstrip('/')
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
        """Translate a given GET path to the equivalent cache location.

        ``path`` is assumed to be normalized.

        :param path: path to translate.
        :param parent: OS path to use as parent directory.
        """
        return parent / self.sub_host.replace('-', '_') / self.parent_path.strip('/') / path

    def to_get_path(self, path: Path) -> str:
        """Translate a given cache location to the equivalent GET path.

        Return an empty string if path doesn't include an endpoint following the parent_path.
        """
        no_etag: Path = path.with_stem(path.stem.split('_etag+', maxsplit=1)[0])
        resource = no_etag.as_posix().split(self.parent_path, maxsplit=1)[-1]
        if Path(resource).is_absolute():
            return ''

        return resource

    def refresh_auth(self) -> None:
        """Refresh authentication to Halo Waypoint servers.

        wpauth MUST have a value for this to work. A lone 343 spartan token is not enough to generate a new one.
        """
        print('REFRESHING AUTH')

        if self._auth_in_progress:
            return
        self._auth_in_progress = True

        def handle_reply(_: Response):
            wpauth: str = decode_url(self.web_session.cookies.get('wpauth') or '')
            token: str = decode_url(self.web_session.cookies.get('343-spartan-token') or '')

            if wpauth and self.wpauth != wpauth:
                self.wpauth = wpauth
            if token:
                self.token = token

            self._auth_in_progress = False

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
