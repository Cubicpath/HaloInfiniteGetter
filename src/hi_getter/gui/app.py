###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module for the main application classes."""

__all__ = (
    'app',
    'GetterApp',
    'Theme',
)

from collections.abc import Callable
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ..events import *
from ..lang import Translator
from ..models import DeferredCallable
from ..models import DistributedCallable
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

    :py:class:`GetterApp` is a singleton and can be accessed via the class using the GetterApp.instance() method or the app() function.
    """

    # PyCharm detects dict literals in __init__ as a dict[str, EventBus], for no explicable reason.
    # noinspection PyTypeChecker
    def __init__(self, argv: Sequence[str], settings: TomlFile, first_launch: bool = False) -> None:
        """Create a new app with the given arguments and settings."""
        super().__init__(argv)
        self._first_launch: bool = first_launch
        self._legacy_style: str = self.styleSheet()
        self._registered_translations: DistributedCallable[set[Callable[DeferredCallable[str]]]] = DistributedCallable(set())

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

    @property
    def first_launch(self) -> bool:
        """Return whether this is the first launch of the application.

        This is determined by checking if the .LAUNCHED file exists in the user's config folder.
        """
        return self._first_launch

    def init_translations(self, translation_calls: dict[Callable, str]) -> None:
        """Initialize the translation of all objects.

        Register functions to call with their respective translation keys.
        This is used to translate everything in the GUI.
        """

        for func, key in translation_calls.items():
            # Call the function with the deferred translation of the given key.
            translate = DeferredCallable(func, DeferredCallable(self.translator, key))

            # Register the object for dynamic translation
            self._registered_translations.callables.add(translate)
            translate()

    # noinspection PyUnresolvedReferences, PyProtectedMember
    def update_language(self) -> None:
        """Set the application language to the one currently selected in settings.

        This method dynamically translates all registered text in the GUI to the given language using translation keys.
        """
        self.translator.language = self.settings['language']
        self._registered_translations()

    def update_stylesheet(self) -> None:
        """Set the application stylesheet to the one currently selected in settings."""
        self.setStyleSheet(self.themes[self.settings['gui/themes/selected']].style)

    def load_themes(self) -> None:
        """Load all theme locations from settings and store them in self.themes.

        Also set current theme from settings.
        """
        self.themes['legacy'] = Theme('legacy', self._legacy_style, 'Legacy (Default Qt)')

        for id_, theme in self.settings['gui/themes'].items():
            if not isinstance(theme, dict):
                continue

            theme: dict = theme.copy()
            path: CommentValue | Path = theme.pop('path')
            if isinstance(path, CommentValue):
                path = Path(path.val)
            if path.is_dir():
                search_path = f'hi_theme_{id_}'

                QDir.addSearchPath(search_path, str(path))
                file = QFile(f'{search_path}:stylesheet.qss')
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
