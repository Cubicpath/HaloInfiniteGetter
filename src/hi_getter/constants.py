###################################################################################################
#                              MIT Licence (C) 2023 Cubicpath@Github                              #
###################################################################################################
"""Neutral namespace for constants. Meant to be star imported."""
from __future__ import annotations

__all__ = (
    'BYTE_UNITS',
    'HI_CACHE_PATH',
    'HI_CONFIG_PATH',
    'HI_DATE_FORMAT',
    'HI_PACKAGE_NAME',
    'HI_PATH_PATTERN',
    'HI_RESOURCE_PATH',
    'HI_SAMPLE_RESOURCE',
    'HI_TOKEN_PATH',
    'HI_URL_PATTERN',
    'HI_WEB_DUMP_PATH',
    'HI_WPAUTH_PATH',
    'MARKDOWN_IMG_LINK_PATTERN',
    'MARKDOWN_REF_LINK_PATTERN',
    'RFC_5646_PATTERN',
    'SUPPORTED_IMAGE_EXTENSIONS',
    'SUPPORTED_IMAGE_MIME_TYPES',
)

import re
from pathlib import Path
from typing import Final

# Mappings

BYTE_UNITS = {'Bytes': 1024**0, 'KiB': 1024**1, 'MiB': 1024**2, 'GiB': 1024**3, 'TiB': 1024**4}
"""Mapping of byte units to their respective powers of 1024."""

# Sets

SUPPORTED_IMAGE_EXTENSIONS: Final[frozenset[str]] = frozenset({
    'bmp', 'cur', 'gif', 'icns', 'ico', 'jpeg', 'jpg', 'pbm', 'pgm', 'png',
    'ppm', 'svg', 'svgz', 'tga', 'tif', 'tiff', 'wbmp', 'webp', 'xbm', 'xpm'
})
"""Set containing all image file extensions supported by application."""

SUPPORTED_IMAGE_MIME_TYPES: Final[frozenset[str]] = frozenset({
    'image/bmp', 'image/gif', 'image/jpeg', 'image/png', 'image/svg+xml', 'image/svg+xml-compressed',
    'image/tiff', 'image/vnd.microsoft.icon', 'image/vnd.wap.wbmp', 'image/webp', 'image/x-icns',
    'image/x-portable-bitmap', 'image/x-portable-graymap', 'image/x-portable-pixmap', 'image/x-tga',
    'image/x-xbitmap', 'image/x-xpixmap'
})
"""Set containing all image mime types supported by application."""

# Strings

HI_DATE_FORMAT: Final[str] = '%Y-%m-%dT%H:%M:%S.%fZ'
"""Format to use for datetime objects."""

HI_PACKAGE_NAME: Final[str] = __package__.split('.', maxsplit=1)[0] if __package__ else ''
"""The base package name for this application, for use in sub-packages."""

HI_SAMPLE_RESOURCE: Final[str] = 'Progression/file/Calendars/Seasons/SeasonCalendar.json'
"""Example resource. Is pre-filled in the search bar."""

# Paths

HI_CACHE_PATH: Final[Path] = Path.home() / '.cache/hi_getter'
"""Directory containing cached API results."""

HI_CONFIG_PATH: Final[Path] = Path.home() / '.config/hi_getter'
"""Directory containing user configuration data."""

HI_RESOURCE_PATH: Final[Path] = Path(__file__).parent / 'resources'
"""Directory containing application resources."""

HI_TOKEN_PATH: Final[Path] = HI_CONFIG_PATH / '.token'
"""File containing api token."""

HI_WEB_DUMP_PATH: Final[Path] = HI_CACHE_PATH / 'cached_requests'
"""Directory to dump web requests to."""

HI_WPAUTH_PATH: Final[Path] = HI_CONFIG_PATH / '.wpauth'
"""File containing auth key (Used for API token generation)."""

# Patterns

HI_PATH_PATTERN: Final[re.Pattern] = re.compile(
    r'[/\\]?(?P<pre_path>[\w\-_.]+[/\\]file[/\\])?'
    r'(?P<dir_name>(?:[\w\-_.]+[/\\])+)'
    r'(?P<file_name>[\w\-_]*\.\w+)')
"""Regex pattern for finding a resource path.
Finds quoted substrings with at least one folder name and file name (with a file extension).
"""

HI_URL_PATTERN: Final[re.Pattern] = re.compile(
    r'(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|'
    r'[a-z0-9.\-]+[.][a-z]{2,}/)(?:[^\s()<>{}\[\]]+|'
    r'\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|'
    r'\(\S+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|'
    r'\(\S+?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’])|'
    r'(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.][a-z]{2,}\b/?(?!@))')
"""Regex pattern for finding URLs.
Derived from https://gist.github.com/gruber/8891611.
"""

MARKDOWN_IMG_LINK_PATTERN: Final[re.Pattern] = re.compile(
    r'\[!\s*(?P<alt>\[[^\t\n\r()\[\]]*])\s*'
    r'(?P<image>\([\S ]+\))]\s*'
    r'(?P<target>[\[(][^\t\n\r()\[\]]*[)\]])')
"""Regex pattern for finding image links."""

MARKDOWN_REF_LINK_PATTERN: Final[re.Pattern] = re.compile(
    r'\[(?P<label>[^\[\]]+)] *: *'
    r'(?P<url>(?:(?:[a-zA-Z]+)?://)?'
    r'\w+(?:\.\w+)*(?::\d{1,5})?'
    r'(?:/[^\s()]*)?(?:\?(?:\w+=\w+&?)+)?)'
    r'(?: \"(?P<description>[^\"\t\n\r]*)\")?')
"""Regex pattern for finding markdown labels."""

RFC_5646_PATTERN: Final[re.Pattern] = re.compile(
    r'^(?=[a-z])(?:(?P<language>(?P<primary>[a-z]{2,3})(?:-(?P<extlang>[a-z]{3}))?)?'
    r'(?:-(?P<script>[a-z]{4}))?'
    r'(?:-(?P<region>[a-z]{2}|\d{3}))?'
    r'(?:-(?P<variants>(?:(?<![a-z\d])(?:[a-z\d]{5,8}|\d[a-z\d]{3})-?)+(?<!-)))?'
    r'(?:-(?P<extensions>(?:(?<![a-z\d])[a-wy-z\d]-[a-z\d]{2,8}-?)+(?<!-)))?)?'
    r'(?:-?(?<![a-z\d])(?P<private>x-(?:(?<![a-z\d])[a-z\d]{1,8}-?)+(?<!-)))?$',
    flags=re.IGNORECASE | re.ASCII)
"""Regex pattern for validating a language tag (langtag). Follows https://datatracker.ietf.org/doc/html/rfc5646

Uniqueness of variant subtags and extension singletons must be done outside of this pattern.

The language subtag is the primary subtag with the optional extlang subtag appended.

Most langtags are formatted as {language}-{REGION}.
Example langtags that follow RFC 5646::

    - "en" represents English ('en') with no region identifier.
    - "es-ES" represents Spanish ('es') as used in Spain ('ES').
    - "de-AT" represents German ('de') as used in Austria ('AT').
    - "sr-Latn" represents Serbian written using the Latin script.
    - "sr-Latn-RS" represents Serbian ('sr') written using Latin script ('Latn') as used in Serbia ('RS').
    - "es-419" represents Spanish ('es') appropriate to the UN-defined Latin America and Caribbean region ('419').
    - "sl-nedis" represents the Natisone or Nadiza dialect of Slovenian.
    - "de-CH-1996" represents German as used in Switzerland and as written using the spelling
            reform beginning in the year 1996 C.E.
    - en-a-bbb-x-a-ccc
    - x-private-tag-example
"""
