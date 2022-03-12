###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Package initialization module. Import the Client and version info from here."""

__all__ = (
    'Client',
)

from ._version import __version__
from ._version import __version_info__
from .client import *

__author__ = 'Cubicpath@Github <cubicpath@pm.me>'
"""Author's information."""
