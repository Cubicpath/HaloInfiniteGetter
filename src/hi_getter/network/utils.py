###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utils for the HaloInfiniteGetter networking."""

__all__ = (
    'decode_url',
    'dict_to_cookie_list',
    'dict_to_query',
    'encode_url_params',
    'http_code_map',
)

from http import HTTPStatus
from urllib.parse import unquote as decode_url
from urllib.parse import urlencode as encode_url_params

from PySide6.QtCore import *
from PySide6.QtNetwork import *

# pylint: disable=not-an-iterable
http_code_map = {status.value: (status.phrase, status.description) for status in HTTPStatus}
for _code, _description in {
        400: 'Your search path has malformed syntax or bad characters.',
        401: 'No permission -- Your API token is most likely invalid.',
        403: 'Request forbidden -- You cannot get this resource with or without an API token.',
        404: 'No resource found at the given location.',
        405: 'Invalid method -- GET requests are not accepted for this resource.',
        406: 'Client does not support the given resource format.',
}.items():
    http_code_map[_code] = (http_code_map[_code][0], _description)
    del _code, _description


def dict_to_cookie_list(cookie_values: dict[str, str]) -> list[QNetworkCookie]:
    """Transforms a name and value pair into a list of :py:class:`QNetworkCookie` objects."""
    return [QNetworkCookie(
        name=name.encode('utf8'),
        value=value.encode('utf8')
    ) for name, value in cookie_values.items()]


def dict_to_query(params: dict[str, str]) -> QUrlQuery:
    """Transforms a param name and value pair into a :py:class:`QUrlQuery` object."""
    query = QUrlQuery()
    query.setQueryItems([(key, value) for key, value in params.items()])
    return query
