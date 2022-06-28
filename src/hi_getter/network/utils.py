###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utils for the HaloInfiniteGetter networking."""

__all__ = (
    'decode_url',
    'dict_to_cookie_list',
    'dict_to_query',
    'encode_url_params',
    'guess_json_utf',
    'http_code_map',
    'is_error_status',
    'query_to_dict',
)

import codecs
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


def query_to_dict(query: QUrlQuery | str) -> dict[str, str]:
    """Translate a query string with the format of QUrl.query() to a dictionary representation."""
    if isinstance(query, QUrlQuery):
        query = query.query()
    query = query.lstrip('?')

    return {} if not query else {
        key: value for key, value in (
            pair.split('=') for pair in query.split('&')
        )
    }


def is_error_status(status: int) -> bool:
    """Returns True if the HTTP status code is an error status."""
    return 400 <= status < 600


# NOTICE:
#
# Requests
# Copyright 2019 Kenneth Reitz
# Apache 2.0 License


# Null bytes; no need to recreate these on each call to guess_json_utf
_NULL = "\x00".encode("ascii")  # encoding to ASCII for Python 3
_NULL2 = _NULL * 2
_NULL3 = _NULL * 3


def guess_json_utf(data):
    """
    :rtype: str
    """
    # JSON always starts with two ASCII characters, so detection is as
    # easy as counting the nulls and from their location and count
    # determine the encoding. Also detect a BOM, if present.
    sample = data[:4]
    if sample in (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE):
        return "utf-32"  # BOM included
    if sample[:3] == codecs.BOM_UTF8:
        return "utf-8-sig"  # BOM included, MS style (discouraged)
    if sample[:2] in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE):
        return "utf-16"  # BOM included
    null_count = sample.count(_NULL)
    if null_count == 0:
        return "utf-8"
    if null_count == 2:
        if sample[::2] == _NULL2:  # 1st and 3rd are null
            return "utf-16-be"
        if sample[1::2] == _NULL2:  # 2nd and 4th are null
            return "utf-16-le"
        # Did not detect 2 valid UTF-16 ascii-range characters
    if null_count == 3:
        if sample[:3] == _NULL3:
            return "utf-32-be"
        if sample[1:] == _NULL3:
            return "utf-32-le"
        # Did not detect a valid UTF-32 ascii-range character
    return None
