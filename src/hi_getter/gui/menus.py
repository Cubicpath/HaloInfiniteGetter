###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing :py:class:`QMenu` Context Menus."""
import sys
import webbrowser
from pathlib import Path
from platform import platform
from shutil import rmtree

import requests
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .._version import __version_info__ as ver
from ..constants import *
from ..utils import current_requirement_versions
from .widgets import LicenseViewer

__all__ = (
    'FileContextMenu',
    'HelpContextMenu',
    'ToolsContextMenu',
)

_PARENT_PACKAGE: str = __package__.split('.', maxsplit=1)[0]


# noinspection PyArgumentList
class FileContextMenu(QMenu):
    """Context menu that shows actions to manipulate files."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`FileContextMenu`."""
        super().__init__(parent)

        open_in:     QAction = QAction(QIcon(str(RESOURCE_PATH / 'icons/folder.ico')), 'Open In Explorer', self, triggered=self.open_explorer)
        flush_cache: QAction = QAction(QIcon(str(RESOURCE_PATH / 'icons/folder.ico')), 'Flush Cache', self, triggered=self.flush_cache)
        import_from: QAction = QAction(QIcon(str(RESOURCE_PATH / 'icons/import.ico')), 'Import Data from...', self, triggered=self.import_data)
        export_to:   QAction = QAction(QIcon(str(RESOURCE_PATH / 'icons/export.ico')), 'Export Data to...', self, triggered=self.export_data)
        section_map = {
            'Files': (open_in, flush_cache, import_from, export_to)
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

        flush_cache.setDisabled(not tuple(CACHE_PATH.iterdir()))  # Set disabled if CACHE_PATH directory is empty

        # TODO: Add functionality and enable
        import_from.setDisabled(True)
        export_to.setDisabled(True)

    @staticmethod
    def open_explorer() -> None:
        """Open the user's file explorer in the current application's export directory."""
        webbrowser.open(f'file:///{CACHE_PATH}')

    def flush_cache(self) -> None:
        """Remove all data from cache."""
        response: int = QMessageBox.warning(
            self, 'Confirm Cache Deletion',
            'Are you sure you want to delete the contents of the cache? This action cannot be undone.',
            QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel
        )

        if response == QMessageBox.StandardButton.Ok:
            rmtree(CACHE_PATH)
            CACHE_PATH.mkdir()

    def import_data(self) -> None:
        """Import data from..."""
        ...

    def export_data(self) -> None:
        """Export data to..."""
        ...


# noinspection PyArgumentList
class HelpContextMenu(QMenu):
    """Context menu that shows actions to help the user."""
    _about: tuple[str, str] | None = None
    _github_icon: bytes = requests.get('https://github.githubassets.com/favicons/favicon.png').content

    def __init__(self, parent) -> None:
        """Create a new :py:class:`HelpContextMenu`."""
        super().__init__(parent)

        self.license_window = LicenseViewer()

        github_pixmap = QPixmap()
        github_pixmap.loadFromData(self._github_icon)

        github_view:  QAction = QAction(QIcon(github_pixmap), 'View on GitHub', self, triggered=self.open_github)
        create_issue: QAction = QAction(QIcon(github_pixmap), 'Create an issue', self, triggered=self.open_issues)
        license_view: QAction = QAction(QIcon(str(RESOURCE_PATH / 'icons/copyright.ico')), 'License', self, triggered=self.open_license)
        about_view:   QAction = QAction(QIcon(str(RESOURCE_PATH / 'icons/about.ico')), 'About', self, triggered=self.open_about)
        section_map = {
            'Github': (github_view, create_issue),
            'Information': (license_view, about_view)
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

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
            package_versions = '\n'.join(f'Using package {package}: {version}' for
                                         package, version in current_requirement_versions(_PARENT_PACKAGE).items())

            self.__class__._about = ('About', f'''
HaloInfiniteGetter by Cubicpath. A simple way to get live Halo data straight from Halo Waypoint.

Version Info: major:{ver[0]}, minor:{ver[1]}, micro:{ver[2]}, releaselevel:{ver[3]}, serial:{ver[4]}

Running on:
\t{platform()}
\t{sys.implementation.name} {sys.version.split('[', maxsplit=1)[0]}

{package_versions}

MIT Licence (C) 2022 Cubicpath@Github
''')
        return self._about


# noinspection PyArgumentList
class ToolsContextMenu(QMenu):
    """Context menu for tools."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`ToolsContextMenu`."""
        super().__init__(parent)

        desktop_icon = self.style().standardIcon(QStyle.SP_DesktopIcon)
        shortcut_tool: QAction = QAction(desktop_icon, 'Create Desktop Shortcut', self, triggered=self.create_shortcut)
        section_map = {
            'Tools': (shortcut_tool,)
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

    @staticmethod
    def create_shortcut():
        """Create shortcut for starting program."""
        from pyshortcuts import make_shortcut

        exec_path = Path(sys.executable)
        name = exec_path.with_suffix('').name
        if not name.endswith('w'):
            name += 'w'

        execute_path = f'{exec_path.with_name(f"{name}{exec_path.suffix}")} -m {_PARENT_PACKAGE}'
        make_shortcut(script=execute_path, name='HaloInfiniteGetter',
                      description='A simple way to get live Halo data straight from Halo Waypoint.',
                      icon=RESOURCE_PATH / 'icons/hi.ico', terminal=False, desktop=True, startmenu=True)
