###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Main networking package for HaloInfiniteGetter."""

__all__ = (
    'Client',
    'decode_url',
    'dict_to_cookie_list',
    'dict_to_query',
    'encode_url_params',
    'http_code_map',
    'NetworkSession',
)

from .client import Client
from .manager import NetworkSession
from .utils import decode_url
from .utils import dict_to_cookie_list
from .utils import dict_to_query
from .utils import encode_url_params
from .utils import guess_json_utf
from .utils import http_code_map
from .utils import is_error_status
from .utils import query_to_dict
