###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Package initialization module. Import the Client and version info from here."""
# TODO: Add logging functionality

__all__ = (
    'Client',
)

from ._version import __version__
from ._version import __version_info__
from .network import Client

__author__ = 'Cubicpath@Github <cubicpath@pm.me>'
"""Author's information."""
