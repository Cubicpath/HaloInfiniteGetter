###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module for the main application classes."""

__all__ = (
    'app',
    'GetterApp',
    'Theme',
)

from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ..events import *
from ..lang import Translator
from ..models import DeferredCallable
from ..tomlfile import *


def app() -> 'GetterApp':
    """:return: GetterApp.instance()"""
    return GetterApp.instance()


class Theme:
    """Object containing data about a Theme."""
    __slots__ = ('id', 'style', 'display_name')

    def __init__(self, id: str, style: str = '', display_name: str | None = None) -> None:
        """Create a new Theme using a unique ID, the style data (.qss file content), and an optional display name.

        :param id: Uniquely identifying string, must be a valid TOML Table name.
        :param style: String read from a .qss file to use as a stylesheet.
        :param display_name: Optional display name to represent the theme, as opposed to the id.
        """
        self.id:           str = id
        self.style:        str = style
        self.display_name: str = display_name if display_name is not None else self.id


# TODO: Add logging functionality
class GetterApp(QApplication):
    """The main HaloInfiniteGetter PySide application that runs in the background and manages the process.

    :py:class:`GetterApp` is a singleton and can be accessed via the class using GetterApp.instance()
    """
    _legacy_style: str = None

    # PyCharm detects dict literals in __init__ as a dict[str, EventBus], for no explicable reason.
    # noinspection PyTypeChecker
    def __init__(self, argv: Sequence[str], settings: TomlFile, first_launch: bool = False) -> None:
        """Create a new app with the given arguments and settings."""
        super().__init__(argv)
        self.first_launch:    bool = first_launch
        self.translator:      Translator = Translator(settings['language'])
        self.settings:        TomlFile = settings
        self.themes:          dict[str, Theme] = {}
        self.theme_index_map: dict[str, int] = {}

        EventBus['settings'] = self.settings.event_bus
        EventBus['settings'].subscribe(DeferredCallable(self.load_themes), TomlEvents.Import)
        EventBus['settings'].subscribe(DeferredCallable(self.update_language), TomlEvents.Import)
        EventBus['settings'].subscribe(DeferredCallable(self.update_stylesheet), TomlEvents.Set, event_predicate=lambda e: e.key == 'gui/themes/selected')

    @classmethod
    def instance(cls) -> 'GetterApp':
        """Return the singleton instance of :py:class:`GetterApp`."""
        o: GetterApp | None = super().instance()
        if o is None:
            raise RuntimeError(f'Called {cls.__name__}.instance() when {cls.__name__} is not instantiated.')
        return o

    def update_language(self) -> None:
        """Set the application language to the one currently selected in settings."""
        self.translator = Translator(self.settings['language'])
        # TODO: Update all text in application to new language data

    def update_stylesheet(self) -> None:
        """Set the application stylesheet to the one currently selected in settings."""
        self.setStyleSheet(self.themes[self.settings['gui/themes/selected']].style)

    def load_themes(self) -> None:
        """Load all theme locations from settings and store them in self.themes.

        Also set current theme from settings.
        """
        if self._legacy_style is None:
            self.__class__._legacy_style = self.styleSheet()
        self.themes['legacy'] = Theme('legacy', self._legacy_style, 'Legacy (Default Qt)')

        for id_, theme in self.settings['gui/themes'].items():
            if not isinstance(theme, dict):
                continue

            theme: dict = theme.copy()
            path = theme.pop('path')
            if isinstance(path, CommentValue):
                path = Path(path.val)
            if path.is_dir():
                QDir.addSearchPath(path.name, str(path))

                file = QFile(f'{path.name}:stylesheet.qss')
                file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
                theme['id'] = id_
                theme['style'] = QTextStream(file).readAll()
                self.themes[id_] = Theme(**theme)
                file.close()

        # noinspection PyUnresolvedReferences
        self.theme_index_map = {theme_id: i for i, theme_id in enumerate(theme.id for theme in self.sorted_themes())}
        self.update_stylesheet()

    def sorted_themes(self) -> list[Theme]:
        """List of themes sorted by their display name."""
        # noinspection PyTypeChecker
        return sorted(self.themes.values(), key=lambda theme: theme.display_name)
