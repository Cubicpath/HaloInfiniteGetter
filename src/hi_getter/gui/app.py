###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module for the main application classes."""

__all__ = (
    'app',
    'GetterApp',
    'Theme',
)

import json
import sys
from collections.abc import Callable
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..constants import *
from ..events import *
from ..lang import Translator
from ..models import DeferredCallable
from ..models import DistributedCallable
from ..network import *
from ..tomlfile import *
from ..utils import has_package
from .utils import icon_from_bytes
from .utils import set_or_swap_icon


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

        app().themes[self.id] = self


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
        self._legacy_style: str = self.styleSheet()  # Set legacy style before it is overridden
        self._registered_translations: DistributedCallable[set[Callable[DeferredCallable[str]]]] = DistributedCallable(set())

        self.client:          Client = Client(self)
        self.icon_store:      dict[str, QIcon] = {}
        self.session:         NetworkSession = NetworkSession(self)
        self.settings:        TomlFile = settings
        self.themes:          dict[str, Theme] = {}
        self.theme_index_map: dict[str, int] = {}
        self.translator:      Translator = Translator(settings['language'])

        # Register callables to events
        EventBus['settings'] = self.settings.event_bus
        EventBus['settings'].subscribe(DeferredCallable(self.load_themes), TomlEvents.Import)
        EventBus['settings'].subscribe(DeferredCallable(self.update_language), TomlEvents.Import)
        EventBus['settings'].subscribe(DeferredCallable(self.update_stylesheet), TomlEvents.Set, event_predicate=lambda e: e.key == 'gui/themes/selected')

        # Load resources from disk
        self.load_icons()
        self.load_themes()

        # Set the default icon for all windows.
        self.setWindowIcon(self.icon_store['hi'])

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

    def _translate_http_code_map(self) -> None:
        """Translate the HTTP code map to the current language."""
        for code in (400, 401, 403, 404, 405, 406):
            http_code_map[code] = (http_code_map[code][0], self.translator(f'network.http.codes.{code}.description'))

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

    def update_language(self) -> None:
        """Set the application language to the one currently selected in settings.

        This method dynamically translates all registered text in the GUI to the given language using translation keys.
        """
        self.translator.language = self.settings['language']
        self._translate_http_code_map()
        self._registered_translations()

    def update_stylesheet(self) -> None:
        """Set the application stylesheet to the one currently selected in settings."""
        self.setStyleSheet(self.themes[self.settings['gui/themes/selected']].style)

    def show_dialog(self, key: str, parent: QWidget | None = None,
                    buttons: QMessageBox.StandardButtons | None = None,
                    default_button: QMessageBox.StandardButton | None = None,
                    title_args: Sequence | None = None,
                    description_args: Sequence | None = None) -> QMessageBox.StandardButton:
        """Show a dialog. This is a wrapper around QMessageBox creation.

        The type of dialog depends on the key's first section.
        The following sections are supported::
            - 'questions'   -> QMessageBox.question
            - 'information' -> QMessageBox.information
            - 'warnings'    -> QMessageBox.warning
            - 'errors'      -> QMessageBox.critical

        The dialog title and description are determined from the "title" and "description" child sections of the given key.
        Example with given key as "questions.key"::
            "questions.key.title": "Question Title"
            "questions.key.description": "Question Description"

        :param key: The translation key to use for the dialog.
        :param parent: The parent widget to use for the dialog. If not supplied, a dummy widget is temporarily created.
        :param buttons: The buttons to use for the dialog. If not supplied, the default buttons are used.
        :param default_button: The default button to use for the dialog. If not supplied, the default button is used.
        :param description_args: The translation arguments used to format the description.
        :param title_args: The translation arguments used to format the title.
        :return: The button that was clicked.
        """
        dummy_widget = QWidget()
        parent = dummy_widget if parent is None else parent
        title_args:       Sequence = () if title_args is None else title_args
        description_args: Sequence = () if description_args is None else description_args

        factory: Callable[[QWidget | QWidget, str, str, QMessageBox.StandardButtons | None, QMessageBox.StandardButton | None], QMessageBox.StandardButton]
        match key.split('.')[0]:
            case 'questions':
                factory = QMessageBox.question
            case 'information':
                factory = QMessageBox.information
            case 'warnings':
                factory = QMessageBox.warning
            case 'errors':
                factory = QMessageBox.critical
            case _:
                factory = QMessageBox.information

        title_text:       str = self.translator(f'{key}.title', *title_args)
        description_text: str = self.translator(f'{key}.description', *description_args)
        button_args:      list = []
        if buttons is not None:
            button_args.append(buttons)
        if default_button is not None:
            button_args.append(default_button)

        return_val = factory(
            parent, title_text, description_text, *button_args
        )
        dummy_widget.deleteLater()
        return return_val

    def load_env(self, verbose: bool = True) -> None:
        """Load environment variables from .env file."""
        if not has_package('python-dotenv'):
            self.show_dialog(
                'errors.missing_package',
                description_args=('python-dotenv', Path(sys.executable))
            )
        else:
            from dotenv import load_dotenv
            load_dotenv(verbose=verbose)

    def load_icons(self) -> None:
        """Load all icons needed for the application.

        Fetch locally stored icons from the HI_RESOURCE_PATH/icons directory

        Asynchronously fetch externally stored icons from urls defined in HI_RESOURCE_PATH/external_icons.json
        """
        # Load locally stored icons
        self.icon_store.update({
            filename.with_suffix('').name: QIcon(str(filename)) for
            filename in (HI_RESOURCE_PATH / 'icons').iterdir() if filename.is_file()
        })

        # Load external icon links
        external_icon_links: dict[str, str] = json.loads((HI_RESOURCE_PATH / 'external_icons.json').read_text(encoding='utf8'))

        # Load externally stored icons
        # pylint: disable=cell-var-from-loop
        for key, url in external_icon_links.items():
            # Create a new handler for every key being requested.
            def handle_reply(reply):
                icon = icon_from_bytes(reply.readAll())
                set_or_swap_icon(self.icon_store, key, icon)
                reply.deleteLater()

            app().session.get(url, finished=handle_reply)

    def load_themes(self) -> None:
        """Load all theme locations from settings and store them in self.themes.

        Also set current theme from settings.
        """
        Theme('legacy', self._legacy_style, 'Legacy (Default Qt)')

        for id_, theme in self.settings['gui/themes'].items():
            if not isinstance(theme, dict):
                continue

            theme: dict = theme.copy()
            if isinstance((path := theme.pop('path')), CommentValue):
                path = Path(path.val)
            if path.is_dir():
                search_path = f'hi_theme+{id_}'

                QDir.addSearchPath(search_path, str(path))
                file = QFile(f'{search_path}:stylesheet.qss')
                file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
                theme['id'] = id_
                theme['style'] = QTextStream(file).readAll()

                Theme(**theme)
                file.close()

        # noinspection PyUnresolvedReferences
        self.theme_index_map = {theme_id: i for i, theme_id in enumerate(theme.id for theme in self.sorted_themes())}
        self.update_stylesheet()

    def sorted_themes(self) -> list[Theme]:
        """List of themes sorted by their display name."""
        # noinspection PyTypeChecker
        return sorted(self.themes.values(), key=lambda theme: theme.display_name)

    @staticmethod
    def quit() -> None:
        """Quit the application."""
        app().client.deleteLater()
        app().quit()
