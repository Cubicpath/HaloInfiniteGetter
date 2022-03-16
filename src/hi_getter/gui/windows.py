###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing GUI elements meant to be used as windows."""

__all__ = (
    'AppWindow',
    'SettingsWindow',
)

import json
import webbrowser
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .._version import __version__
from ..client import Client
from ..client import HTTP_CODE_MAP
from ..constants import *
from ..tomlfile import TomlFile
from .app import *
from .menus import *
from .widgets import *


# noinspection PyArgumentList
class SettingsWindow(QWidget):
    """Window that provides user interaction with the application's settings."""

    def __init__(self, parent: 'AppWindow', size: QSize) -> None:
        """Create a new settings window. Should only have one instance."""
        super().__init__()
        self.client = parent.client
        self.clipboard: QClipboard | None = parent.clipboard
        self.getter_window = parent
        self.settings: TomlFile = parent.APP.settings
        self.translator = parent.APP.translator

        self.setWindowTitle(self.translator('gui.settings.title'))
        self.setWindowIcon(QIcon(str(HI_RESOURCE_PATH / 'icons/settings.ico')))
        self.resize(size)
        self.setFixedWidth(self.width())
        self.settings.hook_event('$fail:import', lambda: QMessageBox.warning(
            self, *(self.translator(*key) for key in (
                ('warnings.settings.import_failure.title',), ('warnings.settings.import_failure.description', self.settings.path)))
        ))

        self.theme_dropdown:          QComboBox
        self.aspect_ratio_dropdown:   QComboBox
        self.transformation_dropdown: QComboBox
        self.line_wrap_dropdown:      QComboBox
        self.key_set_button:          QPushButton
        self.key_field:               QLineEdit
        self._init_ui()

    def _init_ui(self) -> None:

        def save_settings() -> None:
            """Save current settings to the user's settings file."""
            save_button.setDisabled(True)
            self.settings.save()

        def reload_settings() -> None:
            """Reload current settings from the user's settings file."""
            save_button.setDisabled(True)
            if self.settings.reload():
                self.refresh_dropdowns()

        def import_settings() -> None:
            """Import settings from a chosen TOML file."""
            save_button.setDisabled(True)
            file_path = Path(QFileDialog.getOpenFileName(self, self.translator('gui.settings.import'),
                                                         str(HI_CONFIG_PATH), 'TOML Files (*.toml);;All files (*.*)')[0])
            if file_path.is_file():
                if self.settings.import_from(file_path):
                    self.refresh_dropdowns()

        def export_settings() -> None:
            """Export current settings to a chosen file location."""
            file_path = Path(QFileDialog.getSaveFileName(self, self.translator('gui.settings.export'),
                                                         str(HI_CONFIG_PATH), 'TOML Files (*.toml);;All files (*.*)')[0])
            if str(file_path) != '.':
                self.settings.export_to(file_path)

        def set_aspect_ratio_method() -> None:
            """Set the media output's aspect ratio method to the chosen method."""
            save_button.setDisabled(False)
            self.settings['gui/media_output/aspect_ratio_mode'] = self.aspect_ratio_dropdown.currentIndex()
            self.getter_window.resize_image()

        def set_transformation_method() -> None:
            """Set the media output's image transformation method to the chosen method."""
            save_button.setDisabled(False)
            self.settings['gui/media_output/transformation_mode'] = self.transformation_dropdown.currentIndex()
            self.getter_window.resize_image()

        def set_line_wrap_method() -> None:
            """Set the text output's line wrap method to the chosen method."""
            save_button.setDisabled(False)
            self.settings['gui/text_output/line_wrap_mode'] = self.line_wrap_dropdown.currentIndex()
            self.getter_window.text_output.setLineWrapMode(QTextEdit.LineWrapMode(self.settings['gui/text_output/line_wrap_mode']))

        def set_theme() -> None:
            """Set selected theme to the chosen theme."""
            save_button.setDisabled(False)
            self.settings['gui/themes/selected'] = self.getter_window.APP.sorted_themes()[self.theme_dropdown.currentIndex()].id

        def hide_key() -> None:
            """Hide API key."""
            self.key_set_button.setDisabled(True)
            self.key_field.setDisabled(True)
            self.key_field.setText(self.client.hidden_key())
            self.key_field.setAlignment(Qt.AlignCenter)

        def show_key() -> None:
            """Toggle hiding and showing the API key."""
            if not self.key_field.isEnabled():
                self.key_field.setAlignment(Qt.AlignLeft)
                self.key_field.setText(self.client.wpauth)
                self.key_field.setDisabled(False)
                self.key_field.setFocus()
                self.key_set_button.setDisabled(False)
            else:
                hide_key()

        def copy_key() -> None:
            """Copy the current key value to the system clipboard."""
            if self.clipboard is not None:
                self.clipboard.setText(self.client.wpauth)

        def set_key() -> None:
            """Set the client's auth_key to the current text in the key field."""
            self.client.wpauth = self.key_field.text().strip() or None
            show_key()

        def clear_token() -> None:
            self.client.token = None
            self.token_clear_button.setDisabled(True)

        save_button:                  QPushButton = QPushButton(self.translator('gui.settings.save'), clicked=save_settings)
        reload_button:                QPushButton = QPushButton(self.translator('gui.settings.reload'), clicked=reload_settings)
        import_button:                QPushButton = QPushButton(self.translator('gui.settings.import'), clicked=import_settings)
        export_button:                QPushButton = QPushButton(self.translator('gui.settings.export'), clicked=export_settings)
        theme_label:                  QLabel = QLabel(self.translator('gui.settings.gui.theme'))
        aspect_ratio_label:           QLabel = QLabel(self.translator('gui.settings.media.aspect_ratio'))
        transformation_label:         QLabel = QLabel(self.translator('gui.settings.media.image_transform'))
        line_wrap_label:              QLabel = QLabel(self.translator('gui.settings.text.line_wrap'))
        self.theme_dropdown:          QComboBox = QComboBox(self)
        self.aspect_ratio_dropdown:   QComboBox = QComboBox(self)
        self.transformation_dropdown: QComboBox = QComboBox(self)
        self.line_wrap_dropdown:      QComboBox = QComboBox(self)
        open_editor_button:           QPushButton = QPushButton(self.translator('gui.settings.open_editor'), clicked=self.open_editor)
        key_show_button:              QPushButton = QPushButton(self.translator('gui.settings.auth.edit'), clicked=show_key)
        key_copy_button:              QPushButton = QPushButton(self.translator('gui.settings.auth.copy'), clicked=copy_key)
        self.key_set_button:          QPushButton = QPushButton(self.translator('gui.settings.auth.set'), clicked=set_key)
        self.key_field:               BetterLineEdit = BetterLineEdit(returnPressed=self.key_set_button.click, pasted=set_key)
        self.token_clear_button:      QPushButton = QPushButton(self.translator('gui.settings.auth.clear_token'), clicked=clear_token)

        self.theme_dropdown.activated.connect(set_theme)
        self.transformation_dropdown.activated.connect(set_transformation_method)
        self.line_wrap_dropdown.activated.connect(set_line_wrap_method)
        self.aspect_ratio_dropdown.activated.connect(set_aspect_ratio_method)

        # Define layouts
        layout = QGridLayout()  # Main layout
        top = QHBoxLayout()
        middle = QVBoxLayout()
        theme_layout = QHBoxLayout()
        output_layout = QGridLayout()
        bottom = QVBoxLayout()
        key_layout = QHBoxLayout()
        token_layout = QHBoxLayout()

        # Assign positions of layouts
        self.setLayout(layout)
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

        # Modify properties of widgets
        theme_label.setMaximumWidth(85)

        self.theme_dropdown.addItems([theme.display_name for theme in self.getter_window.APP.sorted_themes()])
        self.theme_dropdown.setCurrentIndex(self.getter_window.APP.theme_index_map[self.settings['gui/themes/selected']])

        aspect_ratio_label.setMaximumWidth(90)
        transformation_label.setMaximumWidth(90)
        line_wrap_label.setMaximumWidth(90)
        self.aspect_ratio_dropdown.addItems((self.translator('gui.settings.media.aspect_ratio.ignore'),
                                             self.translator('gui.settings.media.aspect_ratio.keep'),
                                             self.translator('gui.settings.media.aspect_ratio.expanding')))
        self.transformation_dropdown.addItems((self.translator('gui.settings.media.image_transform.fast'),
                                               self.translator('gui.settings.media.image_transform.smooth')))
        self.line_wrap_dropdown.addItems((self.translator('gui.settings.text.line_wrap.no_wrap'),
                                          self.translator('gui.settings.text.line_wrap.widget'),
                                          self.translator('gui.settings.text.line_wrap.fixed_pixel'),
                                          self.translator('gui.settings.text.line_wrap.fixed_column')))
        self.aspect_ratio_dropdown.setCurrentIndex(self.settings['gui/media_output/aspect_ratio_mode'])
        self.transformation_dropdown.setCurrentIndex(self.settings['gui/media_output/transformation_mode'])
        self.line_wrap_dropdown.setCurrentIndex(self.settings['gui/text_output/line_wrap_mode'])

        save_button.setMaximumWidth(50)
        save_button.setDisabled(True)
        reload_button.setMaximumWidth(60)

        self.key_field.setAlignment(Qt.AlignCenter)
        self.key_field.setMinimumWidth(220)
        self.key_field.setFont(QFont('segoe ui', 8))
        self.key_set_button.setMinimumWidth(40)
        self.token_clear_button.setDisabled(not self.client.token)

    def refresh_dropdowns(self) -> None:
        """Refresh all dropdown widgets with the current settings assigned to them."""
        self.aspect_ratio_dropdown.setCurrentIndex(self.settings['gui/media_output/aspect_ratio_mode'])
        self.transformation_dropdown.setCurrentIndex(self.settings['gui/media_output/transformation_mode'])
        self.line_wrap_dropdown.setCurrentIndex(self.settings['gui/text_output/line_wrap_mode'])
        self.theme_dropdown.setCurrentIndex(self.getter_window.APP.theme_index_map[self.settings['gui/themes/selected']])

    def open_editor(self) -> None:
        """Open current settings file in the user's default text editor."""
        webbrowser.open(str(self.settings.path))

    # # # # # Events

    def showEvent(self, event: QShowEvent) -> None:
        """Auto hides the key upon un-minimizing."""
        super().showEvent(event)
        self.key_set_button.setDisabled(True)
        self.key_field.setAlignment(Qt.AlignCenter)
        self.key_field.setDisabled(True)
        self.key_field.setText(self.client.hidden_key())
        self.token_clear_button.setDisabled(not self.client.token)


# TODO: Add exception logger
# noinspection PyArgumentList
class AppWindow(QMainWindow):
    """Main window for the HaloInfiniteGetter application."""

    shown_key_warning: bool = False

    def __init__(self, client: Client, app: GetterApp, size: QSize) -> None:
        """Create the window for the application."""
        super().__init__()
        self.APP:                   GetterApp = app
        self.client:                Client = client
        self.clipboard:             QClipboard = app.clipboard()
        self.current_image:         QPixmap | None = None
        self._clicked_input_field:  bool = False
        self.detached:              dict[str, QMainWindow | None] = {'media': None, 'text': None}
        self.setWindowTitle(self.APP.translator('app.title', __version__))
        self.setWindowIcon(QIcon(str(HI_RESOURCE_PATH / 'icons/hi.ico')))
        self.resize(size)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.input_field:   HistoryComboBox
        self.media_output:  QGraphicsView
        self.text_output:   QTextBrowser
        self.clear_picture: QPushButton
        self.copy_picture:  QPushButton
        self.clear_text:    QPushButton
        self.copy_text:     QPushButton

        self._init_toolbar()
        self._init_ui()

        self.settings_window = SettingsWindow(self, QSize(420, 600))

    def _init_toolbar(self) -> None:
        """Initialize toolbar widgets."""

        def context_menu_handler(menu_class: type) -> None:
            """Create a new :py:class:`QMenu` and show it at the cursor's position."""
            if not issubclass(menu_class, QMenu):
                raise TypeError(f'{menu_class} is not a subclass of {QMenu}')

            menu = menu_class(self)
            menu.move(self.cursor().pos())
            menu.show()

        toolbar = QToolBar('Toolbar', self)
        file = QAction('File', self, triggered=lambda: context_menu_handler(FileContextMenu))
        settings = QAction('Settings', self, triggered=self.open_settings_window)
        tools = QAction('Tools', self, triggered=lambda: context_menu_handler(ToolsContextMenu))
        help_ = QAction('Help', self, triggered=lambda: context_menu_handler(HelpContextMenu))

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        for action in (file, settings, tools, help_):
            toolbar.addSeparator()
            toolbar.addAction(action)

        file.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
        settings.setMenuRole(QAction.MenuRole.PreferencesRole)
        tools.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
        help_.setMenuRole(QAction.MenuRole.AboutRole)

    def _init_ui(self) -> None:
        """Initialize the UI, including Layouts and widgets."""

        def setup_detached_window(id_: str, frame: QFrame, handler: Callable, title: str = None) -> QMainWindow:
            """Set up a detached window, with the layout represented as a :py:class:`QFrame`.

            :param id_: unique name for the window
            :param frame: Set the window's central widget as this QFrame.
            :param handler: Callable to execute when closed, to reattach the frame to the parent window.
            :param title: The window title.
            """
            window = QMainWindow()
            window.setWindowTitle(title if title is not None else self.windowTitle())
            window.setCentralWidget(frame)
            window.setMinimumHeight(200)
            window.setMinimumWidth(300)
            window.closeEvent = lambda *_: handler() if self.detached[id_] is not None else None
            return window

        def toggle_media_detach() -> None:
            """Handler for detaching and reattaching the media output."""
            if self.detached['media'] is None:
                self.detached['media'] = window = setup_detached_window('media',
                                                                        self.media_frame, toggle_media_detach,
                                                                        self.APP.translator('gui.outputs.image.detached'))
                self.image_detach_button.setText(self.APP.translator('gui.outputs.reattach'))
                window.resizeEvent = lambda *_: self.resize_image()
                window.show()
            else:
                window = self.detached['media']
                self.detached['media'] = None
                window.close()

                self.outputs.insertWidget(0, self.media_frame)
                self.image_detach_button.setText(self.APP.translator('gui.outputs.detach'))

        def toggle_text_detach() -> None:
            """Handler for detaching and reattaching the text output."""
            if self.detached['text'] is None:
                self.detached['text'] = window = setup_detached_window('text',
                                                                       self.text_frame, toggle_text_detach,
                                                                       self.APP.translator('gui.outputs.text.label_empty'))
                self.text_detach_button.setText(self.APP.translator('gui.outputs.reattach'))
                window.show()
            else:
                window = self.detached['text']
                self.detached['text'] = None
                window.close()

                self.outputs.insertWidget(-1, self.text_frame)
                self.text_detach_button.setText(self.APP.translator('gui.outputs.detach'))

        def clear_current_pixmap() -> None:
            """Clear the current image from the media output."""
            self.image_size_label.setText(self.APP.translator('gui.outputs.image.label_empty'))
            self.clear_picture.setDisabled(True)
            self.copy_picture.setDisabled(True)
            self.media_output.scene().clear()
            self.current_image = None

        def copy_current_pixmap() -> None:
            """Copy the current image to the system clipboard."""
            if self.clipboard is not None:
                self.clipboard.setPixmap(self.current_image)

        def clear_current_text() -> None:
            """Clear the current text from the text output."""
            self.text_size_label.setText(self.APP.translator('gui.outputs.text.label_empty'))
            self.clear_text.setDisabled(True)
            self.copy_text.setDisabled(True)
            self.text_output.setDisabled(True)
            self.text_output.clear()

        def copy_current_text() -> None:
            """Copy the current output text to the system clipboard."""
            if self.clipboard is not None:
                self.clipboard.setText(self.text_output.toPlainText())

        self.input_field:         HistoryComboBox = HistoryComboBox()
        self.media_frame:         QFrame = QFrame()
        self.image_size_label:    QLabel = QLabel(self.APP.translator('gui.outputs.image.label_empty'))
        self.image_detach_button: QPushButton = QPushButton(self.APP.translator('gui.outputs.detach'), clicked=toggle_media_detach)
        self.media_output:        QGraphicsView = QGraphicsView()
        self.text_frame:          QFrame = QFrame()
        self.text_size_label:     QLabel = QLabel(self.APP.translator('gui.outputs.text.label_empty'))
        self.text_detach_button:  QPushButton = QPushButton(self.APP.translator('gui.outputs.detach'), clicked=toggle_text_detach)
        self.text_output:         QTextBrowser = QTextBrowser()
        self.clear_picture:       QPushButton = QPushButton(self.APP.translator('gui.outputs.clear'), clicked=clear_current_pixmap)
        self.copy_picture:        QPushButton = QPushButton(self.APP.translator('gui.outputs.image.copy'), clicked=copy_current_pixmap)
        self.clear_text:          QPushButton = QPushButton(self.APP.translator('gui.outputs.clear'), clicked=clear_current_text)
        self.copy_text:           QPushButton = QPushButton(self.APP.translator('gui.outputs.text.copy'), clicked=copy_current_text)
        subdomain_field:          QLineEdit = QLineEdit(self.client.sub_host)
        root_folder_field:        QLineEdit = QLineEdit(self.client.parent_path)
        get_button:               QPushButton = QPushButton(self.APP.translator('gui.input_field.get'), clicked=self.use_input)
        scan_button:              QPushButton = QPushButton(self.APP.translator('gui.input_field.scan'), clicked=lambda: self.use_input(scan=True))

        self.input_field.lineEdit().returnPressed.connect(self.use_input)  # Connect pressing enter while in the line edit to use_input
        self.text_output.anchorClicked.connect(lambda e: self.navigate_to(e.toDisplayString()))

        main_widget = QWidget()
        layout = QGridLayout()
        top = QHBoxLayout()
        self.outputs = QHBoxLayout()
        media_layout = QVBoxLayout()
        media_top = QHBoxLayout()
        media_bottom = QHBoxLayout()
        text_layout = QVBoxLayout()
        text_top = QHBoxLayout()
        text_bottom = QHBoxLayout()
        bottom = QGridLayout()
        statuses = QHBoxLayout()

        self.setCentralWidget(main_widget)
        main_widget.setLayout(layout)
        layout.addLayout(top, 10, 0, Qt.AlignTop)
        layout.addLayout(self.outputs, 20, 0, Qt.AlignHCenter)
        layout.addLayout(bottom, 30, 0, Qt.AlignBottom)

        top.addWidget(subdomain_field)
        top.addWidget(root_folder_field)
        top.addWidget(self.input_field)
        top.addWidget(get_button)
        top.addWidget(scan_button)
        top.setSpacing(2)

        self.outputs.addWidget(self.media_frame)
        self.outputs.addWidget(self.text_frame)

        # noinspection Duplicates
        self.media_frame.setLayout(media_layout)
        media_layout.addLayout(media_top)
        media_layout.addWidget(self.media_output)
        media_layout.addLayout(media_bottom)
        media_top.addWidget(self.image_size_label, Qt.AlignLeft)
        media_top.addWidget(self.image_detach_button, Qt.AlignRight)
        media_bottom.addWidget(self.clear_picture, Qt.AlignLeft)
        media_bottom.addWidget(self.copy_picture, Qt.AlignLeft)

        # noinspection Duplicates
        self.text_frame.setLayout(text_layout)
        text_layout.addLayout(text_top)
        text_layout.addWidget(self.text_output)
        text_layout.addLayout(text_bottom)
        text_top.addWidget(self.text_size_label, Qt.AlignLeft)
        text_top.addWidget(self.text_detach_button, Qt.AlignRight)
        text_bottom.addWidget(self.clear_text, Qt.AlignLeft)
        text_bottom.addWidget(self.copy_text, Qt.AlignLeft)
        text_bottom.setSpacing(5)

        bottom.addLayout(statuses, 10, 0)

        subdomain_field.setFixedWidth(125)
        subdomain_field.setDisabled(True)
        root_folder_field.setFixedWidth(28)
        root_folder_field.setDisabled(True)
        self.input_field.addItem(HI_SAMPLE_RESOURCE)
        get_button.setMaximumWidth(40)
        scan_button.setMaximumWidth(55)
        self.image_size_label.setMinimumWidth(50)
        self.image_detach_button.setMaximumWidth(80)
        self.media_output.setScene(QGraphicsScene())
        self.media_output.setMinimumHeight(28)
        self.media_output.setAutoFillBackground(False)
        self.media_output.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.media_output.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.media_output.setDisabled(True)
        self.text_size_label.setMinimumWidth(50)
        self.text_detach_button.setMaximumWidth(80)
        self.text_output.setMinimumHeight(28)
        self.text_output.setLineWrapMode(QTextEdit.LineWrapMode(self.APP.settings['gui/text_output/line_wrap_mode']))
        self.text_output.setOpenLinks(False)
        self.text_output.setDisabled(True)
        self.clear_picture.setMaximumWidth(80)
        self.clear_picture.setMinimumWidth(40)
        self.clear_picture.setDisabled(True)
        self.copy_picture.setMaximumWidth(160)
        self.copy_picture.setMinimumWidth(80)
        self.copy_picture.setDisabled(True)
        self.clear_text.setMaximumWidth(80)
        self.clear_text.setMinimumWidth(40)
        self.clear_text.setDisabled(True)
        self.copy_text.setMaximumWidth(160)
        self.copy_text.setMinimumWidth(80)
        self.copy_text.setDisabled(True)

    def open_settings_window(self) -> None:
        """Show the :py:class:`SettingsWindow` and bring it the front."""
        self.settings_window.show()
        self.settings_window.activateWindow()
        self.settings_window.raise_()

    def navigate_to(self, path: str) -> None:
        """Set input field text to path and get resource."""
        self.input_field.addItem(path)
        self.input_field.setCurrentIndex(self.input_field.count() - 1)
        self.use_input()

    def use_input(self, scan: bool = False) -> None:
        """Use the current input field's text to search through the Client for data.

        Automatically handles media and text data.

        :param scan: Whether to recursively scan a resource.
        """
        self._clicked_input_field = True
        user_input = self.input_field.currentText()
        if '/file/' not in user_input:
            if user_input.endswith(('png', 'jpg', 'jpeg', 'webp', 'gif')):
                user_input = f'images/file/{user_input}'
            else:
                user_input = f'progression/file/{user_input}'

        if user_input:
            if scan:
                self.client.recursive_search(user_input)
                self.use_input()
            else:
                data = self.client.get_hi_data(user_input)
                if isinstance(data, bytes):
                    self.clear_picture.setDisabled(False)
                    self.copy_picture.setDisabled(False)
                    self.current_image = QPixmap()
                    self.current_image.loadFromData(data)
                    size = self.current_image.size()
                    self.image_size_label.setText(self.APP.translator('gui.outputs.image.label',
                                                                      size.width(), size.height(),
                                                                      round(len(data) / 1024, 4)))
                    self.resize_image()
                else:
                    self.clear_text.setDisabled(False)
                    self.copy_text.setDisabled(False)
                    self.text_output.setDisabled(False)

                    if isinstance(data, dict):
                        data = json.dumps(data, indent=2)
                    elif isinstance(data, int):
                        data = f'{data}: {HTTP_CODE_MAP[data][0]}\n{HTTP_CODE_MAP[data][1]}'

                    output = data
                    replaced = set()

                    for match in HI_PATH_PATTERN.finditer(data):
                        match = match[0].replace('"', '')
                        if match not in replaced:
                            output = output.replace(match, f'<a href="{match}" style="color: #2A5DB0">{match}</a>')
                            replaced.add(match)
                    self.text_output.setHtml(f'<body style="white-space: pre-wrap">{output}</body>')
                    self.text_size_label.setText(self.APP.translator('gui.outputs.text.label',
                                                                     len(data.splitlines()), len(data),
                                                                     round(len(data.encode('utf8')) / 1024, 4)))

    def resize_image(self) -> None:
        """Refresh the media output with a resized version of the current image."""
        if self.current_image is not None:
            new = self.current_image.copy()
            self.media_output.scene().clear()  # Clear buffer, otherwise causes memory leak
            if self.current_image.size() != self.media_output.viewport().size():
                # Create a new image from the copied source image, scaled to fit the window.
                new = new.scaled(
                    self.media_output.viewport().size(),
                    Qt.AspectRatioMode(self.APP.settings['gui/media_output/aspect_ratio_mode']),
                    Qt.TransformationMode(self.APP.settings['gui/media_output/transformation_mode'])
                )
            # Add image to buffer
            self.media_output.scene().addPixmap(new)

    # # # # # Events
    def show(self) -> None:
        """After window is displayed, show warnings if not already warned."""
        super().show()
        if not self.shown_key_warning and self.client.token is None:
            QMessageBox.warning(self, *(self.APP.translator(key) for key in ('warnings.empty_token.title', 'warnings.empty_token.description')))
            self.__class__.shown_key_warning = True

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Resize image on resize of window."""
        super().resizeEvent(event)
        self.resize_image()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Closes all detached/children windows and quit application."""
        super().closeEvent(event)
        self.APP.quit()
