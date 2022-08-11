###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module for the main application classes."""
from __future__ import annotations

__all__ = (
    'app',
    'GetterApp',
    'Theme',
    'tr',
)

import json
import subprocess
import sys
from collections.abc import Callable
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from typing import NamedTuple

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
from ..utils.gui import icon_from_bytes
from ..utils.gui import set_or_swap_icon
from ..utils.package import has_package
from ..utils.network import http_code_map


def app() -> GetterApp:
    """:return: GetterApp.instance()"""
    return GetterApp.instance()


def tr(key: str, *args: Any, **kwargs: Any) -> str:
    """Alias for app().translator().

    :param key: Translation keys to translate.
    :param args: Arguments to format key with.
    :keyword default: Default value to return if key is not found.
    :return: Translated text.
    """
    return app().translator(key, *args, **kwargs)


class _DialogResponse(NamedTuple):
    """Response object for GetterApp.show_dialog()."""
    button: QAbstractButton = QMessageBox.NoButton
    role:   QMessageBox.ButtonRole = QMessageBox.NoRole


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

        # TODO: cache platform() call early on separate thread

        # Register callables to events
        EventBus['settings'] = self.settings.event_bus
        EventBus['settings'].subscribe(DeferredCallable(self.load_themes), TomlEvents.Import)
        EventBus['settings'].subscribe(DeferredCallable(self.update_language), TomlEvents.Import)
        EventBus['settings'].subscribe(DeferredCallable(self.update_stylesheet), TomlEvents.Set, event_predicate=lambda e: e.key == 'gui/themes/selected')

        # Load resources from disk
        self.load_themes()
        self.load_icons()

        # Set the default icon for all windows.
        self.setWindowIcon(self.icon_store['hi'])

    @classmethod
    def instance(cls) -> GetterApp:
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
        try:
            self.setStyleSheet(self.themes[self.settings['gui/themes/selected']].style)
        except KeyError:
            self.settings['gui/themes/selected'] = 'legacy'
            self.setStyleSheet(self._legacy_style)

    def show_dialog(self, key: str, parent: QWidget | None = None,
                    buttons: Sequence[tuple[QAbstractButton, QMessageBox.ButtonRole] | QMessageBox.StandardButton] | QMessageBox.StandardButtons | None = None,
                    default_button: QAbstractButton | QMessageBox.StandardButton | None = None,
                    title_args: Sequence | None = None,
                    description_args: Sequence | None = None) -> _DialogResponse | None:
        """Show a dialog. This is a wrapper around QMessageBox creation.

        The type of dialog icon depends on the key's first section.
        The following sections are supported::
            - 'about':      -> QMessageBox.about
            - 'questions'   -> QMessageBox.Question
            - 'information' -> QMessageBox.Information
            - 'warnings'    -> QMessageBox.Warning
            - 'errors'      -> QMessageBox.Critical

        The dialog title and description are determined from the "title" and "description" child sections of the given key.
        Example with given key as "questions.key"::
            "questions.key.title": "Question Title"
            "questions.key.description": "Question Description"

        WARNING: If a StandardButton is clicked, the button returned is NOT a StandardButton enum, but a QPushButton.

        :param key: The translation key to use for the dialog.
        :param parent: The parent widget to use for the dialog. If not supplied, a dummy widget is temporarily created.
        :param buttons: The buttons to use for the dialog. If button is not a StandardButton, it should be a tuple containing the button and its role.
        :param default_button: The default button to use for the dialog.
        :param description_args: The translation arguments used to format the description.
        :param title_args: The translation arguments used to format the title.
        :return: The button that was clicked, as well as its role. None if the key's first section is "about".
        """
        if parent is None:
            dummy_widget = QWidget()
            parent = dummy_widget

        title_args:       Sequence = () if title_args is None else title_args
        description_args: Sequence = () if description_args is None else description_args

        icon: QMessageBox.Icon
        first_section: str = key.split('.')[0]
        match first_section:
            case 'questions':
                icon = QMessageBox.Question
            case 'information':
                icon = QMessageBox.Information
            case 'warnings':
                icon = QMessageBox.Warning
            case 'errors':
                icon = QMessageBox.Critical
            case _:
                icon = QMessageBox.NoIcon

        title_text:       str = self.translator(f'{key}.title', *title_args)
        description_text: str = self.translator(f'{key}.description', *description_args)

        msg_box = QMessageBox(icon, title_text, description_text, parent=parent)

        if first_section == 'about':
            return msg_box.about(parent, title_text, description_text)

        standard_buttons = None
        if buttons is not None:
            if isinstance(buttons, Sequence):
                for button in buttons:
                    if isinstance(button, tuple):
                        msg_box.addButton(*button)
                    else:
                        # If the button is not a tuple, assume it's a QMessageBox.StandardButton.
                        # Build a StandardButtons from all StandardButton objects in buttons.
                        if standard_buttons is None:
                            standard_buttons = button
                        else:
                            standard_buttons |= button
            else:
                # If the buttons is not a sequence, assume it's QMessageBox.StandardButtons.
                standard_buttons = buttons

        if standard_buttons:
            msg_box.setStandardButtons(standard_buttons)

        if default_button is not None:
            msg_box.setDefaultButton(default_button)

        msg_box.buttonClicked.connect((result := set()).add)
        msg_box.exec()

        result_button: QAbstractButton = next(iter(result)) if result else QMessageBox.NoButton
        result_role:   QMessageBox.ButtonRole = msg_box.buttonRole(result_button) if result else QMessageBox.NoRole

        if parent is None:
            # noinspection PyUnboundLocalVariable
            dummy_widget.deleteLater()

        return _DialogResponse(button=result_button, role=result_role)

    def missing_package_dialog(self, package: str, reason: str | None = None, parent: QObject | None = None) -> None:
        """Show a dialog informing the user that a package is missing and asks to install said package.

        If a user presses the "Install" button, the package is installed.

        :param package: The name of the package that is missing.
        :param reason: The reason why the package is attempting to be used.
        :param parent: The parent widget to use for the dialog. If not supplied, a dummy widget is temporarily created.
        """
        exec_path = Path(sys.executable)

        install_button = QPushButton(self.get_theme_icon('dialog_ok'), self.translator('errors.missing_package.install'))

        consent_to_install: bool = self.show_dialog(
            'errors.missing_package', parent,
            [(install_button, QMessageBox.AcceptRole), QMessageBox.Cancel],
            QMessageBox.Cancel,
            description_args=(package, reason, exec_path)
        ).role == QMessageBox.AcceptRole

        if consent_to_install:
            try:
                # Install the package
                subprocess.run([exec_path, '-m', 'pip', 'install', package], check=True)
            except (OSError, subprocess.SubprocessError) as e:
                self.show_dialog(
                    'errors.package_install_failure', parent,
                    description_args=(package, e)
                )
            else:
                self.show_dialog(
                    'information.package_installed', parent,
                    description_args=(package, reason)
                )

    def load_env(self, verbose: bool = True) -> None:
        """Load environment variables from .env file."""
        if not has_package('python-dotenv'):
            self.missing_package_dialog('python-dotenv', 'Loading environment variables')
        if has_package('python-dotenv'):  # Not the same as else, during the dialog, the package may be dynamically installed by user.
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

    def get_theme_icon(self, icon: str) -> QIcon | None:
        """Return the icon for the given theme.

        :param icon: Icon name for given theme.
        :return: QIcon for the given theme or default value or None if icon not found.
        """
        current_theme = self.settings['gui/themes/selected']
        if (icon_key := f'hi_theme+{current_theme}+{icon}') in self.icon_store:
            return self.icon_store[icon_key]

    def load_themes(self) -> None:
        """Load all theme locations from settings and store them in self.themes.

        Also set current theme from settings.
        """
        Theme('legacy', self._legacy_style, 'Legacy (Default Qt)')

        try:
            themes = self.settings['gui/themes']
        except KeyError:
            self.settings['gui/themes'] = themes = {}

        for id, theme in themes.items():
            if not isinstance(theme, dict):
                continue

            theme: dict = theme.copy()
            if isinstance((path := theme.pop('path')), CommentValue):
                path = path.val

            # Translate builtin theme locations
            if isinstance(path, str) and path.startswith('builtin::'):
                path = HI_RESOURCE_PATH / f'themes/{path.removeprefix("builtin::")}'

            # Ensure path is a Path value that exists
            if (path := Path(path)).is_dir():
                search_path = f'hi_theme+{id}'
                QDir.addSearchPath(search_path, str(path))

                for theme_resource in path.iterdir():
                    if theme_resource.is_file():
                        if theme_resource.name == 'stylesheet.qss':
                            theme['id'] = id
                            theme['style'] = theme_resource.read_text(encoding='utf8')
                        elif theme_resource.suffix.lstrip('.') in SUPPORTED_IMAGE_EXTENSIONS:
                            # Load all images in the theme directory into the icon store.
                            self.icon_store[f'hi_theme+{id}+{theme_resource.with_suffix("").name}'] = QIcon(str(theme_resource.resolve()))

                Theme(**theme)

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
        QApplication.quit()
