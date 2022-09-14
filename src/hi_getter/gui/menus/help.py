###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Help menu implementation."""
from __future__ import annotations

__all__ = (
    'HelpContextMenu',
    'package_versions',
)

import sys
import webbrowser
from platform import platform

from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..._version import __version_info__
from ...constants import *
from ...models import DeferredCallable
from ...utils.gui import init_objects
from ...utils.package import current_requirement_versions
from ..app import app
from ..app import tr


def package_versions() -> str:
    """Generate the package version list for use in the about message.

    :return: Package version list separated by newlines.
    """
    return '\n'.join(
        tr('about.app.package_version', package, version) for
        package, version in current_requirement_versions(HI_PACKAGE_NAME, include_extras=True).items()
    )


# noinspection PyArgumentList
class HelpContextMenu(QMenu):
    """Context menu that shows actions to help the user."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`HelpContextMenu`."""
        super().__init__(parent)

        init_objects({
            (github_view := QAction(self)): {
                'text': tr('gui.menus.help.github'),
                'icon': app().icon_store['github'],
                'triggered': DeferredCallable(
                    webbrowser.open, 'https://github.com/Cubicpath/HaloInfiniteGetter/', new=2, autoraise=True
                )
            },

            (create_issue := QAction(self)): {
                'text': tr('gui.menus.help.issue'),
                'icon': app().icon_store['github'],
                'triggered': DeferredCallable(
                    webbrowser.open, 'https://github.com/Cubicpath/HaloInfiniteGetter/issues/new/choose', new=2, autoraise=True
                )
            },

            (about_view := QAction(self)): {
                'text': tr('gui.menus.help.about'),
                'icon': app().get_theme_icon('message_question') or app().icon_store['about'],
                'triggered': self.open_about
            },

            (about_qt_view := QAction(self)): {
                'text': tr('gui.menus.help.about_qt'),
                'icon': app().get_theme_icon('message_question') or app().icon_store['about'],
                'triggered': DeferredCallable(
                    QMessageBox(self).aboutQt, self, tr('about.qt.title')
                )
            },

            (license_view := QAction(self)): {
                'text': tr('gui.menus.help.license'),
                'icon': app().icon_store['copyright'],
                'triggered': lambda: app().windows['license_viewer'].show()
            },

            (readme := QAction(self)): {
                'text': tr('gui.menus.help.readme'),
                'icon': app().get_theme_icon('message_information') or self.style().standardIcon(QStyle.SP_DialogApplyButton),
                'triggered': lambda: app().windows['readme_viewer'].show()
            }
        })

        section_map = {
            'Github': (github_view, create_issue),
            'Information': (about_view, about_qt_view, license_view, readme)
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

    # pylint: disable=not-an-iterable
    def open_about(self) -> None:
        """Open the application's about section."""
        app().show_dialog(
            'about.app', self,
            description_args=(
                *__version_info__, platform(), sys.implementation.name,
                sys.version.split('[', maxsplit=1)[0],
                package_versions()
            )
        )