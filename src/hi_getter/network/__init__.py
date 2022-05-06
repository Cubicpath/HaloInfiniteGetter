###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utils for the HaloInfiniteGetter client."""

__all__ = (
    'Client',
    'decode_url',
    'HTTP_CODE_MAP',
    'NetworkWrapper',
)

from .client import Client
from .manager import NetworkWrapper
from .utils import decode_url
from .utils import HTTP_CODE_MAP
