###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
from importlib import metadata
import sys
import webbrowser
from pathlib import Path
from platform import platform

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
    _about = None
    _github_icon = None

    def __init__(self, parent) -> None:
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
        webbrowser.open('https://github.com/Cubicpath/HaloInfiniteGetter/', new=2, autoraise=True)

    @staticmethod
    def open_issues() -> None:
        webbrowser.open('https://github.com/Cubicpath/HaloInfiniteGetter/issues/new', new=2, autoraise=True)

    def open_license(self) -> None:
        self.license_window.show()

    def open_about(self) -> None:
        self.setWindowIcon(QIcon(str(RESOURCE_PATH / 'icons/about.ico')))
        QMessageBox.information(self, *self.about_message())

    def about_message(self) -> tuple[str, str]:
        if self._about is None:
            self.__class__._about = ('About', f'''
HaloInfiniteGetter by Cubicpath. A simple way to get live Halo data straight from Halo Waypoint.

Version Info: major:{ver[0]}, minor:{ver[1]}, micro:{ver[2]}, releaselevel:{ver[3]}, serial:{ver[4]}

Running on:
\t{platform()}
\t{sys.implementation.name} {sys.version.split("[")[0]}

Using requests: {metadata.version("requests")}
Using PyQT6: {metadata.version("PyQT6")}
Using python-dotenv: {metadata.version("python-dotenv")}

MIT Licence (C) 2022 Cubicpath@Github
''')
        return self._about


# noinspection PyArgumentList
class FileContextMenu(QMenu):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        open_in = QAction(QIcon(str(RESOURCE_PATH / 'icons/folder.ico')), 'Open In Explorer', self, triggered=self.open_explorer)
        import_from = QAction(QIcon(str(RESOURCE_PATH / 'icons/import.ico')), 'Import Data from...', self, triggered=self.import_data)
        export_to = QAction(QIcon(str(RESOURCE_PATH / 'icons/export.ico')), 'Export Data', self, triggered=self.export_data)
        self.addAction(open_in)
        self.addAction(import_from)
        self.addAction(export_to)

        # TOD#O: Add functionality and enable
        import_from.setDisabled(True)
        export_to.setDisabled(True)

    @staticmethod
    def open_explorer() -> None:
        webbrowser.open('file:///' + str(Path.cwd() / 'hi_data'))

    def import_data(self) -> None:
        ...

    def export_data(self) -> None:
        ...
