###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Main networking package for HaloInfiniteGetter."""

__all__ = (
    'Client',
    'NetworkSession',
)

from .client import Client
from .manager import NetworkSession
