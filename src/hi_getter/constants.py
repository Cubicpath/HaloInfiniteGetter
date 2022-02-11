###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Neutral namespace for constants."""
from pathlib import Path
from typing import Final

__all__ = (
    'CONFIG_PATH',
    'RESOURCE_PATH',
)


CONFIG_PATH:   Final[Path] = Path.home() / '.config/hi_getter'
"""Directory containing user configuration data."""

RESOURCE_PATH: Final[Path] = Path(__file__).parent / 'resources'
"""Directory containing application resources."""
