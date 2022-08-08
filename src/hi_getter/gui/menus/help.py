###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Help menu implementation."""
from __future__ import annotations

__all__ = (
    'HelpContextMenu',
)

import sys
import webbrowser
from platform import platform

from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..._version import __version_info__
from ...constants import *
from ...models import DeferredCallable
from ...utils.package import current_requirement_versions
from ..app import app
from ..app import tr


# noinspection PyArgumentList
class HelpContextMenu(QMenu):
    """Context menu that shows actions to help the user."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`HelpContextMenu`."""
        from ..windows import LicenseViewer
        from ..windows import ReadmeViewer

        super().__init__(parent)

        # Make sure when instantiating QObjects that those QObjects reference a Python object that re-references that QObject,
        # otherwise the QObject will not be considered "in use" by the garbage collector, and will be deleted.
        self.license_window = LicenseViewer()
        self.readme_window = ReadmeViewer()

        github_view: QAction = QAction(
            app().icon_store['github'],
            tr('gui.menus.help.github'), self, triggered=DeferredCallable(
                webbrowser.open, 'https://github.com/Cubicpath/HaloInfiniteGetter/', new=2, autoraise=True
            )
        )

        create_issue: QAction = QAction(
            app().icon_store['github'],
            tr('gui.menus.help.issue'), self, triggered=DeferredCallable(
                webbrowser.open, 'https://github.com/Cubicpath/HaloInfiniteGetter/issues/new/choose', new=2, autoraise=True
            )
        )

        about_view: QAction = QAction(
            app().get_theme_icon('message_question') or app().icon_store['about'],
            tr('gui.menus.help.about'), self, triggered=self.open_about
        )

        about_qt_view: QAction = QAction(
            app().get_theme_icon('message_question') or app().icon_store['about'],
            tr('gui.menus.help.about_qt'), self, triggered=DeferredCallable(
                QMessageBox(self).aboutQt, self, tr('about.qt.title')
            )
        )

        license_view: QAction = QAction(
            app().icon_store['copyright'],
            tr('gui.menus.help.license'), self, triggered=self.license_window.show
        )

        readme: QAction = QAction(
            app().get_theme_icon('message_information') or self.style().standardIcon(QStyle.SP_DialogApplyButton),
            tr('gui.menus.help.readme'), self, triggered=self.readme_window.show
        )

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
                self.package_versions()
            )
        )

    @staticmethod
    def package_versions() -> str:
        """Generate the package version list for use in the about message.

        :return: Package version list seperated by newlines.
        """
        return '\n'.join(
            tr(
                'about.app.package_version',
                package, version
            ) for package, version in current_requirement_versions(HI_PACKAGE_NAME, include_extras=True).items()
        )
