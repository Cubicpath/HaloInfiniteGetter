###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Loads data and defines the HTTP Client."""
import json
import os
import random
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from requests import Response
from requests import Session
from requests.utils import guess_json_utf

from .constants import CONFIG_PATH
from .utils import *

__all__ = (
    'Client',
)

load_dotenv(verbose=True)


class Client:
    """HTTP REST Client that interfaces with HaloWaypoint to get data."""
    HOST: str = 'svc.halowaypoint.com'
    PARENT_PATH: str = '/hi/'

    def __init__(self, **kwargs) -> None:
        """Initializes HaloWaypoint Client

        API Key is first taken from auth kwarg, then SPARTAN_AUTH environment variable, then from the user's config directory.

        :keyword auth: Token to authenticate self to 343 API.
        """
        user_key_path = CONFIG_PATH / 'api_key'
        self._auth: str = kwargs.pop('auth', os.getenv('SPARTAN_AUTH', user_key_path.read_text(encoding='utf8').strip() if user_key_path.is_file() else None))
        self.sub_host: str = 'gamecms-hacs-origin'  # Must be defined before session headers

        self.searched_paths = {}
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
            'x-343-authorization-spartan': self._auth
        }
        self.session.cookies.set('343-spartan-token', self._auth)
        data_path = Path.cwd() / 'hi_data'
        if not data_path.is_dir():
            os.mkdir(data_path)

    # def _refresh_auth(self) -> None:
    #     self._AUTH = ...

    def get(self, path: str, **kwargs) -> Response:
        """Get a :py:class:`Response` from HaloWaypoint and update cookies.

        :param path: path to append to the API root
        :param kwargs: Key word arguments to pass to the requests GET Request.
        """
        response: Response = self.session.get(self.api_root + path.strip(), **kwargs)
        self.session.cookies.update(response.cookies)
        if not response.ok:
            if response.status_code == 401:
                ...
                # TODO: Automatically refresh api key
                # print('test')
                # self._refresh_auth()
                # time.sleep(1)
                # response = self.get(path, **kwargs)
        return response

    def get_hi_data(self, path: str, only_dump: bool = False, dump_path: Path = Path.cwd()) -> dict[str, Any] | bytes | int | None:
        """Returns data from a path. Return type depends on the resource.

        :return: dict for JSON objects, bytes for media, int for error codes.
        """
        os_path: Path = dump_path / Path(('hi_data/' + path.replace('/file/', '/')).lower())
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
            time.sleep(random.randint(100, 200) / 750)

        elif not only_dump:
            print(path)
            data = os_path.read_bytes()
            if os_path.suffix == '.json':
                data = json.loads(data.decode(guess_json_utf(data)))

        return data

    def recursive_search(self, search_path: str) -> None:
        """Recursively get Halo Infinite files linked to the search_path through Mapping keys."""
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

    @property
    def auth_key(self) -> str:
        """343 auth token to authenticate self to HaloWaypoint."""
        return self._auth

    @auth_key.setter
    def auth_key(self, value: str) -> None:
        self._auth = value
        self.session.headers.update({'x-343-authorization-spartan': self._auth})
        self.session.cookies.set('343-spartan-token', self._auth)

    @property
    def api_root(self) -> str:
        """Root of sent API requests."""
        return f'https://{self.host}{self.PARENT_PATH}'

    @property
    def host(self) -> str:
        """Host to send to."""
        return f'{self.sub_host}.{self.HOST}'

    @host.setter
    def host(self, value: str) -> None:
        self.sub_host = value
