###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Main networking package for HaloInfiniteGetter."""

__all__ = (
    'Client',
    'http_code_map',
    'NetworkSession',
)

from .client import Client
from .manager import NetworkSession
from .utils import http_code_map
