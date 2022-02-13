###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing :py:class:`QMenu` Context Menus."""
import sys
import webbrowser
from importlib import metadata
from platform import platform
from shutil import rmtree

import requests
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from .._version import __version_info__ as ver
from ..constants import *
from .widgets import LicenseViewer

__all__ = (
    'HelpContextMenu',
    'FileContextMenu',
)


# noinspection PyArgumentList
class HelpContextMenu(QMenu):
    """Context menu that shows actions to help the user."""

    _about: tuple[str, str] | None = None
    _github_icon: bytes | None = None

    def __init__(self, parent) -> None:
        """Create a new :py:class:`HelpContextMenu`."""
        super().__init__(parent)

        self.license_window = LicenseViewer()

        if self._github_icon is None:
            self.__class__._github_icon = requests.get('https://github.githubassets.com/favicons/favicon.png').content

        ico_pixmap = QPixmap()
        ico_pixmap.loadFromData(self._github_icon)

        github_view = QAction(QIcon(ico_pixmap), 'View on GitHub', self, triggered=self.open_github)
        create_issue = QAction(QIcon(ico_pixmap), 'Create an issue', self, triggered=self.open_issues)
        license_view = QAction(QIcon(str(RESOURCE_PATH / 'icons/copyright.ico')), 'License', self, triggered=self.open_license)
        about_view = QAction(QIcon(str(RESOURCE_PATH / 'icons/about.ico')), 'About', self, triggered=self.open_about)
        self.addSection('Github')
        self.addAction(github_view)
        self.addAction(create_issue)
        self.addSection('Information')
        self.addAction(license_view)
        self.addAction(about_view)

    @staticmethod
    def open_github() -> None:
        """Open the project's GitHub repository in the user's default browser."""
        webbrowser.open('https://github.com/Cubicpath/HaloInfiniteGetter/', new=2, autoraise=True)

    @staticmethod
    def open_issues() -> None:
        """Creates a new GitHub issue using the user's default browser."""
        webbrowser.open('https://github.com/Cubicpath/HaloInfiniteGetter/issues/new', new=2, autoraise=True)

    def open_license(self) -> None:
        """Show the :py:class:`LicenseViewer` window."""
        self.license_window.show()

    # pylint: disable=not-an-iterable
    def open_about(self) -> None:
        """Open the application's about section."""
        self.setWindowIcon(QIcon(str(RESOURCE_PATH / 'icons/about.ico')))
        QMessageBox.information(self, *self.about_message())

    def about_message(self) -> tuple[str, str]:
        """Generate the 'About' information regarding the application's environment.
        Since this takes a while the first time, the result is cached as a class value.

        :return: Tuple containing the title and the message
        """
        if self._about is None:
            self.__class__._about = ('About', f'''
HaloInfiniteGetter by Cubicpath. A simple way to get live Halo data straight from Halo Waypoint.

Version Info: major:{ver[0]}, minor:{ver[1]}, micro:{ver[2]}, releaselevel:{ver[3]}, serial:{ver[4]}

Running on:
\t{platform()}
\t{sys.implementation.name} {sys.version.split('[', maxsplit=1)[0]}

Using requests: {metadata.version("requests")}
Using PyQT6: {metadata.version("PyQT6")}
Using python-dotenv: {metadata.version("python-dotenv")}

MIT Licence (C) 2022 Cubicpath@Github
''')
        return self._about


# noinspection PyArgumentList
class FileContextMenu(QMenu):
    """Context menu that shows actions to manipulate files."""
    def __init__(self, parent) -> None:
        """Create a new :py:class:`FileContextMenu`."""
        super().__init__(parent)

        open_in = QAction(QIcon(str(RESOURCE_PATH / 'icons/folder.ico')), 'Open In Explorer', self, triggered=self.open_explorer)
        flush_cache = QAction(QIcon(str(RESOURCE_PATH / 'icons/folder.ico')), 'Flush Cache', self, triggered=self.flush_cache)
        import_from = QAction(QIcon(str(RESOURCE_PATH / 'icons/import.ico')), 'Import Data from...', self, triggered=self.import_data)
        export_to = QAction(QIcon(str(RESOURCE_PATH / 'icons/export.ico')), 'Export Data', self, triggered=self.export_data)
        self.addAction(open_in)
        self.addAction(flush_cache)
        self.addAction(import_from)
        self.addAction(export_to)

        # TODO: Add functionality and enable
        flush_cache.setDisabled(tuple(CACHE_PATH.iterdir()) == ())  # Set disabled if CACHE_PATH directory is empty
        import_from.setDisabled(True)
        export_to.setDisabled(True)

    @staticmethod
    def open_explorer() -> None:
        """Open the user's file explorer in the current application's export directory."""
        webbrowser.open(f'file:///{CACHE_PATH}')

    @staticmethod
    def flush_cache() -> None:
        """Remove all data from cache."""
        rmtree(CACHE_PATH)
        CACHE_PATH.mkdir()

    def import_data(self) -> None:
        """Import data from..."""
        ...

    def export_data(self) -> None:
        """Export data to..."""
        ...
