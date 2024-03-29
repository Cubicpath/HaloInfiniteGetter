###################################################################################################
#                              MIT Licence (C) 2023 Cubicpath@Github                              #
###################################################################################################
"""Main networking package for HaloInfiniteGetter."""

__all__ = (
    'Client',
    'gc_response',
    'KNOWN_HEADERS',
    'NetworkSession',
    'Request',
    'Response',
    'VersionChecker',
)

from .client import Client
from .manager import gc_response
from .manager import KNOWN_HEADERS
from .manager import NetworkSession
from .manager import Request
from .manager import Response
from .version_check import VersionChecker
