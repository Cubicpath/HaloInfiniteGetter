###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Settings window implementation."""
from __future__ import annotations

__all__ = (
    'SettingsWindow',
)

import webbrowser
from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...constants import *
from ...events import EventBus
from ...models import DeferredCallable
from ...tomlfile import TomlEvents
from ...utils.gui import init_objects
from ..app import app
from ..app import tr
from ..widgets import PasteLineEdit
from .application import AppWindow


# noinspection PyArgumentList
class SettingsWindow(QWidget):
    """Window that provides user interaction with the application's settings."""

    def __init__(self, parent: AppWindow, size: QSize) -> None:
        """Create a new settings window. Should only have one instance."""
        super().__init__()
        self.app_window = parent

        self.setWindowTitle(tr('gui.settings.title'))
        self.setWindowIcon(app().icon_store['settings'])
        self.resize(size)
        self.setFixedWidth(self.width())

        # Create a tr DeferredCallable with every tuple acting as arguments.
        EventBus['settings'].subscribe(
            DeferredCallable(app().show_dialog, 'errors.settings.import_failure', self, description_args=(app().settings.path,)),
            TomlEvents.Fail, event_predicate=lambda event: event.failure == 'import'
        )

        self.theme_dropdown:          QComboBox
        self.aspect_ratio_dropdown:   QComboBox
        self.transformation_dropdown: QComboBox
        self.line_wrap_dropdown:      QComboBox
        self.key_set_button:          QPushButton
        self.key_field:               QLineEdit
        self._init_ui()

    def _init_ui(self) -> None:

        def import_settings() -> None:
            """Import settings from a chosen TOML file."""
            file_path = Path(QFileDialog.getOpenFileName(self, tr('gui.settings.import'),
                                                         str(HI_CONFIG_PATH), 'TOML Files (*.toml);;All files (*.*)')[0])
            if file_path.is_file():
                if app().settings.import_from(file_path):
                    save_button.setDisabled(False)

        def export_settings() -> None:
            """Export current settings to a chosen file location."""
            file_path = Path(QFileDialog.getSaveFileName(self, tr('gui.settings.export'),
                                                         str(HI_CONFIG_PATH), 'TOML Files (*.toml);;All files (*.*)')[0])
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

        # Define base widgets
        (
            theme_label, aspect_ratio_label, transformation_label, line_wrap_label,
            save_button, reload_button, import_button, export_button, open_editor_button,
            key_show_button, key_copy_button, self.key_set_button, self.token_clear_button,
            self.theme_dropdown, self.aspect_ratio_dropdown, self.transformation_dropdown, self.line_wrap_dropdown,
            self.key_field
        ) = (
            QLabel(self), QLabel(self), QLabel(self), QLabel(self),
            QPushButton(self), QPushButton(self), QPushButton(self), QPushButton(self), QPushButton(self),
            QPushButton(self), QPushButton(self), QPushButton(self), QPushButton(self),
            QComboBox(self), QComboBox(self), QComboBox(self), QComboBox(self),
            PasteLineEdit(self)
        )

        for subscribe_params in (
                (DeferredCallable(self.app_window.resize_image), TomlEvents.Set, lambda event: event.key.startswith('gui/media_output/')),
                (lambda val: self.app_window.text_output.setLineWrapMode(val.new), TomlEvents.Set, lambda event: event.key == 'gui/text_output/line_wrap_mode'),
                (DeferredCallable(save_button.setDisabled, False), TomlEvents.Set, lambda event: event.old != event.new),
                (DeferredCallable(save_button.setDisabled, True), TomlEvents.Export, lambda event: event.toml_file.path == event.path),
                (DeferredCallable(save_button.setDisabled, True), TomlEvents.Import, lambda event: event.toml_file.path == event.path),
                (DeferredCallable(self.refresh_dropdowns), TomlEvents.Import)
        ): EventBus['settings'].subscribe(*subscribe_params)

        init_objects({
            # Labels
            theme_label: {
                'size': {'maximum': (85, None)}
            },
            aspect_ratio_label: {
                'size': {'maximum': (90, None)}
            },
            transformation_label: {
                'size': {'maximum': (90, None)}
            },
            line_wrap_label: {
                'size': {'maximum': (90, None)}
            },

            # Buttons
            save_button: {
                'disabled': True,
                'size': {'maximum': (50, None)},
                'clicked': app().settings.save
            },
            reload_button: {
                'size': {'maximum': (60, None)},
                'clicked': app().settings.reload
            },
            import_button: {
                'clicked': import_settings
            },
            export_button: {
                'clicked': export_settings
            },
            open_editor_button: {
                'clicked': DeferredCallable(webbrowser.open, lambda: app().settings.path)
            },
            key_show_button: {
                'clicked': toggle_key_visibility
            },
            key_copy_button: {
                'clicked': DeferredCallable(app().clipboard().setText, lambda: app().client.wpauth)
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
            }
        }, translator=tr)

        app().init_translations({
            self.setWindowTitle: 'gui.settings.title',

            # Labels
            theme_label.setText: 'gui.settings.theme',
            aspect_ratio_label.setText: 'gui.settings.media.aspect_ratio',
            transformation_label.setText: 'gui.settings.media.image_transform',
            line_wrap_label.setText: 'gui.settings.text.line_wrap',

            # Buttons
            save_button.setText: 'gui.settings.save',
            reload_button.setText: 'gui.settings.reload',
            import_button.setText: 'gui.settings.import',
            export_button.setText: 'gui.settings.export',
            open_editor_button.setText: 'gui.settings.open_editor',
            key_show_button.setText: 'gui.settings.auth.edit',
            key_copy_button.setText: 'gui.settings.auth.copy',
            self.key_set_button.setText: 'gui.settings.auth.set',
            self.token_clear_button.setText: 'gui.settings.auth.clear_token'
        })

        # Define layouts
        layout = QGridLayout(self)  # Main layout
        top = QHBoxLayout()
        middle = QVBoxLayout()
        theme_layout = QHBoxLayout()
        output_layout = QGridLayout()
        bottom = QVBoxLayout()
        key_layout = QHBoxLayout()
        token_layout = QHBoxLayout()

        # Assign positions of layouts
        layout.addLayout(top, 0, 0, Qt.AlignTop)
        layout.addLayout(middle, 10, 0, Qt.AlignTop)
        layout.addLayout(bottom, 20, 0, Qt.AlignBottom)

        # Add top widgets
        top.addWidget(save_button)
        top.addWidget(reload_button)
        top.addWidget(import_button)
        top.addWidget(export_button)

        # Add middle widgets
        middle.addWidget(open_editor_button)
        middle.addLayout(theme_layout)
        middle.addLayout(output_layout)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_dropdown)
        output_layout.addWidget(aspect_ratio_label, 0, 0)
        output_layout.addWidget(self.aspect_ratio_dropdown, 0, 10)
        output_layout.addWidget(transformation_label, 0, 20)
        output_layout.addWidget(self.transformation_dropdown, 0, 30)
        output_layout.addWidget(line_wrap_label, 10, 0)
        output_layout.addWidget(self.line_wrap_dropdown, 10, 10)

        # Add bottom widgets
        bottom.addWidget(key_show_button)
        bottom.addLayout(key_layout)
        bottom.addLayout(token_layout)
        key_layout.addWidget(key_copy_button)
        key_layout.addWidget(self.key_field)
        key_layout.addWidget(self.key_set_button)
        token_layout.addWidget(self.token_clear_button)

        self.refresh_dropdowns()

    def refresh_dropdowns(self) -> None:
        """Refresh all dropdown widgets with the current settings assigned to them."""
        self.aspect_ratio_dropdown.setCurrentIndex(app().settings['gui/media_output/aspect_ratio_mode'])
        self.transformation_dropdown.setCurrentIndex(app().settings['gui/media_output/transformation_mode'])
        self.line_wrap_dropdown.setCurrentIndex(app().settings['gui/text_output/line_wrap_mode'])
        self.theme_dropdown.setCurrentIndex(app().theme_index_map[app().settings['gui/themes/selected']])

    # # # # # Events

    def showEvent(self, event: QShowEvent) -> None:
        """Auto hides the key upon un-minimizing."""
        super().showEvent(event)
        self.key_set_button.setDisabled(True)
        self.key_field.setAlignment(Qt.AlignCenter)
        self.key_field.setDisabled(True)
        self.key_field.setText(app().client.hidden_key())
        self.token_clear_button.setDisabled(not app().client.token)
        event.accept()
