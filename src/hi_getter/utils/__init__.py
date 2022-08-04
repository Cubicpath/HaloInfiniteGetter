###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utility functions for hi_getter."""
from __future__ import annotations

__all__ = (
    'bit_rep',
    'create_shortcut',
    'current_requirement_licenses',
    'current_requirement_names',
    'current_requirement_versions',
    'delete_layout_widgets',
    'dump_data',
    'get_parent_doc',
    'has_package',
    'hide_windows_file',
    'icon_from_bytes',
    'init_objects',
    'patch_windows_taskbar_icon',
    'quote_str',
    'return_arg',
    'scroll_to_top',
    'set_or_swap_icon',
    'unique_values',
)

from .common import bit_rep
from .common import dump_data
from .common import get_parent_doc
from .common import return_arg
from .common import quote_str
from .common import unique_values
from .gui import delete_layout_widgets
from .gui import icon_from_bytes
from .gui import init_objects
from .gui import scroll_to_top
from .gui import set_or_swap_icon
from .package import current_requirement_licenses
from .package import current_requirement_names
from .package import current_requirement_versions
from .package import has_package
from .system import create_shortcut
from .system import get_desktop_path
from .system import get_start_menu_path
from .system import get_winreg_value
from .system import hide_windows_file
from .system import patch_windows_taskbar_icon
