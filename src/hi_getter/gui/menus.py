###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing :py:class:`QMenu` Context Menus."""

__all__ = (
    'FileContextMenu',
    'HelpContextMenu',
    'ToolsContextMenu',
)

import os
import sys
import webbrowser
from contextlib import redirect_stdout
from pathlib import Path
from platform import platform
from shutil import rmtree

import requests
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .._version import __version_info__ as ver
from ..constants import *
from ..models import DeferredCallable
from ..utils import current_requirement_versions
from ..utils import has_package
from .app import app
from .widgets import *

_PARENT_PACKAGE: str = __package__.split('.', maxsplit=1)[0]


# noinspection PyArgumentList
class FileContextMenu(QMenu):
    """Context menu that shows actions to manipulate files."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`FileContextMenu`."""
        super().__init__(parent)

        open_explorer:     QAction = QAction(
            QIcon(str(HI_RESOURCE_PATH / 'icons/folder.ico')),
            app().translator('gui.menus.file.open'), self, triggered=DeferredCallable(
                webbrowser.open, f'file:///{HI_CACHE_PATH}'
            )
        )

        flush_cache: QAction = QAction(
            QIcon(str(HI_RESOURCE_PATH / 'icons/folder.ico')),
            app().translator('gui.menus.file.flush'), self, triggered=self.flush_cache
        )

        import_from: QAction = QAction(
            QIcon(str(HI_RESOURCE_PATH / 'icons/import.ico')),
            app().translator('gui.menus.file.import'), self, triggered=self.import_data
        )

        export_to:   QAction = QAction(
            QIcon(str(HI_RESOURCE_PATH / 'icons/export.ico')),
            app().translator('gui.menus.file.export'), self, triggered=self.export_data
        )

        section_map = {
            'Files': (open_explorer, flush_cache, import_from, export_to)
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

        flush_cache.setDisabled(not tuple(HI_CACHE_PATH.iterdir()))  # Set disabled if HI_CACHE_PATH directory is empty

        # TODO: Add functionality and enable
        import_from.setDisabled(True)
        export_to.setDisabled(True)

    def flush_cache(self) -> None:
        """Remove all data from cache."""
        response: int = QMessageBox.warning(
            self, app().translator('warnings.delete_cache.title'),
            app().translator('warnings.delete_cache.description'),
            QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel, defaultButton=QMessageBox.StandardButton.Cancel
        )

        if response == QMessageBox.StandardButton.Ok:
            rmtree(HI_CACHE_PATH)
            HI_CACHE_PATH.mkdir()

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

        # Make sure when instantiating QObjects that those QObjects reference a Python object that re-references that QObject,
        # otherwise the QObject will not be considered "in use" by the garbage collector, and will be deleted.
        self.license_window = LicenseViewer()
        self.readme_window = ReadmeViewer()

        github_pixmap = QPixmap()
        github_pixmap.loadFromData(self._github_icon)

        github_view:  QAction = QAction(
            QIcon(github_pixmap),
            app().translator('gui.menus.help.github'), self, triggered=DeferredCallable(
                webbrowser.open, 'https://github.com/Cubicpath/HaloInfiniteGetter/', new=2, autoraise=True
            )
        )

        create_issue: QAction = QAction(
            QIcon(github_pixmap),
            app().translator('gui.menus.help.issue'), self, triggered=DeferredCallable(
                webbrowser.open, 'https://github.com/Cubicpath/HaloInfiniteGetter/issues/new/choose', new=2, autoraise=True
            )
        )

        about_view:   QAction = QAction(
            QIcon(str(HI_RESOURCE_PATH / 'icons/about.ico')),
            app().translator('gui.menus.help.about'), self, triggered=self.open_about
        )

        license_view: QAction = QAction(
            QIcon(str(HI_RESOURCE_PATH / 'icons/copyright.ico')),
            app().translator('gui.menus.help.license'), self, triggered=self.license_window.show
        )

        readme: QAction = QAction(
            self.style().standardIcon(QStyle.SP_DialogApplyButton),
            app().translator('gui.menus.help.readme'), self, triggered=self.readme_window.show
        )

        section_map = {
            'Github': (github_view, create_issue),
            'Information': (about_view, license_view, readme)
        }

        # print({k: v for k, v in locals().items() if isinstance(v, QObject)})

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

    # pylint: disable=not-an-iterable
    def open_about(self) -> None:
        """Open the application's about section."""
        self.setWindowIcon(QIcon(str(HI_RESOURCE_PATH / 'icons/about.ico')))
        QMessageBox.information(self, *self.about_message())

    def about_message(self) -> tuple[str, str]:
        """Generate the 'About' information regarding the application's environment.
        Since this takes a while the first time, the result is cached as a class value.

        :return: Tuple containing the title and the message
        """
        if self._about is None:
            package_versions = '\n'.join(
                f'Using package {package}: {version}' for package, version in current_requirement_versions(_PARENT_PACKAGE).items() if has_package(package)
            )

            self.__class__._about = (
                app().translator('information.about.title'),
                app().translator(
                    'information.about.description',
                    *ver, platform(), sys.implementation.name,
                    sys.version.split('[', maxsplit=1)[0],
                    package_versions
                )
            )
        return self._about


# noinspection PyArgumentList
class ToolsContextMenu(QMenu):
    """Context menu for tools."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`ToolsContextMenu`."""
        super().__init__(parent)

        shortcut_tool: QAction = QAction(
            self.style().standardIcon(QStyle.SP_DesktopIcon),
            app().translator('gui.menus.tools.desktop_shortcut'), self, triggered=self.create_shortcut
        )

        section_map = {
            'Tools': (shortcut_tool,)
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

    def create_shortcut(self) -> None:
        """Create shortcut for starting program."""
        exec_path = Path(sys.executable)

        if not has_package('pyshortcuts'):
            QMessageBox.critical(
                self, app().translator('errors.missing_package.title'),
                app().translator('errors.missing_package.description', 'pyshortcuts', exec_path)
            )
        else:
            from pyshortcuts import make_shortcut

            name = exec_path.with_suffix('').name
            if not name.endswith('w'):
                name += 'w'
            shortcut_path = f'{exec_path.with_name(f"{name}{exec_path.suffix}")} -m {_PARENT_PACKAGE}'

            with redirect_stdout(open(os.devnull, 'w', encoding='utf8')):
                make_shortcut(script=shortcut_path, name=app().translator('app.name'),
                              description=app().translator('app.description'),
                              icon=HI_RESOURCE_PATH / 'icons/hi.ico', terminal=False, desktop=True, startmenu=True)
