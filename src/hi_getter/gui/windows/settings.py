###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Settings window implementation."""
from __future__ import annotations

__all__ = (
    'SettingsWindow',
)

from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ...events import EventBus
from ...models import DeferredCallable
from ...models import Singleton
from ...tomlfile import TomlEvents
from ...utils.gui import init_layouts
from ...utils.gui import init_objects
from ..app import app
from ..app import tr
from ..widgets import PasteLineEdit
from ..widgets import TranslatableComboBox


# noinspection PyTypeChecker
class SettingsWindow(Singleton, QWidget):
    """Window that provides user interaction with the application's settings.

    :py:class:`SettingsWindow` is a singleton and can be accessed via the class using the SettingsWindow.instance() class method.
    """
    _singleton_base_type = QWidget
    _singleton_check_ref = False

    def __init__(self, size: QSize) -> None:
        """Create the settings window."""
        super().__init__()

        self.setWindowTitle(tr('gui.settings.title'))
        self.setWindowIcon(app().icon_store['settings'])
        self.resize(size)
        self.setFixedWidth(self.width())

        # Show an error dialog on import failure
        EventBus['settings'].subscribe(
            DeferredCallable(app().show_dialog, 'errors.settings.import_failure', self, description_args=(app().settings.path,)),
            TomlEvents.Fail, event_predicate=lambda event: event.failure == 'import'
        )

        self.theme_dropdown: QComboBox
        self.aspect_ratio_dropdown: QComboBox
        self.transformation_dropdown: QComboBox
        self.line_wrap_dropdown: QComboBox
        self.key_set_button: QPushButton
        self.key_field: QLineEdit
        self._init_ui()

    def _init_ui(self) -> None:

        def import_settings() -> None:
            """Import settings from a chosen TOML file."""
            file_path = Path(QFileDialog.getOpenFileName(self, caption=tr('gui.settings.import'),
                                                         dir=str(HI_CONFIG_PATH), filter='TOML Files (*.toml);;All files (*.*)')[0])
            if file_path.is_file():
                if app().settings.import_from(file_path):
                    save_button.setDisabled(False)

        def export_settings() -> None:
            """Export current settings to a chosen file location."""
            file_path = Path(QFileDialog.getSaveFileName(self, caption=tr('gui.settings.export'),
                                                         dir=str(HI_CONFIG_PATH), filter='TOML Files (*.toml);;All files (*.*)')[0])
            if str(file_path) != '.':
                app().settings.export_to(file_path)

        def hide_key() -> None:
            """Hide API key."""
            self.key_set_button.setDisabled(True)
            self.key_field.setDisabled(True)
            self.key_field.setText(app().client.hidden_key())
            self.key_field.setAlignment(Qt.AlignCenter)

        def toggle_key_visibility() -> None:
            """Toggle hiding and showing the API key."""
            if not self.key_field.isEnabled():
                self.key_field.setAlignment(Qt.AlignLeft)
                self.key_field.setText(app().client.wpauth)
                self.key_field.setDisabled(False)
                self.key_field.setFocus()
                self.key_set_button.setDisabled(False)
            else:
                hide_key()

        def set_key() -> None:
            """Set the client's auth_key to the current text in the key field."""
            text = self.key_field.text().strip()
            if text:
                app().client.wpauth = text
            else:
                del app().client.wpauth
            toggle_key_visibility()

        def clear_token() -> None:
            del app().client.token
            self.token_clear_button.setDisabled(True)

        # Define widget attributes
        # Cannot be defined in init_objects() as walrus operators are not allowed for object attribute assignment.
        # This works in the standard AST, but is a seemingly arbitrary limitation set by the interpreter.
        # See: https://stackoverflow.com/questions/64055314/why-cant-pythons-walrus-operator-be-used-to-set-instance-attributes#answer-66617839
        (
            self.key_set_button, self.token_clear_button,
            self.theme_dropdown, self.aspect_ratio_dropdown, self.transformation_dropdown, self.line_wrap_dropdown, self.icon_mode_dropdown,
            self.key_field
        ) = (
            QPushButton(self), QPushButton(self),
            TranslatableComboBox(self), TranslatableComboBox(self), TranslatableComboBox(self), TranslatableComboBox(self), TranslatableComboBox(self),
            PasteLineEdit(self)
        )

        init_objects({
            # Labels
            (theme_label := QLabel(self)): {
                'size': {'maximum': (85, None)}
            },
            (aspect_ratio_label := QLabel(self)): {
                'size': {'maximum': (90, None)}
            },
            (transformation_label := QLabel(self)): {
                'size': {'maximum': (90, None)}
            },
            (line_wrap_label := QLabel(self)): {
                'size': {'maximum': (90, None)}
            },
            (icon_mode_label := QLabel(self)): {
                'size': {'maximum': (90, None)}
            },

            # Buttons
            (save_button := QPushButton(self)): {
                'disabled': True,
                'size': {'maximum': (50, None)},
                'clicked': app().settings.save
            },
            (reload_button := QPushButton(self)): {
                'size': {'maximum': (60, None)},
                'clicked': app().settings.reload
            },
            (import_button := QPushButton(self)): {
                'clicked': import_settings
            },
            (export_button := QPushButton(self)): {
                'clicked': export_settings
            },
            (open_editor_button := QPushButton(self)): {
                'clicked': DeferredCallable(QDesktopServices.openUrl, lambda: QUrl(app().settings.path.as_uri()))
            },
            (key_show_button := QPushButton(self)): {
                'clicked': toggle_key_visibility
            },
            self.key_set_button: {
                'size': {'minimum': (40, None)},
                'clicked': set_key
            },
            self.token_clear_button: {
                'disabled': not app().client.token,
                'clicked': clear_token
            },

            # Line editors
            self.key_field: {
                'font': QFont('segoe ui', 8), 'text': app().client.hidden_key(),
                'pasted': set_key, 'returnPressed': self.key_set_button.click,
                'size': {'minimum': (220, None)}, 'alignment': Qt.AlignCenter
            },

            # Dropdowns
            self.theme_dropdown: {
                'activated': DeferredCallable(
                    app().settings.__setitem__,
                    'gui/themes/selected',
                    lambda: app().sorted_themes()[self.theme_dropdown.currentIndex()].id
                ),
                'items': (theme.display_name for theme in app().sorted_themes())
            },
            self.aspect_ratio_dropdown: {
                'activated': DeferredCallable(
                    app().settings.__setitem__,
                    'gui/media_output/aspect_ratio_mode',
                    self.aspect_ratio_dropdown.currentIndex
                ),
                'items': (
                    'gui.settings.media.aspect_ratio.ignore',
                    'gui.settings.media.aspect_ratio.keep',
                    'gui.settings.media.aspect_ratio.expanding'
                )
            },
            self.transformation_dropdown: {
                'activated': DeferredCallable(
                    app().settings.__setitem__,
                    'gui/media_output/transformation_mode',
                    self.transformation_dropdown.currentIndex
                ),
                'items': (
                    'gui.settings.media.image_transform.fast',
                    'gui.settings.media.image_transform.smooth'
                )
            },
            self.line_wrap_dropdown: {
                'activated': DeferredCallable(
                    app().settings.__setitem__,
                    'gui/text_output/line_wrap_mode',
                    self.line_wrap_dropdown.currentIndex
                ),
                'items': (
                    'gui.settings.text.line_wrap.no_wrap',
                    'gui.settings.text.line_wrap.widget',
                    'gui.settings.text.line_wrap.fixed_pixel',
                    'gui.settings.text.line_wrap.fixed_column'
                )
            },
            self.icon_mode_dropdown: {
                'activated': DeferredCallable(
                    app().settings.__setitem__,
                    'gui/cache_explorer/icon_mode',
                    self.icon_mode_dropdown.currentIndex
                ),
                'items': (
                    'gui.settings.cache.icon_mode.no_icons',
                    'gui.settings.cache.icon_mode.default',
                    'gui.settings.cache.icon_mode.preview'
                )
            }
        })

        app().init_translations({
            self.setWindowTitle: 'gui.settings.title',
            self.aspect_ratio_dropdown.translate_items: '',
            self.line_wrap_dropdown.translate_items: '',
            self.theme_dropdown.translate_items: '',
            self.transformation_dropdown.translate_items: '',

            # Labels
            theme_label.setText: 'gui.settings.theme',
            aspect_ratio_label.setText: 'gui.settings.media.aspect_ratio',
            transformation_label.setText: 'gui.settings.media.image_transform',
            line_wrap_label.setText: 'gui.settings.text.line_wrap',
            icon_mode_label.setText: 'gui.settings.cache.icon_mode',

            # Buttons
            save_button.setText: 'gui.settings.save',
            reload_button.setText: 'gui.settings.reload',
            import_button.setText: 'gui.settings.import',
            export_button.setText: 'gui.settings.export',
            open_editor_button.setText: 'gui.settings.open_editor',
            key_show_button.setText: 'gui.settings.auth.edit',
            self.key_set_button.setText: 'gui.settings.auth.set',
            self.token_clear_button.setText: 'gui.settings.auth.clear_token'
        })

        init_layouts({
            # Add bottom widgets
            (token_layout := QHBoxLayout()): {
                'items': [self.token_clear_button]
            },
            (key_layout := QHBoxLayout()): {
                'items': [self.key_field, self.key_set_button]
            },
            (bottom := QVBoxLayout()): {
                'items': [key_show_button, key_layout, token_layout]
            },

            # Add middle widgets
            (cache_layout := QHBoxLayout()): {
                'items': [icon_mode_label, self.icon_mode_dropdown]
            },
            (output_layout := QGridLayout()): {
                'items': [
                    (aspect_ratio_label, 0, 0),
                    (self.aspect_ratio_dropdown, 0, 10),
                    (transformation_label, 0, 20),
                    (self.transformation_dropdown, 0, 30),
                    (line_wrap_label, 10, 0),
                    (self.line_wrap_dropdown, 10, 10)
                ]
            },
            (theme_layout := QHBoxLayout()): {
                'items': [theme_label, self.theme_dropdown]
            },
            (middle := QVBoxLayout()): {
                'items': [theme_layout, output_layout, cache_layout]
            },

            # Add top widgets
            (io_buttons := QHBoxLayout()): {
                'items': [save_button, reload_button, import_button, export_button]
            },
            (top := QVBoxLayout()): {
                'items': [io_buttons, open_editor_button]
            },

            # Main layout
            QGridLayout(self): {
                'items': [
                    (top, 0, 0, Qt.AlignTop),
                    (middle, 10, 0, Qt.AlignTop),
                    (bottom, 20, 0, Qt.AlignBottom)
                ]
            }
        })

        for subscribe_params in (
            (DeferredCallable(save_button.setDisabled, False), TomlEvents.Set, lambda event: event.old != event.new),
            (DeferredCallable(save_button.setDisabled, True), TomlEvents.Export, lambda event: event.toml_file.path == event.path),
            (DeferredCallable(save_button.setDisabled, True), TomlEvents.Import, lambda event: event.toml_file.path == event.path),
            (DeferredCallable(self.refresh_dropdowns), TomlEvents.Import)
        ): EventBus['settings'].subscribe(*subscribe_params)

        self.refresh_dropdowns()

    def refresh_dropdowns(self) -> None:
        """Refresh all dropdown widgets with the current settings assigned to them."""
        self.icon_mode_dropdown.setCurrentIndex(app().settings['gui/cache_explorer/icon_mode'])
        self.aspect_ratio_dropdown.setCurrentIndex(app().settings['gui/media_output/aspect_ratio_mode'])
        self.transformation_dropdown.setCurrentIndex(app().settings['gui/media_output/transformation_mode'])
        self.line_wrap_dropdown.setCurrentIndex(app().settings['gui/text_output/line_wrap_mode'])
        self.theme_dropdown.setCurrentIndex(app().theme_index_map[app().settings['gui/themes/selected']])

    # # # # # Events

    def showEvent(self, event: QShowEvent) -> None:
        """Auto hides the key upon un-minimizing."""
        super().showEvent(event)

        init_objects({
            self.key_field: {
                'disabled': True,
                'alignment': Qt.AlignCenter,
                'text': app().client.hidden_key()
            },
            self.key_set_button: {'disabled': True},
            self.token_clear_button: {'disabled': not app().client.token}
        })

        event.accept()
