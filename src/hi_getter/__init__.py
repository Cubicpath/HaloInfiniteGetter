###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""A simple way to get live Halo data straight from Halo Waypoint."""
# TODO: Add logging functionality

__all__ = (
    'Client',
)

from ._version import __version__
from ._version import __version_info__
from .network import Client

__author__ = 'Cubicpath@Github <cubicpath@pm.me>'
"""Author's information."""
