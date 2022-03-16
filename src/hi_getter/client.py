###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Loads data and defines the HTTP Client."""

__all__ = (
    'Client',
    'HTTP_CODE_MAP',
)

import json
import os
import random
import time
from http import HTTPStatus
from pathlib import Path
from typing import Any
from typing import Final
from urllib.parse import unquote as decode_escapes

from dotenv import load_dotenv
from requests import Response
from requests import Session
from requests.cookies import RequestsCookieJar
from requests.utils import guess_json_utf

from .constants import *
from .utils import dump_data
from .utils import unique_values

load_dotenv(verbose=True)

TOKEN_PATH:  Final[Path] = HI_CONFIG_PATH / 'token'
WPAUTH_PATH: Final[Path] = HI_CONFIG_PATH / 'wpauth'

# pylint: disable=not-an-iterable
HTTP_CODE_MAP = {status.value: (status.phrase, status.description) for status in HTTPStatus}
for _description in (
        (401, 'No permission -- Your API token is most likely invalid.'),
):
    code = _description[0]
    HTTP_CODE_MAP[code] = (HTTP_CODE_MAP[code][0], _description[1])
del _description


class Client:
    """HTTP REST Client that interfaces with Halo Waypoint to get data."""

    def __init__(self, **kwargs) -> None:
        """Initializes Halo Waypoint Client

        token is first taken from token kwarg, then SPARTAN_AUTH environment variable, then from user's token file.
        wpauth is first taken from wpauth kwarg, then WAYPOINT_AUTH environment variable, then from the user's wpauth file.

        :keyword token: Token to authenticate self to 343 API.
        :keyword wpauth: Halo Waypoint authentication key, allows for creation of 343 auth tokens.
        """
        self.SVC_HOST:       str = 'svc.halowaypoint.com'
        self.WEB_HOST:       str = 'www.halowaypoint.com'
        self.parent_path:    str = '/hi/'
        self.sub_host:       str = 'gamecms-hacs-origin'  # Must be defined before session headers
        self.searched_paths: dict = {}

        self._token: str | None = kwargs.pop('token', os.getenv('SPARTAN_AUTH', None))
        if self._token is None and TOKEN_PATH.is_file():
            self._token = TOKEN_PATH.read_text(encoding='utf8').strip()

        self._wpauth: str | None = kwargs.pop('wpauth', os.getenv('WAYPOINT_AUTH', None))
        if self._wpauth is None and WPAUTH_PATH.is_file():
            self._wpauth = WPAUTH_PATH.read_text(encoding='utf8').strip()

        self.session: Session = Session()
        self.session.headers = {
            'Accept': ', '.join(('application/json', 'text/plain', '*/*')),
            'Accept-Encoding': ', '.join(('gzip', 'deflate', 'br')),
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
            'x-343-authorization-spartan': self.token
        }

        self.cookies = RequestsCookieJar()
        self.set_cookie('343-spartan-token', self.token)
        self.set_cookie('wpauth', self.wpauth)

    def get(self, path: str, update_auth_on_401: bool = True, **kwargs) -> Response:
        """Get a :py:class:`Response` from HaloWaypoint.

        :param path: path to append to the API root
        :param update_auth_on_401: run self._refresh_auth if response status code is 401 Unauthorized
        :param kwargs: Key word arguments to pass to the requests GET Request.
        """
        response: Response = self.session.get(self.api_root + path.strip(), **kwargs)
        if not response.ok:
            if response.status_code == 401 and update_auth_on_401 and self.wpauth is not None:
                self.refresh_auth()
                response = self.get(path, False, **kwargs)
        return response

    def get_hi_data(self, path: str, only_dump: bool = False, dump_path: Path = HI_CACHE_PATH, micro_sleep: bool = True) -> dict[str, Any] | bytes | int | None:
        """Returns data from a path. Return type depends on the resource.

        :return: dict for JSON objects, bytes for media, int for error codes.
        """
        os_path: Path = dump_path / self.sub_host.replace('-', '_') / self.parent_path.strip('/') / path.replace('/file/', '/').lower()
        data: dict[str, Any] | bytes | int | None = None

        if not os_path.is_file():
            response: Response = self.get(path)
            if not response.ok:
                return response.status_code
            if 'json' in response.headers.get('content-type'):
                data = response.json()
            else:
                data = response.content

            print(f"DOWNLOADED {path} >>> {response.headers.get('content-type')}")
            dump_data(os_path, data)
            if micro_sleep:
                time.sleep(random.randint(100, 200) / 750)

        elif not only_dump:
            print(path)
            data = os_path.read_bytes()
            if os_path.suffix == '.json':
                data = json.loads(data.decode(guess_json_utf(data)))

        return data

    def hidden_key(self) -> str:
        """:return: The first and last 3 characters of the waypoint token, seperated by periods."""
        key = self.wpauth
        if key is not None and len(key) > 6:
            return f'{key[:3]}{"." * 50}{key[-3:]}'
        return 'None'

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
                    self.get_hi_data('images/file/' + value, True)

    def refresh_auth(self) -> None:
        """Refreshes authentication to Halo Waypoint servers.

        wpauth MUST have a value for this to work. A lone 343 spartan token is not enough to generate a new one.
        """
        web_headers = self.session.headers.copy()
        web_headers.pop('x-343-authorization-spartan')
        web_headers.update({
            'Accept': ','.join(('text/html', 'application/xhtml+xml', 'application/xml;q=0.9', 'image/avif', 'image/webp', '*/*;q=0.8')),
            'Host': self.WEB_HOST,
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })

        # FIXME: Not properly re-authenticating after using clear API token button
        response: Response = self.session.get('https://www.halowaypoint.com/', cookies=self.cookies, headers=web_headers)
        self.cookies.update(response.cookies)

        wpauth: str | None = decode_escapes(self.cookies.get('wpauth') or '') or None
        if wpauth is not None and self.wpauth != wpauth:
            self.wpauth = wpauth

        token: str | None = decode_escapes(self.cookies.get('343-spartan-token') or '') or None
        if token is not None:
            self.token = token

    def delete_cookie(self, name: str):
        """Delete given cookie if cookie exists, else pass."""
        if name in self.cookies:
            self.cookies.clear(domain=self.WEB_HOST, path='/', name=name)

    def set_cookie(self, name: str, value: str) -> None:
        """Set cookie value in Cookie jar. Defaults cookie domain as the WEB_HOST."""
        self.cookies.set(name=name, value=value, domain=self.WEB_HOST)

    @property
    def token(self) -> str | None:
        """343 auth token to authenticate self to API endpoints."""
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        if value is None:
            self._token = None
            self.delete_cookie('343-spartan-token')
            if TOKEN_PATH.is_file():
                TOKEN_PATH.unlink()
        else:
            value = decode_escapes(value)
            key_start_index = value.find('v4=')
            if key_start_index == -1:
                raise ValueError('token value is missing version identifier ("v4=") to signify start.')

            self._token = value[key_start_index:].rstrip()
            self.set_cookie('343-spartan-token', self._token)
            TOKEN_PATH.write_text(self._token)

        self.session.headers['x-343-authorization-spartan'] = self._token

    @property
    def wpauth(self) -> str | None:
        """Halo Waypoint auth key to create 343 spartan tokens."""
        return self._wpauth

    @wpauth.setter
    def wpauth(self, value: str | None) -> None:
        if value is None:
            self._wpauth = None
            self.delete_cookie('wpauth')
            if WPAUTH_PATH.is_file():
                WPAUTH_PATH.unlink()
        else:
            value = decode_escapes(value)
            self._wpauth = value.split(':')[-1].strip()
            self.set_cookie('wpauth', self._wpauth)
            WPAUTH_PATH.write_text(self._wpauth)

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
