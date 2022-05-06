###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utils for the HaloInfiniteGetter networking."""

__all__ = (
    'decode_url',
    'HTTP_CODE_MAP',
)

from http import HTTPStatus
from urllib.parse import unquote as decode_url

# pylint: disable=not-an-iterable
HTTP_CODE_MAP = {status.value: (status.phrase, status.description) for status in HTTPStatus}
for _description in (
        (400, 'Your search path has malformed syntax or bad characters.'),
        (401, 'No permission -- Your API token is most likely invalid.'),
        (403, 'Request forbidden -- You cannot get this resource with or without an API token.'),
        (404, 'No resource found at the given location.'),
        (405, 'Invalid method -- GET requests are not accepted for this resource.'),
        (406, 'Client does not support the given resource format.'),
):
    _code: int = _description[0]
    HTTP_CODE_MAP[_code] = (HTTP_CODE_MAP[_code][0], _description[1])
del _description
