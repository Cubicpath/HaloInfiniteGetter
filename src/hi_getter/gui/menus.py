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

from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .._version import __version_info__ as ver
from ..constants import *
from ..models import DeferredCallable
from ..utils import current_requirement_versions
from ..utils import has_package
from .app import app
from .utils import PARENT_PACKAGE
from .widgets import *


# noinspection PyArgumentList
class FileContextMenu(QMenu):
    """Context menu that shows actions to manipulate files."""

    def __init__(self, parent) -> None:
        """Create a new :py:class:`FileContextMenu`."""
        super().__init__(parent)

        open_explorer: QAction = QAction(
            app().icon_store['folder'],
            app().translator('gui.menus.file.open'), self, triggered=DeferredCallable(
                webbrowser.open, f'file:///{HI_CACHE_PATH}'
            )
        )

        flush_cache: QAction = QAction(
            app().icon_store['folder'],
            app().translator('gui.menus.file.flush'), self, triggered=self.flush_cache
        )

        import_from: QAction = QAction(
            app().icon_store['import'],
            app().translator('gui.menus.file.import'), self, triggered=self.import_data
        )

        export_to: QAction = QAction(
            app().icon_store['export'],
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
        response = app().show_dialog(
            'warnings.delete_cache', self,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
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

    def __init__(self, parent) -> None:
        """Create a new :py:class:`HelpContextMenu`."""
        super().__init__(parent)

        # Make sure when instantiating QObjects that those QObjects reference a Python object that re-references that QObject,
        # otherwise the QObject will not be considered "in use" by the garbage collector, and will be deleted.
        self.license_window = LicenseViewer()
        self.readme_window = ReadmeViewer()

        github_view: QAction = QAction(
            app().icon_store['github'],
            app().translator('gui.menus.help.github'), self, triggered=DeferredCallable(
                webbrowser.open, 'https://github.com/Cubicpath/HaloInfiniteGetter/', new=2, autoraise=True
            )
        )

        create_issue: QAction = QAction(
            app().icon_store['github'],
            app().translator('gui.menus.help.issue'), self, triggered=DeferredCallable(
                webbrowser.open, 'https://github.com/Cubicpath/HaloInfiniteGetter/issues/new/choose', new=2, autoraise=True
            )
        )

        about_view: QAction = QAction(
            app().icon_store['about'],
            app().translator('gui.menus.help.about'), self, triggered=self.open_about
        )

        license_view: QAction = QAction(
            app().icon_store['copyright'],
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

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

    # pylint: disable=not-an-iterable
    def open_about(self) -> None:
        """Open the application's about section."""
        self.setWindowIcon(app().icon_store['about'])
        app().show_dialog(
            'information.about', self,
            description_args=(
                *ver, platform(), sys.implementation.name,
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
            app().translator(
                'information.about.package_version',
                package, version
            ) for package, version in current_requirement_versions(PARENT_PACKAGE).items() if has_package(package)
        )


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

        exception_reporter: QAction = QAction(
            parent.exception_reporter.logger.icon(),
            app().translator('gui.menus.tools.exception_reporter'), self, triggered=parent.exception_reporter.show
        )

        section_map = {
            'Tools': (shortcut_tool, exception_reporter)
        }

        for section, actions in section_map.items():
            self.addSection(section)
            self.addActions(actions)

    def create_shortcut(self) -> None:
        """Create shortcut for starting program."""
        exec_path = Path(sys.executable)

        if not has_package('pyshortcuts'):
            app().show_dialog(
                'errors.missing_package', self,
                description_args=('pyshortcuts', exec_path)
            )
        else:
            from pyshortcuts import make_shortcut

            name = exec_path.with_suffix('').name
            if not name.endswith('w'):
                name += 'w'
            shortcut_path = f'{exec_path.with_name(f"{name}{exec_path.suffix}")} -m {PARENT_PACKAGE}'

            with redirect_stdout(open(os.devnull, 'w', encoding='utf8')):
                make_shortcut(script=shortcut_path, name=app().translator('app.name'),
                              description=app().translator('app.description'),
                              icon=HI_RESOURCE_PATH / 'icons/hi.ico', terminal=False, desktop=True, startmenu=True)
