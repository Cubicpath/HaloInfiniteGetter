###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Neutral namespace for holding type references."""

__all__ = (
    'CommentValue',
    'TOML_VALUE',
)

from pathlib import PurePath
from types import UnionType

from toml.decoder import CommentValue

TOML_VALUE: UnionType = dict | list | float | int | str | bool | PurePath
"""Represents a possible TOML value, with :py:class:`dict` being a Table, and :py:class:`list` being an Array."""
