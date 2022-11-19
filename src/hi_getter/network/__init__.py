###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Main networking package for HaloInfiniteGetter."""

__all__ = (
    'Client',
    'NetworkSession',
    'Response',
)

from .client import Client
from .manager import NetworkSession
from .manager import Response
