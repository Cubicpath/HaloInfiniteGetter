###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Neutral namespace for constants."""

__all__ = (
    'CACHE_PATH',
    'CONFIG_PATH',
    'PATH_PATTERN',
    'RESOURCE_PATH',
    'SAMPLE_RESOURCE',
)

import re
from pathlib import Path
from typing import Final

SAMPLE_RESOURCE: Final[str] = 'Progression/file/Calendars/Seasons/SeasonCalendar.json'
"""Example resource. Is pre-filled in the search bar."""

PATH_PATTERN:    Final[re.Pattern] = re.compile(r'\"([\w\-_]+/)+[\w\-_]*\.\w+\"')
"""Regex pattern for finding a resource path. Finds quoted substrings with at least one folder name and file name (with a file extension)."""

CACHE_PATH:      Final[Path] = Path.home() / '.cache/hi_getter'
"""Directory containing cached API results."""

CONFIG_PATH:     Final[Path] = Path.home() / '.config/hi_getter'
"""Directory containing user configuration data."""

RESOURCE_PATH:   Final[Path] = Path(__file__).parent / 'resources'
"""Directory containing application resources."""
